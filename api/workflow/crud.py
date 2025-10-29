#!/usr/bin/env python3
"""
Core wf CRUD operations and metadata management

Handles: add, remove, list, sync, search, stats wf operations
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import AppConfig
from ..db import DBApi
from ..models import Workflow


class WorkflowCRUD:
    """Core wf CRUD operations"""

    def __init__(self, db: DBApi, config: AppConfig):
        self.db = db
        self.config = config
        self.base_path = config.workflows_path

    def add_workflow(self, workflow_id: str, name: str, n8n_version_id: Optional[str] = None) -> None:
        """Add a new wf to database"""
        # Check if wf already exists
        existing = self.db.get_workflow(workflow_id)
        if existing:
            raise ValueError(f"Workflow with ID '{workflow_id}' already exists")

        wf = Workflow(
            id=workflow_id,
            name=name,
            file=None,
            file_folder=str(self.base_path) if self.base_path else None,
            server_id=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_synced=None,
            n8n_version_id=n8n_version_id,
        )

        self.db.add_workflow(wf)

    def add_workflow_from_file(self, json_file_path: str, name: str) -> None:
        """Add wf from JSON file path"""
        # Resolve the file path relative to flow directory
        if self.base_path:
            file_path = Path(self.base_path) / json_file_path
        else:
            file_path = Path(json_file_path)

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")

        # Read and parse JSON file to get wf ID
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Extract wf ID from JSON
            workflow_id = workflow_data.get("id")
            if not workflow_id:
                raise ValueError(f"No 'id' field found in wf file: {file_path}")

            n8n_version_id = workflow_data.get("n8n_version_id")

            # Add wf using the extracted ID
            self.add_workflow(workflow_id, name, n8n_version_id=n8n_version_id)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in wf file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read wf file {file_path}: {e}")

    def remove_workflow(self, workflow_id: str) -> None:
        """Remove wf from database (file remains untouched)"""
        wf = self.db.get_workflow(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.db.delete_workflow(workflow_id)

    def list_workflows(self, only_backupable: bool = False) -> List[Dict[str, Any]]:
        """List all available workflows from database

        Args:
            only_backupable: Ignored - all workflows from database are returned
        """
        workflows = []
        db_workflows = self.db.list_workflows()

        for wf in db_workflows:
            # Determine flow folder: use wf's file_folder or default to base_path
            flow_folder = Path(wf.file_folder) if wf.file_folder else self.base_path
            if not flow_folder:
                flow_folder = Path.cwd()  # Default to current directory

            # Check if wf file exists: {workflow_id}.json in flow folder
            workflow_file = flow_folder / f"{wf.id}.json"
            file_exists = workflow_file.exists()

            workflow_info = {
                "id": wf.id,
                "name": wf.name,
                "last_synced": wf.last_synced.isoformat() if wf.last_synced else None,
                "status": wf.status,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
                "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
                "push_count": wf.push_count,
                "pull_count": wf.pull_count,
                "file_exists": file_exists,
                "flow_folder": str(flow_folder),
            }
            workflows.append(workflow_info)

        return workflows

    def get_workflow_info(self, id_or_alias: str) -> Dict[str, Any]:
        """Get wf information by ID, name, or alias from database"""
        if id_or_alias == "main":
            workflows = self.db.list_workflows()
            main_workflows = [w for w in workflows if "main" in w.name.lower()]
            if main_workflows:
                id_or_alias = main_workflows[0].id
            else:
                raise ValueError("No main wf found")

        wf = self.db.get_workflow_by_name_or_id(id_or_alias)

        if not wf:
            available = []
            all_workflows = self.db.list_workflows()
            for wf in all_workflows:
                available.append(f"  {wf.id}: {wf.name}")

            raise ValueError(f"Unknown wf ID: {id_or_alias}\nAvailable workflows:\n" + "\n".join(available))

        return {
            "id": wf.id,
            "name": wf.name,
            "wf": wf,
        }

    def search_workflows(self, query: str) -> List[Workflow]:
        """Search workflows in database"""
        return self.db.search_workflows(query)

    def get_workflow_stats(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get wf statistics"""
        if workflow_id:
            # Individual wf stats
            wf = self.db.get_workflow(workflow_id)
            if not wf:
                raise ValueError(f"Workflow {workflow_id} not found")

            stats = {
                "workflow_id": wf.id,
                "id": wf.id,
                "name": wf.name,
                "status": wf.status,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
                "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
                "last_synced": wf.last_synced.isoformat() if wf.last_synced else None,
                "push_count": wf.push_count,
                "pull_count": wf.pull_count,
                "n8n_version_id": wf.n8n_version_id,
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
