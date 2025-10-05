#!/usr/bin/env python3
"""
High-level workflow orchestration with modular components
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..api_keys import KeyApi
from ..config import AppConfig
from ..db import DBApi
from ..models import Workflow
from .backup import WorkflowBackup
from .crud import WorkflowCRUD
from .n8n_api import N8nAPI


class WorkflowApi:
    """High-level workflow orchestration using modular components"""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        base_path: Optional[Path] = None,
        skip_ssl_verify: bool = False,
        remote: Optional[str] = None,
    ) -> None:
        if config is not None:
            self.config: Optional[AppConfig] = config
        elif base_path is not None:
            self.config = AppConfig(base_folder=Path(base_path))
        else:
            # Import at function level to avoid circular import while allowing tests to mock
            from ..config import get_config

            self.config = get_config()

        # Initialize core components
        self.db = DBApi(config=self.config)
        self.key_api = KeyApi(db=self.db, config=self.config)

        # Initialize modular components
        self.crud = WorkflowCRUD(self.db, self.config)
        self.n8n_api = N8nAPI(self.db, self.config, self.key_api, skip_ssl_verify, remote)
        self.backup = WorkflowBackup(self.db, self.config, self.key_api)

    # Delegate to CRUD operations
    def add_workflow(self, workflow_id: str, name: str) -> None:
        """Add a new workflow to database"""
        return self.crud.add_workflow(workflow_id, name)

    def add_workflow_from_file(self, json_file_path: str, name: str) -> None:
        """Add workflow from JSON file path"""
        return self.crud.add_workflow_from_file(json_file_path, name)

    def remove_workflow(self, workflow_id: str) -> None:
        """Remove workflow from database"""
        return self.crud.remove_workflow(workflow_id)

    def list_workflows(self, only_backupable: bool = False) -> List[Dict[str, Any]]:
        """List all workflows"""
        return self.crud.list_workflows(only_backupable)

    def get_workflow_info(self, id_or_alias: str) -> Dict[str, Any]:
        """Get workflow information"""
        return self.crud.get_workflow_info(id_or_alias)

    def search_workflows(self, query: str) -> List[Workflow]:
        """Search workflows"""
        return self.crud.search_workflows(query)

    def get_workflow_stats(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow statistics"""
        return self.crud.get_workflow_stats(workflow_id)

    # Delegate to n8n API operations
    def pull_workflow(self, workflow_id: str) -> bool:
        """Pull workflow from n8n server"""
        return self.n8n_api.pull_workflow(workflow_id)

    def push_workflow(self, workflow_id: str) -> bool:
        """Push workflow to n8n server"""
        return self.n8n_api.push_workflow(workflow_id)

    def list_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """List workflows from n8n server"""
        return self.n8n_api.list_n8n_workflows()

    def get_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """Get workflows from n8n server"""
        return self.n8n_api.get_n8n_workflows()

    # Delegate to backup operations
    def backup_all_workflows(self, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Backup all workflows"""
        return self.backup.backup_all_workflows(backup_dir)

    def create_workflow_backup(self, workflow_id: str, backup_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Create backup for specific workflow"""
        return self.backup.create_workflow_backup(workflow_id, backup_dir)

    def restore_workflows_backup(self, backup_file: Path, force: bool = False) -> bool:
        """Restore workflows from backup"""
        return self.backup.restore_workflows_backup(backup_file, force)

    def verify_backup_integrity(self, backup_file: Path) -> bool:
        """Verify backup integrity"""
        return self.backup.verify_backup_integrity(backup_file)

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all backups"""
        return self.backup.list_backups()
