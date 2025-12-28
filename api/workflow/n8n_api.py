#!/usr/bin/env python3
"""
n8n server API integration for push/pull operations

Handles: pull, push, server operations
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..api_keys import KeyApi
from ..config import AppConfig
from ..db import DBApi
from ..models import Workflow
from .http_client import N8nHttpClient
from .server_resolver import ServerResolver
from .types import N8nApiErrorType, N8nApiResult


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
        # base_path may be None if flow_folder was not explicitly provided
        self.base_path: Optional[Path] = config.flow_folder
        # Track if flow folder was explicitly provided (--flow-dir or env var)
        self.base_path_explicit = config.flow_folder_explicit

        # HTTP client for API requests
        self._http_client = N8nHttpClient(skip_ssl_verify=skip_ssl_verify)

        # Server resolver for URL and API key resolution
        self._server_resolver = ServerResolver(
            config=config,
            db=db,
            api_manager=api_manager,
            remote=remote,
            skip_ssl_verify=skip_ssl_verify,
        )

    def _get_n8n_credentials(self, workflow_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get n8n API credentials using remote-based resolution

        Args:
            workflow_id: Optional workflow ID for linked server resolution
        """
        return self._server_resolver.get_credentials(workflow_id=workflow_id)

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

        base_url = credentials.get("server_url", "").rstrip("/")
        url = f"{base_url}/{endpoint.lstrip('/')}"

        return self._http_client.request_dict(
            method=method,
            url=url,
            headers=credentials["headers"],
            data=data,
            silent=silent,
            skip_ssl_verify=credentials.get("skip_ssl_verify"),
        )

    def _make_n8n_request_typed(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, silent: bool = False
    ) -> N8nApiResult:
        """Make authenticated request to n8n API with typed result

        Returns N8nApiResult with detailed error information instead of None.
        This allows callers to distinguish between different error types,
        particularly 404 (workflow not found) vs network errors.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Optional request payload
            silent: If True, suppress error messages for failed requests
        """
        credentials = self._get_n8n_credentials()
        if not credentials:
            return N8nApiResult(
                success=False,
                error_type=N8nApiErrorType.AUTH_FAILURE,
                error_message="No API credentials available",
            )

        base_url = credentials.get("server_url", "").rstrip("/")
        url = f"{base_url}/{endpoint.lstrip('/')}"

        return self._http_client.request(
            method=method,
            url=url,
            headers=credentials["headers"],
            data=data,
            silent=silent,
            skip_ssl_verify=credentials.get("skip_ssl_verify"),
        )

    def get_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch all workflows from n8n server"""
        result = self._make_n8n_request("GET", "api/v1/workflows")
        if result and isinstance(result, dict) and "data" in result:
            data = result["data"]
            return data if isinstance(data, list) else None
        return result if isinstance(result, list) else None

    def get_n8n_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Fetch specific workflow from n8n server by ID"""
        return self._make_n8n_request("GET", f"api/v1/workflows/{workflow_id}")

    def get_n8n_workflow_typed(self, workflow_id: str) -> N8nApiResult:
        """Fetch specific workflow from n8n server by ID with typed result

        Returns N8nApiResult that distinguishes 404 (not found) from other errors.
        Use this when you need to differentiate between "workflow doesn't exist"
        and "cannot reach server" (e.g., during push operations).

        Args:
            workflow_id: The workflow ID to fetch

        Returns:
            N8nApiResult with success=True and data if found,
            or success=False with appropriate error_type
        """
        return self._make_n8n_request_typed("GET", f"api/v1/workflows/{workflow_id}")

    def _strip_readonly_fields(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Strip read-only fields that n8n API rejects on create/update.

        Uses a whitelist approach to ensure only n8n-accepted fields are sent.
        Based on n8n API v1 documentation and GitHub issue #19587.

        Allowed root fields: name, nodes, connections, settings, staticData
        """
        # Whitelist of fields accepted by n8n API for create/update
        allowed_root_fields = {
            "name",
            "nodes",
            "connections",
            "settings",
            "staticData",
        }

        # Valid settings fields accepted by n8n API (whitelist)
        valid_settings_fields = {
            "executionOrder",
            "callerPolicy",
            "saveDataErrorExecution",
            "saveDataSuccessExecution",
            "saveManualExecutions",
            "saveExecutionProgress",
            "executionTimeout",
            "errorWorkflow",
            "timezone",
        }

        # Only keep allowed root fields
        result = {k: v for k, v in workflow_data.items() if k in allowed_root_fields}

        # Filter settings object to only include valid fields
        if "settings" in result and isinstance(result["settings"], dict):
            result["settings"] = {k: v for k, v in result["settings"].items() if k in valid_settings_fields}

        return result

    def create_n8n_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new workflow on n8n server"""
        clean_data = self._strip_readonly_fields(workflow_data)
        return self._make_n8n_request("POST", "api/v1/workflows", clean_data)

    def update_n8n_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing workflow on n8n server"""
        clean_data = self._strip_readonly_fields(workflow_data)
        return self._make_n8n_request("PUT", f"api/v1/workflows/{workflow_id}", clean_data)

    def delete_n8n_workflow(self, workflow_id: str) -> bool:
        """Delete workflow from n8n server

        Args:
            workflow_id: The workflow ID to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        credentials = self._get_n8n_credentials(workflow_id=workflow_id)
        if not credentials:
            return False

        server_url = credentials.get("server_url", "unknown")
        print(f"🗑️  Deleting workflow {workflow_id} from {server_url}...")

        base_url = server_url.rstrip("/")
        url = f"{base_url}/api/v1/workflows/{workflow_id}"

        success = self._http_client.delete_workflow(
            url=url,
            headers=credentials["headers"],
            skip_ssl_verify=credentials.get("skip_ssl_verify"),
        )

        if success:
            return True
        else:
            # HTTP client already printed error message
            return False

    def list_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """List all workflows from n8n server (alias for get_n8n_workflows)"""
        return self.get_n8n_workflows()

    def pull_workflow(self, workflow_id: str, filename: Optional[str] = None) -> bool:
        """Pull workflow from n8n server using REST API

        Args:
            workflow_id: Workflow ID or name to pull
            filename: Optional filename for new workflows. If not provided and
                     workflow doesn't exist in database, uses {id}.json
        """
        try:
            from .crud import WorkflowCRUD

            # Try to resolve workflow name to ID if it exists in database
            crud = WorkflowCRUD(self.db, self.config)
            try:
                info = crud.get_workflow_info(workflow_id)
                actual_id = info["wf"].id
            except ValueError:
                # Workflow not in database, use provided ID directly
                actual_id = workflow_id

            # Check credentials availability (resolves server URL with workflow context)
            credentials = self._get_n8n_credentials(workflow_id=actual_id)
            if not credentials:
                return False

            server_url = credentials.get("server_url", "unknown server")

            # Print pull message
            try:
                info = crud.get_workflow_info(actual_id)
                print(f"🔄 Pulling workflow {actual_id} ({info['name']}) from {server_url}...")
            except ValueError:
                print(f"🔄 Pulling workflow {actual_id} from {server_url}...")

            workflow_data = self.get_n8n_workflow(actual_id)

            if not workflow_data:
                print(f"❌ Workflow {actual_id} not found on server")
                return False

            print(f"📋 Workflow: {workflow_data.get('name', 'Unknown')} ({workflow_data.get('id', actual_id)})")
            print(f"🎯 Active: {workflow_data.get('active', False)}")
            print(f"📊 Nodes: {len(workflow_data.get('nodes', []))}")

            # Determine filename for saving
            # Priority: 1) existing workflow's stored filename, 2) --filename option, 3) {id}.json
            existing_workflow = self.db.get_workflow(actual_id)
            if existing_workflow and existing_workflow.file:
                # Existing workflow - use stored filename
                target_filename = existing_workflow.file
            elif filename:
                # New workflow with explicit filename
                target_filename = filename
            else:
                # New workflow - use {id}.json as default
                target_filename = f"{actual_id}.json"

            # Determine save directory
            # Priority: explicit --flow-dir > DB-stored file_folder > base_folder > cwd
            if self.base_path_explicit and self.base_path:
                # User explicitly provided --flow-dir, use it
                save_folder = self.base_path
            elif existing_workflow and existing_workflow.file_folder:
                # Existing workflow - use stored folder
                save_folder = Path(existing_workflow.file_folder)
            elif self.base_path:
                # Fallback to environment variable or config
                save_folder = self.base_path
            else:
                # Ultimate fallback to current directory with warning
                save_folder = Path.cwd()
                print(f"⚠️  No flow directory specified, using current directory: {save_folder}")

            workflow_path = save_folder / target_filename
            with open(workflow_path, "w", encoding="utf-8") as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)

            print(f"📄 Saved to: {workflow_path}")

            # Get n8n server version for tracking
            n8n_version = self.get_n8n_version()

            # Check if workflow exists in database, if not add it
            if not existing_workflow:
                # Add new workflow with n8n version
                wf = Workflow(
                    id=actual_id,
                    name=workflow_data.get("name", "Unknown"),
                    file=target_filename,
                    file_folder=str(save_folder),  # Store resolved save folder
                    server_id=None,  # Will be set if workflow is linked to a server
                    n8n_version_id=n8n_version,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    last_synced=datetime.now(timezone.utc),
                )
                self.db.add_workflow(wf)
            else:
                # Update existing workflow with n8n version
                existing_workflow.n8n_version_id = n8n_version
                existing_workflow.updated_at = datetime.now(timezone.utc)
                existing_workflow.last_synced = datetime.now(timezone.utc)
                self.db.update_workflow(existing_workflow)

            # Increment pull counter
            self.db.increment_pull_count(actual_id)
            print("✅ Workflow pulled successfully")
            return True

        except Exception as e:
            # Print specific error details, but let CLI handle the summary message
            print(f"❌ Error: {e}")
            return False

    def _update_workflow_id_after_recreate(
        self,
        old_id: str,
        new_id: str,
        file_path: Path,
        flow_folder: Path,
    ) -> bool:
        """Update workflow ID in database and JSON file after server reassignment

        Called when a stale workflow ID is detected (404) and a new workflow
        is created on the server. Updates local state to match server.

        Args:
            old_id: The stale/local workflow ID
            new_id: The new server-assigned ID
            file_path: Path to the workflow JSON file
            flow_folder: Path to the flow directory

        Returns:
            bool: True if update successful
        """
        # Get the current workflow data from database
        db_workflow = self.db.get_workflow(old_id)
        if not db_workflow:
            print(f"⚠️  Could not find workflow {old_id} in database")
            return False

        # Create new workflow entry with server ID
        new_wf = Workflow(
            id=new_id,
            name=db_workflow.name,
            file=db_workflow.file,  # Keep original filename
            file_folder=str(flow_folder),
            server_id=db_workflow.server_id,
            status=db_workflow.status,
            created_at=db_workflow.created_at,
            updated_at=datetime.now(timezone.utc),
            last_synced=datetime.now(timezone.utc),
            n8n_version_id=self.get_n8n_version(),
            push_count=(db_workflow.push_count or 0) + 1,
            pull_count=db_workflow.pull_count or 0,
        )

        # Update the JSON file with new server ID (keep same filename)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    workflow_content = json.load(f)
                workflow_content["id"] = new_id
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(workflow_content, f, indent=2, ensure_ascii=False)
                print(f"📄 Updated workflow ID in file: {file_path.name}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Could not update workflow file: {e}")

        # Update database: remove old ID, add new ID
        self.db.delete_workflow(old_id)
        self.db.add_workflow(new_wf)
        print(f"🔄 Workflow ID updated in database: {old_id} → {new_id}")
        return True

    def push_workflow(self, workflow_id: str) -> bool:
        """Push workflow to n8n server using REST API"""
        try:
            from .crud import WorkflowCRUD

            crud = WorkflowCRUD(self.db, self.config)

            info = crud.get_workflow_info(workflow_id)
            wf = info["wf"]
            # Use actual workflow ID from database (workflow_id param might be a name)
            actual_id = wf.id

            # Construct file path from workflow data using stored filename
            # Priority: explicit --flow-dir > DB-stored file_folder > base_folder > cwd
            if self.base_path_explicit and self.base_path:
                # User explicitly provided --flow-dir, use it
                flow_folder = self.base_path
            elif wf.file_folder:
                # Use DB-stored path from workflow registration
                flow_folder = Path(wf.file_folder)
            elif self.base_path:
                # Fallback to environment variable or config
                flow_folder = self.base_path
            else:
                # Ultimate fallback to current directory with warning
                flow_folder = Path.cwd()
                print(f"⚠️  No flow directory specified, using current directory: {flow_folder}")

            # Use stored filename or fallback to {id}.json
            filename = crud.get_workflow_filename(wf)
            file_path = flow_folder / filename

            if not file_path.exists():
                print(f"❌ Workflow file not found: {file_path}")
                return False

            with open(file_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Check credentials availability (resolves server URL with workflow context)
            credentials = self._get_n8n_credentials(workflow_id=actual_id)
            if not credentials:
                return False

            server_url = credentials.get("server_url", "unknown server")
            print(f"🔄 Pushing workflow {actual_id} to {server_url}...")
            print(f"📋 Workflow: {info['name']}")
            print(f"📄 File: {file_path}")

            # Check if workflow exists on server using typed result
            # This allows us to distinguish 404 (stale ID) from network errors
            server_check = self.get_n8n_workflow_typed(actual_id)
            workflow_recreated = False

            if server_check.success:
                # Workflow exists on server - update it
                print("🔄 Updating existing workflow on server...")
                result = self.update_n8n_workflow(actual_id, workflow_data)
            elif server_check.is_not_found:
                # 404: Workflow ID is stale - it doesn't exist on server anymore
                # This happens when workflow was deleted/archived on server
                print(f"⚠️  Workflow {actual_id} not found on server (may have been deleted)")
                print("🆕 Creating new workflow on server...")
                result = self.create_n8n_workflow(workflow_data)
                workflow_recreated = True
            elif server_check.is_network_error:
                # Network/connection issue - don't create new workflow, abort
                print("❌ Cannot verify workflow on server (network error)")
                print(f"   Error: {server_check.error_message}")
                print("   Push aborted - please check your network connection")
                return False
            else:
                # Other error (auth, server error, etc.) - don't create new workflow
                print("❌ Cannot verify workflow on server")
                print(f"   Error: {server_check.error_message}")
                print("   Push aborted - please check server status and credentials")
                return False

            if result:
                # Handle ID update for recreated workflows (stale ID or draft ID)
                new_server_id = result.get("id")
                if new_server_id and new_server_id != actual_id:
                    if workflow_recreated:
                        print(f"🔄 Updating stale ID {actual_id} to new server ID {new_server_id}...")
                    else:
                        print(f"🔄 Updating draft ID {actual_id} to server ID {new_server_id}...")

                    self._update_workflow_id_after_recreate(actual_id, new_server_id, file_path, flow_folder)
                    print("✅ Workflow pushed successfully (recreated with new ID)")
                    return True

                # Get n8n server version and update wf
                n8n_version = self.get_n8n_version()
                if n8n_version:
                    db_workflow = self.db.get_workflow(actual_id)
                    if db_workflow:
                        db_workflow.n8n_version_id = n8n_version
                        db_workflow.updated_at = datetime.now(timezone.utc)
                        self.db.update_workflow(db_workflow)

                # Increment push counter
                self.db.increment_push_count(actual_id)
                print("✅ Workflow pushed successfully")
                return True
            else:
                print("❌ Failed to push workflow to server")
                return False

        except Exception as e:
            print(f"❌ Failed to push workflow {workflow_id}: {e}")
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
