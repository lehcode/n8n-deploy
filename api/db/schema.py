#!/usr/bin/env python3
"""
Database schema management for n8n-deploy

Handles database initialization, schema versioning, and migrations.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Union

from ..config import AppConfig


class SchemaApi:
    """Manages database schema initialization and migrations"""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize schema manager with database path"""
        # Database path resolution: config > direct path > default
        if config is not None:
            self.db_path = config.database_path
        elif db_path is not None:
            self.db_path = Path(db_path)
        else:
            from ..config import get_config

            default_config = get_config()
            self.db_path = default_config.database_path

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def initialize_database(self) -> None:
        """Initialize database with schema and tables"""
        with self.get_connection() as conn:
            # Create schema_info table first
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_info (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """
            )

            # Create workflows table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    file_folder TEXT,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_synced TIMESTAMP,
                    n8n_version_id TEXT,
                    push_count INTEGER DEFAULT 0,
                    pull_count INTEGER DEFAULT 0
                )
            """
            )

            # Create api_keys table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    api_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    description TEXT
                )
            """
            )

            # Create configurations table for backup metadata
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    backup_path TEXT NOT NULL,
                    checksum TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """
            )

            # Create versions table for workflow versioning
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    changes_summary TEXT,
                    changes_detail TEXT,
                    file_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
                )
            """
            )

            # Create dependencies table for workflow dependencies
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'workflow',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE,
                    FOREIGN KEY (depends_on) REFERENCES workflows (id) ON DELETE CASCADE
                )
            """
            )

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows (name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_name ON api_keys (name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_versions_workflow_id ON versions (workflow_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dependencies_workflow_id ON dependencies (workflow_id)")

            # Record schema version
            conn.execute(
                """
                INSERT OR REPLACE INTO schema_info (version, applied_at, description)
                VALUES (?, ?, ?)
            """,
                (self.SCHEMA_VERSION, datetime.now(), "Initial database schema"),
            )

            conn.commit()

    def get_schema_version(self) -> int:
        """Get current database schema version"""
        with self.get_connection() as conn:
            try:
                cursor = conn.execute("SELECT MAX(version) FROM schema_info")
                result = cursor.fetchone()
                return int(result[0]) if result and result[0] is not None else 0
            except sqlite3.OperationalError:
                # Table doesn't exist yet
                return 0

    def needs_migration(self) -> bool:
        """Check if database needs migration"""
        current_version = self.get_schema_version()
        return current_version < self.SCHEMA_VERSION

    def migrate_database(self) -> None:
        """Migrate database to current schema version"""
        current_version = self.get_schema_version()

        if current_version < self.SCHEMA_VERSION:
            # For now, just reinitialize if migration needed
            # In future versions, add specific migration logic
            self.initialize_database()
