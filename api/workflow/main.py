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

    # Delegate to CRUD operations
    def add_workflow(self, workflow_id: str, name: str, filename: Optional[str] = None) -> None:
        """Add a new workflow to database

        Args:
            workflow_id: The workflow ID
            name: Human-readable workflow name
            filename: Custom filename (e.g., 'my-workflow.json')
        """
        return self.crud.add_workflow(workflow_id, name, filename=filename)

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
    def pull_workflow(self, workflow_id: str, filename: Optional[str] = None) -> bool:
        """Pull workflow from n8n server

        Args:
            workflow_id: Workflow ID or name to pull
            filename: Optional filename for new workflows
        """
        return self.n8n_api.pull_workflow(workflow_id, filename=filename)

    def push_workflow(self, workflow_id: str) -> bool:
        """Push workflow to n8n server"""
        return self.n8n_api.push_workflow(workflow_id)

    def delete_n8n_workflow(self, workflow_id: str) -> bool:
        """Delete workflow from n8n server

        Args:
            workflow_id: Workflow ID to delete from server

        Returns:
            bool: True if deletion successful
        """
        return self.n8n_api.delete_n8n_workflow(workflow_id)

    def list_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """List workflows from n8n server"""
        return self.n8n_api.list_n8n_workflows()

    def get_n8n_workflows(self) -> Optional[List[Dict[str, Any]]]:
        """Get workflows from n8n server"""
        return self.n8n_api.get_n8n_workflows()
