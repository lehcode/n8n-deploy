#!/usr/bin/env python3

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from api.config import AppConfig, get_config


def normalize_to_slug(text: str) -> str:
    """Convert text to slug format for fuzzy matching.

    "Graphiti Query" -> "graphiti-query"
    "data_processing_job" -> "data-processing-job"

    Args:
        text: Input text to normalize

    Returns:
        Lowercase slug with spaces/underscores replaced by hyphens
    """
    result = text.lower()
    result = re.sub(r"[\s_]+", "-", result)
    result = re.sub(r"[^a-z0-9-]", "", result)
    result = re.sub(r"-+", "-", result)
    return result.strip("-")


from api.db.base import BaseDB
from api.db.schema import SchemaApi
from api.models import DatabaseStats, Workflow, WorkflowStatus


class DBApi(BaseDB):
    """Core database manager for workflow CRUD operations"""

    def __init__(self, config: Optional[AppConfig] = None, db_path: Optional[Union[str, Path]] = None):
        """Initialize with database path and schema manager"""
        # Initialize base class first
        if config:
            super().__init__(config=config)
        elif db_path:
            super().__init__(db_path=db_path)
        else:
            super().__init__(config=get_config())

        self.schema_api = SchemaApi(db_path=self.db_path)

    def _row_to_workflow(self, row: sqlite3.Row) -> Workflow:
        """Convert a database row to a Workflow object.

        Args:
            row: SQLite Row object from query result

        Returns:
            Workflow instance populated from row data
        """
        return Workflow(
            id=row["id"],
            name=row["name"],
            file=row["file"] if "file" in row.keys() else None,
            file_folder=row["file_folder"],
            server_id=row["server_id"] if "server_id" in row.keys() else None,
            status=WorkflowStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_synced=datetime.fromisoformat(row["last_synced"]) if row["last_synced"] else None,
            n8n_version_id=row["n8n_version_id"],
            push_count=row["push_count"] or 0,
            pull_count=row["pull_count"] or 0,
        )

    def add_workflow(self, wf: Workflow) -> str:
        """Add a new workflow to the database"""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO workflows (id, name, file, file_folder, server_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    wf.id,
                    wf.name,
                    wf.file,
                    wf.file_folder,
                    wf.server_id,
                    wf.status,
                    wf.created_at,
                    wf.updated_at,
                ),
            )
            conn.commit()
            return wf.id

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by its ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
            row = cursor.fetchone()
            if row:
                return Workflow(
                    id=row["id"],
                    name=row["name"],
                    file=row["file"] if "file" in row.keys() else None,
                    file_folder=row["file_folder"],
                    server_id=row["server_id"] if "server_id" in row.keys() else None,
                    status=WorkflowStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    last_synced=datetime.fromisoformat(row["last_synced"]) if row["last_synced"] else None,
                    n8n_version_id=row["n8n_version_id"],
                    push_count=row["push_count"] or 0,
                    pull_count=row["pull_count"] or 0,
                )
            return None

    def get_workflow_by_name_or_id(self, name_or_id: str) -> Optional[Workflow]:
        """Get a workflow by its name, ID, or filename with smart matching.

        Lookup priority:
        1. Exact ID match
        2. Exact name match
        3. Case-insensitive name match
        4. Slug-normalized name match (e.g., "graphiti-query" matches "Graphiti Query")
        5. Exact filename match
        6. Filename with .json appended
        7. Basename match (for paths like 'subdir/workflow.json')
        8. Basename with .json appended

        Args:
            name_or_id: Workflow identifier - can be ID, name, slug, or filename

        Returns:
            Workflow if found, None otherwise
        """
        # 1. Try by exact ID match
        wf = self.get_workflow(name_or_id)
        if wf:
            return wf

        with self.get_connection() as conn:
            # 2. Try by exact name match
            cursor = conn.execute("SELECT * FROM workflows WHERE name = ?", (name_or_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_workflow(row)

            # 3. Try case-insensitive name match
            cursor = conn.execute(
                "SELECT * FROM workflows WHERE LOWER(name) = LOWER(?)",
                (name_or_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_workflow(row)

            # 4. Try slug-normalized name match
            input_slug = normalize_to_slug(name_or_id)
            if input_slug:
                cursor = conn.execute("SELECT * FROM workflows")
                for row in cursor.fetchall():
                    if normalize_to_slug(row["name"]) == input_slug:
                        return self._row_to_workflow(row)

            # 5. Try by exact filename match
            cursor = conn.execute("SELECT * FROM workflows WHERE file = ?", (name_or_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_workflow(row)

            # 6. Try with .json appended
            if not name_or_id.endswith(".json"):
                filename_with_json = f"{name_or_id}.json"
                cursor = conn.execute(
                    "SELECT * FROM workflows WHERE file = ?",
                    (filename_with_json,),
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_workflow(row)

            # 7. Try basename match (for paths like 'subdir/workflow.json')
            cursor = conn.execute(
                "SELECT * FROM workflows WHERE file LIKE ? OR file LIKE ?",
                (f"%/{name_or_id}", f"%\\{name_or_id}"),  # Unix and Windows paths
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_workflow(row)

            # 8. Try basename with .json appended
            if not name_or_id.endswith(".json"):
                filename_with_json = f"{name_or_id}.json"
                cursor = conn.execute(
                    "SELECT * FROM workflows WHERE file LIKE ? OR file LIKE ?",
                    (f"%/{filename_with_json}", f"%\\{filename_with_json}"),
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_workflow(row)

            return None

    def list_workflows(self, workflow_type: Optional[str] = None) -> List[Workflow]:
        """List all workflows, optionally filtered by type"""
        with self.get_connection() as conn:
            if workflow_type:
                cursor = conn.execute(
                    """
                    SELECT * FROM workflows WHERE status = ? ORDER BY name
                """,
                    (workflow_type,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM workflows ORDER BY name
                """
                )

            workflows = []
            for row in cursor.fetchall():
                wf = Workflow(
                    id=row["id"],
                    name=row["name"],
                    file=row["file"] if "file" in row.keys() else None,
                    file_folder=row["file_folder"],
                    server_id=row["server_id"] if "server_id" in row.keys() else None,
                    status=WorkflowStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
                    last_synced=datetime.fromisoformat(row["last_synced"]) if row["last_synced"] else None,
                    n8n_version_id=row["n8n_version_id"],
                    push_count=row["push_count"] or 0,
                    pull_count=row["pull_count"] or 0,
                )
                workflows.append(wf)

            return workflows

    def update_workflow(self, wf: Workflow) -> bool:
        """Update an existing wf"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE workflows SET
                    name = ?, file = ?, file_folder = ?, server_id = ?, status = ?, updated_at = ?,
                    last_synced = ?, n8n_version_id = ?,
                    push_count = ?, pull_count = ?
                WHERE id = ?
            """,
                (
                    wf.name,
                    wf.file,
                    wf.file_folder,
                    wf.server_id,
                    wf.status,
                    wf.updated_at,
                    wf.last_synced,
                    wf.n8n_version_id,
                    wf.push_count,
                    wf.pull_count,
                    wf.id,
                ),
            )
            conn.commit()
            return bool(cursor.rowcount > 0)

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM workflows WHERE id = ?
            """,
                (workflow_id,),
            )
            conn.commit()
            return bool(cursor.rowcount > 0)

    def search_workflows(self, query: str) -> List[Workflow]:
        """Search workflows by name or ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM workflows
                WHERE name LIKE ? OR id LIKE ?
                ORDER BY name
                """,
                (f"%{query}%", f"%{query}%"),
            )
            workflows = []
            for row in cursor.fetchall():
                wf = Workflow(
                    id=row["id"],
                    name=row["name"],
                    file=row["file"] if "file" in row.keys() else None,
                    file_folder=row["file_folder"],
                    server_id=row["server_id"] if "server_id" in row.keys() else None,
                    status=WorkflowStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
                    last_synced=datetime.fromisoformat(row["last_synced"]) if row["last_synced"] else None,
                    n8n_version_id=row["n8n_version_id"],
                    push_count=row["push_count"] or 0,
                    pull_count=row["pull_count"] or 0,
                )
                workflows.append(wf)
            return workflows

    # Statistics and Management
    def get_database_stats(self) -> DatabaseStats:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM workflows")
            workflow_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM api_keys")
            api_key_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM dependencies")
            dependency_count = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM configurations")
            configuration_count = cursor.fetchone()[0]

            # Get database file size
            database_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            # Get schema version
            schema_version = self.schema_api.get_schema_version()

            return DatabaseStats(
                database_path=str(self.db_path),
                database_size=database_size,
                schema_version=schema_version,
                tables={
                    "workflows": workflow_count,
                    "api_keys": api_key_count,
                    "dependencies": dependency_count,
                    "configurations": configuration_count,
                },
                last_updated=datetime.now(),
            )

    def compact(self) -> None:
        """Compact database by rebuilding it"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            conn.execute("REINDEX")
            conn.commit()

    def backup(self, backup_path: Union[str, Path]) -> None:
        """Create a backup of the database"""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as conn:
            with sqlite3.connect(backup_path) as backup_conn:
                conn.backup(backup_conn)

    # Push/Pull count tracking
    def increment_push_count(self, workflow_id: str) -> bool:
        """Increment push count for a workflow and update last_used"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE workflows SET
                    push_count = push_count + 1,
                    last_synced = ?,
                    last_used = ?
                WHERE id = ?
            """,
                (datetime.now(), datetime.now(), workflow_id),
            )
            conn.commit()
            return bool(cursor.rowcount > 0)

    def increment_pull_count(self, workflow_id: str) -> bool:
        """Increment pull count for a workflow and update last_used"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE workflows SET
                    pull_count = pull_count + 1,
                    last_synced = ?,
                    last_used = ?
                WHERE id = ?
            """,
                (datetime.now(), datetime.now(), workflow_id),
            )
            conn.commit()
            return bool(cursor.rowcount > 0)

    def create_backup_record(self, backup_metadata: Dict[str, Any]) -> bool:
        """Store backup metadata in the configurations table"""
        from datetime import datetime

        with self.get_connection() as conn:
            # Use modular database schema - configurations table has different structure
            conn.execute(
                """\
                INSERT INTO configurations (
                    name, backup_path, checksum, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    backup_metadata.get("backup_id", "unknown"),
                    backup_metadata.get("backup_path", ""),
                    backup_metadata.get("sha256_hash", ""),
                    datetime.now(timezone.utc).isoformat(),
                    1,
                ),
            )
            conn.commit()

        print(f"✅ Backup metadata stored: {backup_metadata.get('backup_id', 'unknown')}")
        return True

    def get_backup_history(self) -> List[Dict[str, Any]]:
        """Get all backup records from database"""
        backups = []
        with self.get_connection() as conn:
            cursor = conn.execute(
                """\
                SELECT name, backup_path, checksum, created_at FROM configurations
                WHERE is_active = 1
                ORDER BY created_at DESC
            """
            )

            for row in cursor.fetchall():
                backup_data = {
                    "backup_id": row["name"],
                    "backup_path": row["backup_path"],
                    "sha256_hash": row["checksum"],
                    "stored_at": row["created_at"],
                    "in_database": True,
                }
                backups.append(backup_data)

        return backups

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all backup records (alias for get_backup_history)"""
        return self.get_backup_history()

    def get_backup_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get backup record by filename"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """\
                SELECT name, backup_path, checksum, created_at FROM configurations
                WHERE backup_path LIKE ?
                AND is_active = 1
            """,
                (f"%{filename}%",),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "backup_id": row["name"],
                    "backup_path": row["backup_path"],
                    "sha256_hash": row["checksum"],
                    "stored_at": row["created_at"],
                    "in_database": True,
                }

        return None
