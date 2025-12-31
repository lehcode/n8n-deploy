#!/usr/bin/env python3
"""
n8n Internal API client for folder operations

This module provides access to n8n's internal REST API (/rest/) which
is NOT part of the public API. It is undocumented and may change between
n8n versions without notice.

WARNING: This API requires session-based authentication (cookies) rather
than API keys. The internal API is used for:
- Folder listing and creation
- Project access
- Moving workflows between folders

For standard workflow CRUD operations, use the public API via n8n_api.py.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import requests

from .folder_path import build_folder_path, find_folder_by_path, split_path_parts
from .ssl_utils import configure_ssl_verification


# Status code messages for error handling
_STATUS_MESSAGES: Dict[int, str] = {
    401: "Session expired or invalid - please re-authenticate",
    403: "Access denied - insufficient permissions",
}


class N8nInternalClient:
    """Client for n8n's internal REST API

    Provides access to folder and project operations that are not available
    in the public API. Requires session cookie authentication.

    Note: This API is undocumented and may break with n8n updates.
    """

    DEFAULT_TIMEOUT = 10

    def __init__(
        self,
        base_url: str,
        skip_ssl_verify: bool = False,
    ) -> None:
        """Initialize internal API client

        Args:
            base_url: n8n server base URL (e.g., http://n8n.example.com:5678)
            skip_ssl_verify: If True, disable SSL certificate verification
        """
        self.base_url = base_url.rstrip("/")
        self.skip_ssl_verify = skip_ssl_verify
        self._session_cookie: Optional[str] = None
        self._session: requests.Session = requests.Session()

        configure_ssl_verification(skip_ssl_verify, self._session)

    @property
    def is_authenticated(self) -> bool:
        """Check if client has a session cookie"""
        return self._session_cookie is not None

    def set_session_cookie(self, cookie: str) -> None:
        """Set the session cookie for authentication

        Args:
            cookie: The n8n session cookie value (typically named 'n8n-auth').
                    Accepts either raw JWT value or full cookie string with
                    'n8n-auth=' prefix.
        """
        # Strip cookie name prefix if provided (e.g., "n8n-auth=eyJ..." -> "eyJ...")
        if cookie.startswith("n8n-auth="):
            cookie = cookie[9:]
        self._session_cookie = cookie
        self._session.cookies.set("n8n-auth", cookie)

    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate with email and password to obtain session cookie

        Args:
            email: n8n account email
            password: n8n account password

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Clear old cookies before new auth
            self._session.cookies.clear()
            self._session_cookie = None

            response = self._session.post(
                f"{self.base_url}/rest/login",
                json={"emailOrLdapLoginId": email, "password": password},
                timeout=self.DEFAULT_TIMEOUT,
            )

            if response.status_code == 200:
                # Extract session cookie from response
                for cookie in self._session.cookies:
                    if cookie.name == "n8n-auth":
                        self._session_cookie = cookie.value
                        return True
                # Fallback: check for auth-like cookie names
                for cookie in self._session.cookies:
                    if "auth" in cookie.name.lower() or "session" in cookie.name.lower():
                        self._session_cookie = cookie.value
                        return True

            return False

        except requests.exceptions.RequestException:
            return False

    def get_cookie_expiry(self) -> Optional[datetime]:
        """Get the expiry time of the current session cookie

        Returns:
            Expiry datetime if available, None otherwise
        """
        if not self._session_cookie:
            return None

        # Try to extract expiry from cookie
        for cookie in self._session.cookies:
            if cookie.name == "n8n-auth" and cookie.expires:
                return datetime.fromtimestamp(cookie.expires, tz=timezone.utc)

        # Default: assume 24 hours from now
        return datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)

    def _get_method_dispatcher(self) -> Dict[str, Callable[..., requests.Response]]:
        """Return HTTP method dispatcher for the session."""
        return {
            "GET": lambda url, data: self._session.get(url, timeout=self.DEFAULT_TIMEOUT),
            "POST": lambda url, data: self._session.post(url, json=data, timeout=self.DEFAULT_TIMEOUT),
            "PUT": lambda url, data: self._session.put(url, json=data, timeout=self.DEFAULT_TIMEOUT),
            "PATCH": lambda url, data: self._session.patch(url, json=data, timeout=self.DEFAULT_TIMEOUT),
            "DELETE": lambda url, data: self._session.delete(url, timeout=self.DEFAULT_TIMEOUT),
        }

    def _handle_status_code(self, status_code: int, response_text: str, silent: bool) -> Optional[Dict[str, Any]]:
        """Handle HTTP status codes and return appropriate result.

        Returns empty dict for 204, None for errors, raises for success (caller continues).
        """
        # Known error status codes
        if status_code in _STATUS_MESSAGES:
            if not silent:
                print(_STATUS_MESSAGES[status_code])
            return None

        # Generic error
        if status_code >= 400:
            if not silent:
                print(f"API error: {status_code} - {response_text}")
            return None

        # No content
        if status_code == 204:
            return {}

        # Success - return None to signal caller should parse JSON
        return None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        silent: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request to internal API

        Args:
            method: HTTP method
            endpoint: API endpoint (without /rest/ prefix)
            data: Optional request payload
            silent: If True, suppress error messages

        Returns:
            Response JSON dict or None on failure
        """
        if not self._session_cookie:
            if not silent:
                print("Not authenticated - call authenticate() or set_session_cookie() first")
            return None

        url = f"{self.base_url}/rest/{endpoint.lstrip('/')}"
        method_upper = method.upper()

        try:
            dispatcher = self._get_method_dispatcher()
            if method_upper not in dispatcher:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response = dispatcher[method_upper](url, data)

            # Handle error status codes
            if response.status_code in _STATUS_MESSAGES or response.status_code >= 400:
                return self._handle_status_code(response.status_code, response.text, silent)

            # Handle 204 No Content
            if response.status_code == 204:
                return {}

            # Parse and return JSON
            json_response: Dict[str, Any] = response.json()
            return json_response

        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"Request failed: {e}")
            return None

    # ==================== PROJECT OPERATIONS ====================

    def get_projects(self) -> Optional[List[Dict[str, Any]]]:
        """Get all projects accessible to the user

        Returns:
            List of project dicts or None on failure
        """
        result = self._make_request("GET", "projects")
        if result and "data" in result:
            data: List[Dict[str, Any]] = result["data"]
            return data
        return None

    def get_personal_project(self) -> Optional[Dict[str, Any]]:
        """Get the user's personal project

        Returns:
            Personal project dict or None
        """
        projects = self.get_projects()
        if not projects:
            return None

        for project in projects:
            if project.get("type") == "personal":
                return project

        return None

    # ==================== FOLDER OPERATIONS ====================

    def list_folders(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """List all folders in a project

        Args:
            project_id: The project UUID

        Returns:
            List of folder dicts or None on failure

        Note: This endpoint may return folders in a nested structure.
        """
        # Try the standard folders endpoint first
        result = self._make_request("GET", f"projects/{project_id}/folders")
        if result:
            if "data" in result:
                data: List[Dict[str, Any]] = result["data"]
                return data

        # Fallback: try alternative endpoint structure
        result = self._make_request("GET", f"folders?projectId={project_id}")
        if result and "data" in result:
            fallback_data: List[Dict[str, Any]] = result["data"]
            return fallback_data

        return None

    def get_folder(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """Get folder details by ID

        Args:
            folder_id: The folder UUID

        Returns:
            Folder dict or None
        """
        return self._make_request("GET", f"folders/{folder_id}")

    def create_folder(
        self,
        project_id: str,
        name: str,
        parent_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new folder in a project

        Args:
            project_id: The project UUID
            name: Folder name
            parent_id: Optional parent folder UUID for nested folders

        Returns:
            Created folder dict or None on failure
        """
        data: Dict[str, Any] = {
            "name": name,
            "projectId": project_id,
        }
        if parent_id:
            data["parentId"] = parent_id

        return self._make_request("POST", "folders", data)

    def delete_folder(self, folder_id: str) -> bool:
        """Delete a folder

        Args:
            folder_id: The folder UUID

        Returns:
            True if deleted successfully
        """
        result = self._make_request("DELETE", f"folders/{folder_id}")
        return result is not None

    def rename_folder(self, folder_id: str, new_name: str) -> Optional[Dict[str, Any]]:
        """Rename a folder

        Args:
            folder_id: The folder UUID
            new_name: New folder name

        Returns:
            Updated folder dict or None
        """
        return self._make_request("PATCH", f"folders/{folder_id}", {"name": new_name})

    # ==================== WORKFLOW FOLDER OPERATIONS ====================

    def get_workflows_in_folder(self, folder_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get all workflows in a specific folder

        Args:
            folder_id: The folder UUID

        Returns:
            List of workflow dicts or None
        """
        result = self._make_request("GET", f"folders/{folder_id}/workflows")
        if result and "data" in result:
            data: List[Dict[str, Any]] = result["data"]
            return data
        return None

    def move_workflow_to_folder(
        self,
        workflow_id: str,
        folder_id: str,
    ) -> bool:
        """Move a workflow to a folder

        Args:
            workflow_id: The workflow ID
            folder_id: Target folder UUID

        Returns:
            True if moved successfully
        """
        result = self._make_request(
            "PATCH",
            f"workflows/{workflow_id}",
            {"folderId": folder_id},
        )
        return result is not None

    def remove_workflow_from_folder(self, workflow_id: str) -> bool:
        """Remove a workflow from its folder (move to root)

        Args:
            workflow_id: The workflow ID

        Returns:
            True if removed successfully
        """
        result = self._make_request(
            "PATCH",
            f"workflows/{workflow_id}",
            {"folderId": None},
        )
        return result is not None

    # ==================== UTILITY METHODS ====================
    # These delegate to module-level functions for better testability

    def build_folder_path(self, folders: List[Dict[str, Any]], folder_id: str) -> str:
        """Build full folder path from folder list. Delegates to folder_path module."""
        return build_folder_path(folders, folder_id)

    def find_folder_by_path(
        self,
        folders: List[Dict[str, Any]],
        path: str,
    ) -> Optional[Dict[str, Any]]:
        """Find folder by its full path. Delegates to folder_path module."""
        return find_folder_by_path(folders, path)

    def get_or_create_folder_path(
        self,
        project_id: str,
        path: str,
    ) -> Optional[str]:
        """Get or create a folder path, creating intermediate folders as needed

        Args:
            project_id: Project UUID
            path: Folder path like "parent/child/folder"

        Returns:
            Final folder ID or None on failure
        """
        folders = self.list_folders(project_id)
        if folders is None:
            return None

        parts = split_path_parts(path)
        parent_id: Optional[str] = None
        current_path = ""

        for part in parts:
            current_path = f"{current_path}/{part}" if current_path else part
            existing = find_folder_by_path(folders, current_path)

            if existing:
                parent_id = existing["id"]
            else:
                # Create the folder
                result = self.create_folder(project_id, part, parent_id)
                if not result or "id" not in result:
                    return None
                parent_id = result["id"]
                # Refresh folders list
                folders = self.list_folders(project_id) or []

        return parent_id

    def test_connection(self) -> bool:
        """Test if the connection and authentication work

        Returns:
            True if connection is working and cookie is valid
        """
        if not self._session_cookie:
            return False
        # Test with an API call that requires authentication
        result = self._make_request("GET", "projects", silent=True)
        return result is not None
