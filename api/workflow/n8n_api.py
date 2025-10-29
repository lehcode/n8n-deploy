#!/usr/bin/env python3
"""
n8n server API integration for push/pull operations

Handles: pull, push, server operations
"""

import json
import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from urllib3.exceptions import InsecureRequestWarning

from ..api_keys import KeyApi
from ..config import AppConfig
from ..db import DBApi
from ..db.servers import ServerCrud
from ..jwt_utils import check_jwt_expiration
from ..models import Workflow


class N8nAPI:
    """n8n server API integration"""

    def __init__(
        self, db: "DBApi", config: AppConfig, api_manager: KeyApi, skip_ssl_verify: bool = False, remote: Optional[str] = None
    ):
        self.db = db
        self.config = config
        self.api_manager = api_manager
        self.skip_ssl_verify = skip_ssl_verify
        self.remote = remote
        self.base_path = config.workflows_path
        self._server_url: Optional[str] = None
        self._server_api_key: Optional[str] = None

        # Suppress InsecureRequestWarning when SSL verification is disabled
        if skip_ssl_verify:
            warnings.filterwarnings("ignore", category=InsecureRequestWarning)

    def _check_api_key_expiration(self, api_key: Optional[str]) -> None:
        """Check if API key is expired and print warning"""
        if not api_key:
            return

        is_expired, exp_datetime, warning = check_jwt_expiration(api_key)
        if warning:
            print(f"{warning}")
            if is_expired:
                print("Generate a new API key from your n8n server settings")

    def _resolve_remote(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolve remote to server URL and API key

        Returns:
            tuple: (server_url, api_key) or (None, None) if resolution fails
        """
        import os

        if not self.remote:
            # No remote specified - use config or environment
            server_url = self.config.n8n_api_url if self.config else os.getenv("N8N_SERVER_URL", "")
            # Try to get first available API key
            keys = self.api_manager.list_api_keys()
            if keys:
                api_key = self.api_manager.get_api_key(keys[0]["name"])
                self._check_api_key_expiration(api_key)
                return (server_url, api_key)
            # Fallback to environment variable
            env_api_key = os.getenv("N8N_DEPLOY_SERVER_KEY")
            self._check_api_key_expiration(env_api_key)
            return (server_url, env_api_key)

        # Remote specified - check if it's a server name or URL
        server_api = ServerCrud(config=self.config)

        # Try as server name first
        server = server_api.get_server_by_name(self.remote)
        if server:
            # Get API key for this server
            api_key = server_api.get_api_key_for_server(self.remote)
            if not api_key:
                print(f"⚠️  No API key linked to server '{self.remote}'")
                print(f"   Use: n8n-deploy server link {self.remote} <key_name>")
                return (None, None)
            self._check_api_key_expiration(api_key)
            return (server["url"], api_key)

        # Try as URL (check if it looks like a URL)
        if self.remote.startswith("http://") or self.remote.startswith("https://"):
            server = server_api.get_server_by_url(self.remote)
            if server:
                api_key = server_api.get_api_key_for_server(server["name"])
                self._check_api_key_expiration(api_key)
                return (self.remote, api_key)
            # URL not in database - try first available API key or environment
            keys = self.api_manager.list_api_keys()
            if keys:
                api_key = self.api_manager.get_api_key(keys[0]["name"])
                self._check_api_key_expiration(api_key)
                return (self.remote, api_key)
            env_api_key = os.getenv("N8N_DEPLOY_SERVER_KEY")
            self._check_api_key_expiration(env_api_key)
            return (self.remote, env_api_key)

        print(f"❌ Server '{self.remote}' not found")
        print(f"   Add it with: n8n-deploy server add {self.remote} <url>")
        return (None, None)

    def _get_n8n_credentials(self) -> Optional[Dict[str, Any]]:
        """Get n8n API credentials using remote-based resolution"""
        try:
            # Use cached values if available
            if self._server_url and self._server_api_key:
                server_url: str = self._server_url
                api_key: str = self._server_api_key
            else:
                resolved_url, resolved_key = self._resolve_remote()
                if not resolved_url or not resolved_key:
                    print("⚠️  No API key available for the specified server")
                    return None
                # Cache the values
                self._server_url = resolved_url
                self._server_api_key = resolved_key
                server_url = resolved_url
                api_key = resolved_key

            return {
                "api_key": api_key,
                "server_url": server_url,
                "headers": {
                    "X-N8N-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
            }
        except Exception as e:
            print(f"❌ Failed to retrieve API key: {e}")
            return None

    def _make_n8n_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, silent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request to n8n API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Optional request payload
            silent: If True, suppress error messages for failed requests
        """
        credentials = self._get_n8n_credentials()
        if not credentials:
            return None

        # Use server_url from credentials (resolved from remote)
        base_url = credentials.get("server_url", "").rstrip("/")
        url = f"{base_url}/{endpoint.lstrip('/')}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=credentials["headers"], verify=not self.skip_ssl_verify, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    headers=credentials["headers"],
                    json=data,
                    verify=not self.skip_ssl_verify,
                    timeout=10,
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url,
                    headers=credentials["headers"],
                    json=data,
                    verify=not self.skip_ssl_verify,
                    timeout=10,
                )
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=credentials["headers"], verify=not self.skip_ssl_verify, timeout=10)
            else:
                if not silent:
                    print(f"❌ Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            result = response.json()
            return result if isinstance(result, dict) else None
        except requests.exceptions.Timeout:
            if not silent:
                print("❌ n8n API request timed out after 10 seconds")
            return None
        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"❌ n8n API request failed: {e}")
            return None

    def get_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch all workflows from n8n server"""
        result = self._make_n8n_request("GET", "api/v1/workflows")
        if result and isinstance(result, dict) and "data" in result:
            data = result["data"]
            return data if isinstance(data, list) else None
        return result if isinstance(result, list) else None

    def get_n8n_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Fetch specific wf from n8n server by ID"""
        return self._make_n8n_request("GET", f"api/v1/workflows/{workflow_id}")

    def create_n8n_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new wf on n8n server"""
        return self._make_n8n_request("POST", "api/v1/workflows", workflow_data)

    def update_n8n_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing wf on n8n server"""
        return self._make_n8n_request("PUT", f"api/v1/workflows/{workflow_id}", workflow_data)

    def list_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """List all workflows from n8n server (alias for get_n8n_workflows)"""
        return self.get_n8n_workflows()

    def pull_workflow(self, workflow_id: str) -> bool:
        """Pull wf from n8n server using REST API"""
        try:
            print(f"🔄 Pulling wf {workflow_id} from n8n server...")
            workflow_data = self.get_n8n_workflow(workflow_id)

            if not workflow_data:
                print(f"❌ Workflow {workflow_id} not found on server")
                return False

            print(f"📋 Workflow: {workflow_data.get('name', 'Unknown')} ({workflow_data.get('id', workflow_id)})")
            print(f"🎯 Active: {workflow_data.get('active', False)}")
            print(f"📊 Nodes: {len(workflow_data.get('nodes', []))}")

            workflow_path = self.base_path / f"{workflow_id}.json"
            with open(workflow_path, "w", encoding="utf-8") as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)

            print(f"📄 Saved to: {workflow_path}")

            # Get n8n server version for tracking
            n8n_version = self.get_n8n_version()

            # Check if wf exists in database, if not add it
            existing_workflow = self.db.get_workflow(workflow_id)
            if not existing_workflow:
                # Add new wf with n8n version
                wf = Workflow(
                    id=workflow_id,
                    name=workflow_data.get("name", "Unknown"),
                    file=None,
                    file_folder=str(self.base_path),
                    n8n_version_id=n8n_version,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    last_synced=datetime.now(timezone.utc),
                )
                self.db.add_workflow(wf)
            else:
                # Update existing wf with n8n version
                existing_workflow.n8n_version_id = n8n_version
                existing_workflow.updated_at = datetime.now(timezone.utc)
                existing_workflow.last_synced = datetime.now(timezone.utc)
                self.db.update_workflow(existing_workflow)

            # Increment pull counter
            self.db.increment_pull_count(workflow_id)
            print("✅ Workflow pulled successfully")
            return True

        except Exception as e:
            # Print specific error details, but let CLI handle the summary message
            print(f"❌ Error: {e}")
            return False

    def push_workflow(self, workflow_id: str) -> bool:
        """Push wf to n8n server using REST API"""
        try:
            from pathlib import Path
            from .crud import WorkflowCRUD

            crud = WorkflowCRUD(self.db, self.config)

            info = crud.get_workflow_info(workflow_id)
            wf = info["wf"]

            # Construct file path from workflow data
            flow_folder = Path(wf.file_folder) if wf.file_folder else self.base_path
            if not flow_folder:
                flow_folder = Path.cwd()

            file_path = flow_folder / f"{workflow_id}.json"

            if not file_path.exists():
                print(f"❌ Workflow file not found: {file_path}")
                return False

            print(f"🔄 Pushing wf {workflow_id} to n8n server...")
            print(f"📋 Workflow: {info['name']}")
            print(f"📄 File: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Check credentials availability first
            if not self._get_n8n_credentials():
                return False

            # Check if wf exists on server
            existing_workflow = self.get_n8n_workflow(workflow_id)

            if existing_workflow:
                # Update existing wf
                print("🔄 Updating existing wf on server...")
                result = self.update_n8n_workflow(workflow_id, workflow_data)
            else:
                # Create new wf
                print("🆕 Creating new wf on server...")
                result = self.create_n8n_workflow(workflow_data)

            if result:
                # Get n8n server version and update wf
                n8n_version = self.get_n8n_version()
                if n8n_version:
                    db_workflow = self.db.get_workflow(workflow_id)
                    if db_workflow:
                        db_workflow.n8n_version_id = n8n_version
                        db_workflow.updated_at = datetime.now(timezone.utc)
                        self.db.update_workflow(db_workflow)

                # Increment push counter
                self.db.increment_push_count(workflow_id)
                print("✅ Workflow pushed successfully")
                return True
            else:
                print("❌ Failed to push wf to server")
                return False

        except Exception as e:
            print(f"❌ Failed to push wf {workflow_id}: {e}")
            return False

    def get_n8n_version(self) -> Optional[str]:
        """Get n8n server version information

        This is optional metadata - failures are silently handled.
        """
        try:
            # The /settings endpoint typically contains version information
            response = self._make_n8n_request("GET", "api/v1/settings", silent=True)
            if response and "data" in response:
                settings = response["data"]
                # Look for version information in various possible fields
                for version_field in ["version", "n8nVersion", "versionCli"]:
                    if version_field in settings:
                        return str(settings[version_field])

            # If version not in settings, try the health endpoint
            health_response = self._make_n8n_request("GET", "healthz", silent=True)
            if health_response:
                return "healthy-{}".format(datetime.now().strftime("%Y%m%d"))

            # Fallback to generic identifier
            return "unknown-{}".format(datetime.now().strftime("%Y%m%d"))

        except Exception:
            # Silent failure - version tracking is optional
            return None
