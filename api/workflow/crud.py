#!/usr/bin/env python3
"""
Core workflow CRUD operations and metadata management

Handles: add, remove, list, sync, search, stats workflow operations
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import AppConfig
from ..db import DBApi
from ..models import Workflow


class WorkflowCRUD:
    """Core workflow CRUD operations"""

    def __init__(self, db: DBApi, config: AppConfig):
        self.db = db
        self.config = config
        self.base_path = config.workflows_path

    def add_workflow(self, workflow_id: str, name: str, n8n_version_id: Optional[str] = None) -> None:
        """Add a new workflow to database"""
        # Check if workflow already exists
        existing = self.db.get_workflow(workflow_id)
        if existing:
            raise ValueError(f"Workflow with ID '{workflow_id}' already exists")

        workflow = Workflow(
            id=workflow_id,
            name=name,
            file=None,
            file_folder=str(self.base_path) if self.base_path else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_synced=None,
            n8n_version_id=n8n_version_id,
        )

        self.db.add_workflow(workflow)

    def add_workflow_from_file(self, json_file_path: str, name: str) -> None:
        """Add workflow from JSON file path"""
        # Resolve the file path relative to flow directory
        if self.base_path:
            file_path = Path(self.base_path) / json_file_path
        else:
            file_path = Path(json_file_path)

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")

        # Read and parse JSON file to get workflow ID
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Extract workflow ID from JSON
            workflow_id = workflow_data.get("id")
            if not workflow_id:
                raise ValueError(f"No 'id' field found in workflow file: {file_path}")

            n8n_version_id = workflow_data.get("n8n_version_id")

            # Add workflow using the extracted ID
            self.add_workflow(workflow_id, name, n8n_version_id=n8n_version_id)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in workflow file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read workflow file {file_path}: {e}")

    def remove_workflow(self, workflow_id: str) -> None:
        """Remove workflow from database (file remains untouched)"""
        workflow = self.db.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.db.delete_workflow(workflow_id)

    def list_workflows(self, only_backupable: bool = False) -> List[Dict[str, Any]]:
        """List all available workflows from database

        Args:
            only_backupable: Ignored - all workflows from database are returned
        """
        workflows = []
        db_workflows = self.db.list_workflows()

        for workflow in db_workflows:
            # Determine flow folder: use workflow's file_folder or default to base_path
            flow_folder = Path(workflow.file_folder) if workflow.file_folder else self.base_path
            if not flow_folder:
                flow_folder = Path.cwd()  # Default to current directory

            # Check if workflow file exists: {workflow_id}.json in flow folder
            workflow_file = flow_folder / f"{workflow.id}.json"
            file_exists = workflow_file.exists()

            workflow_info = {
                "id": workflow.id,
                "name": workflow.name,
                "last_synced": workflow.last_synced.isoformat() if workflow.last_synced else None,
                "status": workflow.status,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
                "push_count": workflow.push_count,
                "pull_count": workflow.pull_count,
                "file_exists": file_exists,
                "flow_folder": str(flow_folder),
            }
            workflows.append(workflow_info)

        return workflows

    def get_workflow_info(self, id_or_alias: str) -> Dict[str, Any]:
        """Get workflow information by ID or alias from database"""
        if id_or_alias == "main":
            workflows = self.db.list_workflows()
            main_workflows = [w for w in workflows if "main" in w.name.lower()]
            if main_workflows:
                id_or_alias = main_workflows[0].id
            else:
                raise ValueError("No main workflow found")

        workflow = self.db.get_workflow(id_or_alias)

        if not workflow:
            available = []
            all_workflows = self.db.list_workflows()
            for wf in all_workflows:
                available.append(f"  {wf.id}: {wf.name}")

            raise ValueError(f"Unknown workflow ID: {id_or_alias}\nAvailable workflows:\n" + "\n".join(available))

        return {
            "id": workflow.id,
            "name": workflow.name,
            "workflow": workflow,
        }

    def search_workflows(self, query: str) -> List[Workflow]:
        """Search workflows in database"""
        return self.db.search_workflows(query)

    def get_workflow_stats(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow statistics"""
        if workflow_id:
            # Individual workflow stats
            workflow = self.db.get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")

            stats = {
                "workflow_id": workflow.id,
                "id": workflow.id,
                "name": workflow.name,
                "status": workflow.status,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
                "last_synced": workflow.last_synced.isoformat() if workflow.last_synced else None,
                "push_count": workflow.push_count,
                "pull_count": workflow.pull_count,
                "n8n_version_id": workflow.n8n_version_id,
            }

            return stats
        else:
            # Overall statistics
            all_workflows = self.db.list_workflows()
            total_workflows = len(all_workflows)
            total_pushes = sum(w.push_count or 0 for w in all_workflows)
            total_pulls = sum(w.pull_count or 0 for w in all_workflows)

            return {
                "total_workflows": total_workflows,
                "total_push_operations": total_pushes,
                "total_pull_operations": total_pulls,
            }
