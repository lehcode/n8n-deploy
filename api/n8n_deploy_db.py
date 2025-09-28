#!/usr/bin/env python3
"""
n8n_deploy_ - Robust SQLite database manager for workflow metadata
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Iterator
from contextlib import contextmanager

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    Workflow,
    WorkflowVersion,
    WorkflowType,
    WorkflowStatus,
    WorkflowDependency,
    WorkflowConfiguration,
    DatabaseStats,
)
from api.config import n8n_deploy_Config, get_legacy_config


class n8n_deploy_DB:
    """n8n_deploy_ database manager - where workflows transform and mature"""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        config: Optional[n8n_deploy_Config] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        # Support both new config system and legacy db_path parameter
        if config is not None:
            self.db_path = config.database_path
        elif db_path is not None:
            self.db_path = Path(db_path)
        else:
            # Fall back to legacy behavior for backward compatibility
            legacy_config = get_legacy_config()
            self.db_path = legacy_config.database_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_database()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections"""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA synchronous = NORMAL")

        assert self._connection is not None  # Type guard for mypy
        try:
            yield self._connection
        finally:
            pass  # Keep connection open for reuse

    def close(self) -> None:
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            if not os.getenv("N8N_DEPLOY_TESTING"):
                print("🎭 Database connection closed")

    def _initialize_database(self) -> None:
        """Initialize database schema"""
        schema_sql = """
        -- Schema version tracking
        CREATE TABLE IF NOT EXISTS schema_info (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Core workflows table
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT CHECK(type IN ('main', 'subflow', 'utility')) DEFAULT 'main',
            description TEXT,
            file_path TEXT NOT NULL,
            node_count INTEGER DEFAULT 0,
            status TEXT CHECK(status IN ('active', 'inactive', 'archived')) DEFAULT 'active',
            tags TEXT, -- JSON array of tags
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_synced DATETIME,
            n8n_version_id TEXT
        );


        -- Workflow configuration snapshots
        CREATE TABLE IF NOT EXISTS configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT NOT NULL,
            config_type TEXT NOT NULL, -- 'settings', 'credentials', 'variables'
            config_data TEXT NOT NULL, -- JSON configuration
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_workflows_type ON workflows(type);
        CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
        CREATE INDEX IF NOT EXISTS idx_workflows_updated ON workflows(updated_at);
        CREATE INDEX IF NOT EXISTS idx_configurations_workflow ON configurations(workflow_id);

        -- Full-text search
        CREATE VIRTUAL TABLE IF NOT EXISTS workflows_fts USING fts5(
            id, name, description, tags,
            content=workflows,
            content_rowid=rowid
        );

        -- Triggers to maintain FTS index
        CREATE TRIGGER IF NOT EXISTS workflows_fts_insert AFTER INSERT ON workflows BEGIN
            INSERT INTO workflows_fts(rowid, id, name, description, tags)
            VALUES (new.rowid, new.id, new.name, new.description, new.tags);
        END;

        CREATE TRIGGER IF NOT EXISTS workflows_fts_delete AFTER DELETE ON workflows BEGIN
            INSERT INTO workflows_fts(workflows_fts, rowid, id, name, description, tags)
            VALUES('delete', old.rowid, old.id, old.name, old.description, old.tags);
        END;

        CREATE TRIGGER IF NOT EXISTS workflows_fts_update AFTER UPDATE ON workflows BEGIN
            INSERT INTO workflows_fts(workflows_fts, rowid, id, name, description, tags)
            VALUES('delete', old.rowid, old.id, old.name, old.description, old.tags);
            INSERT INTO workflows_fts(rowid, id, name, description, tags)
            VALUES (new.rowid, new.id, new.name, new.description, new.tags);
        END;

        -- Trigger to update updated_at timestamp
        CREATE TRIGGER IF NOT EXISTS workflows_updated_at AFTER UPDATE ON workflows BEGIN
            UPDATE workflows SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;

        -- API key storage
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_key TEXT NOT NULL, -- API key
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_used DATETIME,
            expires_at DATETIME,
            is_active BOOLEAN DEFAULT 1,
            description TEXT
        );

        -- Index for faster API key lookups
        CREATE INDEX IF NOT EXISTS idx_api_keys_name ON api_keys(name);
        CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
        """

        with self.get_connection() as conn:
            conn.executescript(schema_sql)

            # Record schema version
            cursor = conn.execute(
                "SELECT version FROM schema_info WHERE version = ?",
                (self.SCHEMA_VERSION,),
            )
            if not cursor.fetchone():
                conn.execute(
                    "INSERT INTO schema_info (version) VALUES (?)",
                    (self.SCHEMA_VERSION,),
                )

            conn.commit()

        if not os.getenv("N8N_DEPLOY_TESTING"):
            print("🎭 Database initialized")

    def create_workflow(self, workflow: Workflow) -> str:
        """Create a new workflow record"""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO workflows (
                    id, name, type, description, file_path, node_count, status, tags,
                    created_at, updated_at, last_synced, n8n_version_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    workflow.id,
                    workflow.name,
                    workflow.type,
                    workflow.description,
                    workflow.file_path,
                    workflow.node_count,
                    workflow.status,
                    json.dumps(workflow.tags),
                    workflow.created_at.isoformat(),
                    workflow.updated_at.isoformat(),
                    workflow.last_synced.isoformat() if workflow.last_synced else None,
                    workflow.n8n_version_id,
                ),
            )
            conn.commit()

        print(f"✅ Created workflow: {workflow.name} ({workflow.id})")
        return workflow.id

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
            )
            row = cursor.fetchone()

            if row:
                return Workflow(
                    id=row["id"],
                    name=row["name"],
                    type=row["type"],
                    description=row["description"],
                    file_path=row["file_path"],
                    node_count=row["node_count"],
                    status=row["status"],
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    last_synced=(
                        datetime.fromisoformat(row["last_synced"])
                        if row["last_synced"]
                        else None
                    ),
                    n8n_version_id=row["n8n_version_id"],
                )

        return None

    def list_workflows(
        self, status: Optional[str] = None, workflow_type: Optional[str] = None
    ) -> List[Workflow]:
        """List workflows with optional filtering"""
        query = "SELECT * FROM workflows WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if workflow_type:
            query += " AND type = ?"
            params.append(workflow_type)

        query += " ORDER BY updated_at DESC"

        workflows = []
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                workflows.append(
                    Workflow(
                        id=row["id"],
                        name=row["name"],
                        type=row["type"],
                        description=row["description"],
                        file_path=row["file_path"],
                        node_count=row["node_count"],
                        status=row["status"],
                        tags=json.loads(row["tags"]) if row["tags"] else [],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        last_synced=(
                            datetime.fromisoformat(row["last_synced"])
                            if row["last_synced"]
                            else None
                        ),
                        n8n_version_id=row["n8n_version_id"],
                    )
                )

        return workflows

    def update_workflow(self, workflow: Workflow) -> bool:
        """Update an existing workflow"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE workflows SET
                    name = ?, type = ?, description = ?, file_path = ?, node_count = ?,
                    status = ?, tags = ?, last_synced = ?, n8n_version_id = ?
                WHERE id = ?
            """,
                (
                    workflow.name,
                    workflow.type,
                    workflow.description,
                    workflow.file_path,
                    workflow.node_count,
                    workflow.status,
                    json.dumps(workflow.tags),
                    workflow.last_synced.isoformat() if workflow.last_synced else None,
                    workflow.n8n_version_id,
                    workflow.id,
                ),
            )
            conn.commit()

            updated = cursor.rowcount > 0
            if updated:
                print(f"✅ Updated workflow: {workflow.name} ({workflow.id})")

            return updated

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow (soft delete by changing status to archived)"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE workflows SET status = 'archived' WHERE id = ?", (workflow_id,)
            )
            conn.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                print(f"✅ Archived workflow: {workflow_id}")

            return deleted

    def search_workflows(self, query: str) -> List[Workflow]:
        """Full-text search workflows"""
        workflows = []
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT w.* FROM workflows w
                JOIN workflows_fts fts ON w.rowid = fts.rowid
                WHERE workflows_fts MATCH ?
                ORDER BY rank
            """,
                (query,),
            )

            for row in cursor.fetchall():
                workflows.append(
                    Workflow(
                        id=row["id"],
                        name=row["name"],
                        type=row["type"],
                        description=row["description"],
                        file_path=row["file_path"],
                        node_count=row["node_count"],
                        status=row["status"],
                        tags=json.loads(row["tags"]) if row["tags"] else [],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                        last_synced=(
                            datetime.fromisoformat(row["last_synced"])
                            if row["last_synced"]
                            else None
                        ),
                        n8n_version_id=row["n8n_version_id"],
                    )
                )

        return workflows

    # Workflow Mapping CRUD Operations
    def add_workflow_mapping(
        self, workflow_id: str, file_path: str, name: str, workflow_type: str = "main"
    ) -> str:
        """Add a new workflow mapping to the database"""
        workflow = Workflow(
            id=workflow_id,
            name=name,
            type=WorkflowType(workflow_type),
            file_path=file_path,
            status=WorkflowStatus.ACTIVE,
            description=None,
            last_synced=None,
            n8n_version_id=None,
        )
        return self.create_workflow(workflow)

    def get_workflow_mapping(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow mapping by ID"""
        workflow = self.get_workflow(workflow_id)
        if workflow:
            return {
                "file": workflow.file_path,
                "name": workflow.name,
                "type": workflow.type,
            }
        return None

    def get_all_workflow_mappings(self) -> Dict[str, Any]:
        """Get all workflow mappings in the format used by workflow-mappings.json"""
        workflows = self.list_workflows()
        mappings: Dict[str, Any] = {"workflows": {}}

        for workflow in workflows:
            if workflow.status == "active":  # Only include active workflows
                mappings["workflows"][workflow.id] = {
                    "file": workflow.file_path,
                    "name": workflow.name,
                    "type": workflow.type,
                }

        # Set default workflow if any exists
        if mappings["workflows"]:
            mappings["default"] = list(mappings["workflows"].keys())[0]

        return mappings

    def update_workflow_mapping(
        self,
        workflow_id: str,
        file_path: Optional[str] = None,
        name: Optional[str] = None,
        workflow_type: Optional[str] = None,
    ) -> bool:
        """Update an existing workflow mapping"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False

        if file_path:
            workflow.file_path = file_path
        if name:
            workflow.name = name
        if workflow_type:
            workflow.type = WorkflowType(workflow_type)

        return self.update_workflow(workflow)

    def remove_workflow_mapping(self, workflow_id: str) -> bool:
        """Remove a workflow mapping (archive it)"""
        return self.delete_workflow(workflow_id)

    def get_database_stats(self) -> DatabaseStats:
        """Get database statistics"""
        table_counts: Dict[str, int] = {}
        tables = ["workflows", "configurations"]

        with self.get_connection() as conn:
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                table_counts[table] = cursor.fetchone()["count"]

        return DatabaseStats(
            database_path=str(self.db_path),
            database_size=self.db_path.stat().st_size if self.db_path.exists() else 0,
            schema_version=self.SCHEMA_VERSION,
            tables=table_counts,
            last_updated=datetime.utcnow(),
        )

    def vacuum(self) -> None:
        """Optimize database storage"""
        print("🎭 Optimizing database...")
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            conn.commit()
        print("✅ Database optimization complete")

    def compact(self) -> None:
        """Compact database to reclaim space and optimize performance (alias for vacuum)"""
        return self.vacuum()

    def backup(self, backup_path: Union[str, Path]) -> None:
        """Create database backup"""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        with self.get_connection() as conn:
            backup_conn = sqlite3.connect(str(backup_path))
            conn.backup(backup_conn)
            backup_conn.close()

        print(f"🎭 Backup created: {backup_path}")

    def create_backup_record(self, backup_metadata: Dict[str, Any]) -> bool:
        """Store backup metadata in the configurations table"""

        # First, ensure we have a 'global' workflow record for backup metadata
        with self.get_connection() as conn:
            # Check if global workflow exists
            cursor = conn.execute("SELECT id FROM workflows WHERE id = 'global'")
            if not cursor.fetchone():
                # Create global workflow record for system-wide operations
                conn.execute(
                    """\
                    INSERT INTO workflows (
                        id, name, type, description, file_path, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        "global",
                        "System Global Operations",
                        "utility",
                        "Virtual workflow for system-wide operations like backups",
                        "system://global",
                        "active",
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat(),
                    ),
                )

            # Now insert backup metadata
            conn.execute(
                """\
                INSERT INTO configurations (
                    workflow_id, config_type, config_data, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    "global",
                    "backup_metadata",
                    json.dumps(backup_metadata),
                    datetime.utcnow().isoformat(),
                    1,
                ),
            )
            conn.commit()

        print(
            f"✅ Backup metadata stored: {backup_metadata.get('backup_id', 'unknown')}"
        )
        return True

    def get_backup_history(self) -> List[Dict[str, Any]]:
        """Get all backup records from database"""
        backups = []
        with self.get_connection() as conn:
            cursor = conn.execute(
                """\
                SELECT config_data, created_at FROM configurations
                WHERE config_type = 'backup_metadata'
                ORDER BY created_at DESC
            """
            )

            for row in cursor.fetchall():
                try:
                    backup_data = json.loads(row["config_data"])
                    backup_data["stored_at"] = row["created_at"]
                    backup_data["in_database"] = True
                    backups.append(backup_data)
                except json.JSONDecodeError:
                    continue

        return backups

    def get_backup_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get backup record by filename"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """\
                SELECT config_data FROM configurations
                WHERE config_type = 'backup_metadata'
                AND json_extract(config_data, '$.filename') = ?
            """,
                (filename,),
            )

            row = cursor.fetchone()
            if row:
                try:
                    result = json.loads(row["config_data"])
                    return result if isinstance(result, dict) else None
                except json.JSONDecodeError:
                    return None

        return None

    def get_backup_by_hash(self, sha256_hash: str) -> Optional[Dict[str, Any]]:
        """Get backup record by SHA256 hash"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """\
                SELECT config_data FROM configurations
                WHERE config_type = 'backup_metadata'
                AND json_extract(config_data, '$.sha256_hash') = ?
            """,
                (sha256_hash,),
            )

            row = cursor.fetchone()
            if row:
                try:
                    result = json.loads(row["config_data"])
                    return result if isinstance(result, dict) else None
                except json.JSONDecodeError:
                    return None

        return None


def cli_main() -> None:
    """CLI entry point for n8n_deploy_ operations"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: n8n-deploy <command> [args]")
        print("Commands: init, stats, vacuum, backup")
        return

    command = sys.argv[1]
    db = n8n_deploy_DB()

    if command == "init":
        if not os.getenv("N8N_DEPLOY_TESTING"):
            print("✅ Database initialized")
    elif command == "stats":
        stats = db.get_database_stats()
        print(json.dumps(stats.dict(), indent=2, default=str))
    elif command == "vacuum":
        db.vacuum()
    elif command == "backup":
        if len(sys.argv) < 3:
            # Create backup in the proper backups directory with timestamp
            backup_filename = (
                f"n8n_deploy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            try:
                # Try to get configuration for proper backup path
                from api.config import get_config

                config = get_config()
                # Ensure backups directory exists
                config.backups_path.mkdir(parents=True, exist_ok=True)
                backup_path = str(config.backups_path / backup_filename)
            except Exception:
                # Fallback to current directory if config fails
                backup_path = backup_filename
        else:
            backup_path = sys.argv[2]
        db.backup(backup_path)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    cli_main()
