#!/usr/bin/env python3
"""
Folder synchronization manager for n8n-deploy

Coordinates bidirectional synchronization between local folders and
n8n server folders. Uses the internal API for folder operations and
the public API for workflow operations.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import AppConfig
from ..db import DBApi
from ..db.folders import FolderDB
from ..db.servers import ServerCrud
from ..models import (
    FolderMapping,
    N8nFolder,
    ServerCredentials,
    SyncDirection,
    SyncResult,
)
from .n8n_api import N8nAPI
from .n8n_internal_api import N8nInternalClient


class FolderSyncManager:
    """Manages folder synchronization between local and n8n server

    Combines internal API (for folders) with public API (for workflows)
    to provide folder-based workflow management.
    """

    def __init__(
        self,
        config: AppConfig,
        db: DBApi,
        folder_db: FolderDB,
        server_id: int,
        skip_ssl_verify: bool = False,
    ) -> None:
        """Initialize folder sync manager

        Args:
            config: Application configuration
            db: Main database API
            folder_db: Folder-specific database operations
            server_id: ID of the server to sync with
            skip_ssl_verify: Skip SSL verification
        """
        self.config = config
        self.db = db
        self.folder_db = folder_db
        self.server_id = server_id
        self.skip_ssl_verify = skip_ssl_verify

        # Get server details
        server_crud = ServerCrud(config=config)
        server = server_crud.get_server_by_id(server_id)
        if not server:
            raise ValueError(f"Server with ID {server_id} not found")
        self._server: Dict[str, Any] = server

        # Initialize internal API client
        self._internal_client = N8nInternalClient(
            base_url=str(self._server["url"]),
            skip_ssl_verify=skip_ssl_verify,
        )

        # Internal API client (initialized on connect)
        self._connected = False

    @property
    def server_url(self) -> str:
        """Get the server URL"""
        return str(self._server["url"])

    @property
    def server_name(self) -> str:
        """Get the server name"""
        return str(self._server["name"])

    def connect(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        cookie: Optional[str] = None,
    ) -> bool:
        """Connect to n8n server using stored or provided credentials

        Args:
            email: n8n login email (optional if using stored credentials)
            password: n8n login password
            cookie: Session cookie (alternative to email/password)

        Returns:
            True if connection successful
        """
        # Try cookie first if provided
        if cookie:
            self._internal_client.set_session_cookie(cookie)
            if self._internal_client.test_connection():
                self._connected = True
                # Update stored credentials
                creds = ServerCredentials(
                    server_id=self.server_id,
                    email=email or "cookie-auth",
                    session_cookie=cookie,
                    cookie_expires_at=self._internal_client.get_cookie_expiry(),
                )
                self.folder_db.save_server_credentials(creds)
                return True

        # Try stored credentials
        stored_creds = self.folder_db.get_server_credentials(self.server_id)
        if stored_creds and stored_creds.session_cookie:
            self._internal_client.set_session_cookie(stored_creds.session_cookie)
            if self._internal_client.test_connection():
                self._connected = True
                return True

        # Try email/password authentication
        if email and password:
            if self._internal_client.authenticate(email, password):
                self._connected = True
                # Store credentials for future use
                creds = ServerCredentials(
                    server_id=self.server_id,
                    email=email,
                    session_cookie=self._internal_client._session_cookie,
                    cookie_expires_at=self._internal_client.get_cookie_expiry(),
                )
                self.folder_db.save_server_credentials(creds)
                return True

        return False

    def is_connected(self) -> bool:
        """Check if connected to server"""
        return self._connected and self._internal_client.is_authenticated

    # ==================== FOLDER DISCOVERY ====================

    def discover_folders(self) -> List[N8nFolder]:
        """Discover all folders on the n8n server

        Returns:
            List of N8nFolder objects representing remote folders
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to server")

        discovered: List[N8nFolder] = []

        # Get all projects
        projects = self._internal_client.get_projects()
        if not projects:
            return discovered

        for project in projects:
            project_id = project.get("id")
            if not project_id:
                continue

            # Get folders in this project
            folders = self._internal_client.list_folders(project_id)
            if not folders:
                continue

            # Build folder objects with full paths
            for folder in folders:
                folder_path = self._internal_client.build_folder_path(folders, folder["id"])
                n8n_folder = N8nFolder(
                    n8n_folder_id=folder["id"],
                    n8n_project_id=project_id,
                    folder_path=folder_path,
                    server_id=self.server_id,
                )
                discovered.append(n8n_folder)

                # Store/update in database
                self.folder_db.upsert_n8n_folder(n8n_folder)

        return discovered

    def get_folder_by_path(self, path: str) -> Optional[N8nFolder]:
        """Get a folder by its path

        Args:
            path: Folder path like "openminded/test"

        Returns:
            N8nFolder or None if not found
        """
        # Check local cache first
        local = self.folder_db.get_n8n_folder_by_path(path, self.server_id)
        if local:
            return local

        # Discover from server
        folders = self.discover_folders()
        for folder in folders:
            if folder.folder_path == path:
                return folder

        return None

    def ensure_folder_exists(self, path: str) -> Optional[N8nFolder]:
        """Ensure a folder path exists, creating if necessary

        Args:
            path: Folder path like "openminded/test"

        Returns:
            N8nFolder or None on failure
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to server")

        # Check if already exists
        existing = self.get_folder_by_path(path)
        if existing:
            return existing

        # Get personal project (default for new folders)
        project = self._internal_client.get_personal_project()
        if not project:
            return None

        project_id = project["id"]

        # Create folder path
        folder_id = self._internal_client.get_or_create_folder_path(project_id, path)
        if not folder_id:
            return None

        # Refresh and return
        self.discover_folders()
        return self.get_folder_by_path(path)

    # ==================== WORKFLOW SYNC ====================

    def get_workflows_in_folder(self, folder_path: str) -> Optional[List[Dict[str, Any]]]:
        """Get all workflows in a remote folder

        Args:
            folder_path: Path to the folder

        Returns:
            List of workflow dicts or None
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to server")

        folder = self.get_folder_by_path(folder_path)
        if not folder:
            return None

        return self._internal_client.get_workflows_in_folder(folder.n8n_folder_id)

    def sync_pull_folder(
        self,
        n8n_path: str,
        local_path: Path,
        dry_run: bool = False,
    ) -> SyncResult:
        """Pull workflows from n8n folder to local directory

        Args:
            n8n_path: Remote folder path
            local_path: Local directory path
            dry_run: If True, don't make changes

        Returns:
            SyncResult with operation details
        """
        result = SyncResult(success=True)

        if not self.is_connected():
            result.success = False
            result.errors.append("Not connected to server")
            return result

        # Ensure local directory exists
        if not dry_run:
            local_path.mkdir(parents=True, exist_ok=True)

        # Get remote workflows
        workflows = self.get_workflows_in_folder(n8n_path)
        if workflows is None:
            result.success = False
            result.errors.append(f"Could not access folder: {n8n_path}")
            return result

        for wf in workflows:
            wf_id: Optional[str] = wf.get("id")
            wf_name: str = wf.get("name", "Unknown")

            if not wf_id:
                result.warnings.append(f"Skipping workflow with no ID: {wf_name}")
                continue

            if dry_run:
                print(f"  [DRY RUN] Would pull: {wf_name} ({wf_id})")
                result.pulled += 1
                continue

            # Determine filename
            existing = self.db.get_workflow(wf_id)
            if existing and existing.file:
                filename = existing.file
            else:
                # Sanitize name for filename
                safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in wf_name)
                filename = f"{safe_name}.json"

            file_path = local_path / filename

            try:
                # Save workflow JSON
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(wf, f, indent=2, ensure_ascii=False)

                # Update database
                from ..models import Workflow, WorkflowStatus

                db_wf = Workflow(
                    id=wf_id,
                    name=wf_name,
                    file=filename,
                    file_folder=str(local_path),
                    server_id=self.server_id,
                    status=WorkflowStatus.ACTIVE,
                    last_synced=datetime.now(timezone.utc),
                    n8n_version_id=None,
                )

                if existing:
                    db_wf.created_at = existing.created_at
                    db_wf.push_count = existing.push_count
                    db_wf.pull_count = (existing.pull_count or 0) + 1
                    self.db.update_workflow(db_wf)
                else:
                    self.db.add_workflow(db_wf)

                print(f"  Pulled: {wf_name} -> {filename}")
                result.pulled += 1

            except Exception as e:
                result.errors.append(f"Failed to pull {wf_name}: {e}")

        # Update folder sync time
        folder = self.get_folder_by_path(n8n_path)
        if folder and folder.id:
            self.folder_db.update_n8n_folder_sync_time(folder.id)

        return result

    def sync_push_folder(
        self,
        local_path: Path,
        n8n_path: str,
        create_folder: bool = False,
        dry_run: bool = False,
    ) -> SyncResult:
        """Push workflows from local directory to n8n folder

        Args:
            local_path: Local directory path
            n8n_path: Remote folder path
            create_folder: Create folder if it doesn't exist
            dry_run: If True, don't make changes

        Returns:
            SyncResult with operation details
        """
        result = SyncResult(success=True)

        if not self.is_connected():
            result.success = False
            result.errors.append("Not connected to server")
            return result

        if not local_path.exists():
            result.success = False
            result.errors.append(f"Local path does not exist: {local_path}")
            return result

        # Ensure remote folder exists
        folder = self.get_folder_by_path(n8n_path)
        if not folder:
            if create_folder:
                if dry_run:
                    print(f"  [DRY RUN] Would create folder: {n8n_path}")
                else:
                    folder = self.ensure_folder_exists(n8n_path)
                    if not folder:
                        result.success = False
                        result.errors.append(f"Could not create folder: {n8n_path}")
                        return result
            else:
                result.success = False
                result.errors.append(f"Folder does not exist: {n8n_path} (use --create to create)")
                return result

        # Find JSON files in local directory
        json_files = list(local_path.glob("*.json"))
        if not json_files:
            result.warnings.append(f"No JSON files found in: {local_path}")
            return result

        from ..api_keys import KeyApi

        api_manager = KeyApi(db=self.db, config=self.config)
        n8n_api = N8nAPI(
            db=self.db,
            config=self.config,
            api_manager=api_manager,
            skip_ssl_verify=self.skip_ssl_verify,
        )

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    wf_data = json.load(f)

                wf_id = wf_data.get("id")
                wf_name = wf_data.get("name", json_file.stem)

                if dry_run:
                    print(f"  [DRY RUN] Would push: {json_file.name}")
                    result.pushed += 1
                    continue

                # Push via public API
                if wf_id:
                    # Try update first
                    existing = n8n_api.get_n8n_workflow(wf_id)
                    if existing:
                        response = n8n_api.update_n8n_workflow(wf_id, wf_data)
                    else:
                        response = n8n_api.create_n8n_workflow(wf_data)
                else:
                    response = n8n_api.create_n8n_workflow(wf_data)

                if not response:
                    result.errors.append(f"Failed to push: {json_file.name}")
                    continue

                new_id = response.get("id", wf_id)

                # Move to folder via internal API
                if folder:
                    self._internal_client.move_workflow_to_folder(new_id, folder.n8n_folder_id)

                # Update local file if ID changed
                if new_id and new_id != wf_id:
                    wf_data["id"] = new_id
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump(wf_data, f, indent=2, ensure_ascii=False)

                print(f"  Pushed: {json_file.name} -> {n8n_path}")
                result.pushed += 1

            except json.JSONDecodeError as e:
                result.errors.append(f"Invalid JSON in {json_file.name}: {e}")
            except Exception as e:
                result.errors.append(f"Failed to push {json_file.name}: {e}")

        return result

    def sync_bidirectional(
        self,
        mapping: FolderMapping,
        dry_run: bool = False,
    ) -> SyncResult:
        """Perform bidirectional sync based on mapping

        Args:
            mapping: FolderMapping configuration
            dry_run: If True, don't make changes

        Returns:
            Combined SyncResult
        """
        result = SyncResult(success=True)

        # Get folder info
        n8n_folder = self.folder_db.get_n8n_folder(mapping.n8n_folder_id)
        if not n8n_folder:
            result.success = False
            result.errors.append("N8n folder not found in database")
            return result

        local_path = Path(mapping.local_path)
        n8n_path = n8n_folder.folder_path

        # Determine what to sync based on direction
        if mapping.sync_direction in (SyncDirection.PULL, SyncDirection.BIDIRECTIONAL):
            print(f"Pulling from {n8n_path}...")
            pull_result = self.sync_pull_folder(n8n_path, local_path, dry_run)
            result.pulled = pull_result.pulled
            result.errors.extend(pull_result.errors)
            result.warnings.extend(pull_result.warnings)
            if not pull_result.success:
                result.success = False

        if mapping.sync_direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
            print(f"Pushing to {n8n_path}...")
            push_result = self.sync_push_folder(local_path, n8n_path, create_folder=True, dry_run=dry_run)
            result.pushed = push_result.pushed
            result.errors.extend(push_result.errors)
            result.warnings.extend(push_result.warnings)
            if not push_result.success:
                result.success = False

        return result

    # ==================== MAPPING MANAGEMENT ====================

    def create_mapping(
        self,
        local_path: str,
        n8n_path: str,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
    ) -> Optional[FolderMapping]:
        """Create a new folder mapping

        Args:
            local_path: Local directory path
            n8n_path: Remote n8n folder path
            direction: Sync direction

        Returns:
            Created FolderMapping or None on failure
        """
        # Ensure n8n folder is in database
        folder = self.get_folder_by_path(n8n_path)
        if not folder:
            folder = self.ensure_folder_exists(n8n_path)
            if not folder or folder.id is None:
                return None

        folder_id = folder.id
        if folder_id is None:
            return None

        mapping = FolderMapping(
            local_path=local_path,
            n8n_folder_id=folder_id,
            sync_direction=direction,
        )

        mapping_id = self.folder_db.add_folder_mapping(mapping)
        mapping.id = mapping_id
        return mapping

    def get_mappings(self) -> List[Tuple[FolderMapping, N8nFolder]]:
        """Get all folder mappings with their n8n folder info

        Returns:
            List of (FolderMapping, N8nFolder) tuples
        """
        result: List[Tuple[FolderMapping, N8nFolder]] = []
        mappings = self.folder_db.list_folder_mappings()

        for mapping in mappings:
            folder = self.folder_db.get_n8n_folder(mapping.n8n_folder_id)
            if folder:
                result.append((mapping, folder))

        return result

    def sync_all_mappings(self, dry_run: bool = False) -> SyncResult:
        """Sync all configured folder mappings

        Args:
            dry_run: If True, don't make changes

        Returns:
            Combined SyncResult
        """
        result = SyncResult(success=True)
        mappings = self.get_mappings()

        for mapping, folder in mappings:
            print(f"\nSyncing: {mapping.local_path} <-> {folder.folder_path}")
            sync_result = self.sync_bidirectional(mapping, dry_run)

            result.pushed += sync_result.pushed
            result.pulled += sync_result.pulled
            result.conflicts += sync_result.conflicts
            result.errors.extend(sync_result.errors)
            result.warnings.extend(sync_result.warnings)

            if not sync_result.success:
                result.success = False

        return result
