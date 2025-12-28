#!/usr/bin/env python3
"""
Database schema management for n8n-deploy

Handles database initialization and schema versioning.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from ..config import AppConfig
from .base import BaseDB


class SchemaApi(BaseDB):
    """Manages database schema initialization and versioning"""

    SCHEMA_VERSION = 8

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize schema manager with database path"""
        super().__init__(config=config, db_path=db_path)
        self._connection: Optional[sqlite3.Connection] = None

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
                    file TEXT,
                    file_folder TEXT,
                    server_id INTEGER,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_synced TIMESTAMP,
                    last_used TIMESTAMP,
                    n8n_version_id TEXT,
                    push_count INTEGER DEFAULT 0,
                    pull_count INTEGER DEFAULT 0,
                    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE SET NULL
                )
            """
            )

            # Create servers table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    skip_ssl_verify BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
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
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create server_api_keys junction table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS server_api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER NOT NULL,
                    api_key_id INTEGER NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE CASCADE,
                    FOREIGN KEY (api_key_id) REFERENCES api_keys (id) ON DELETE CASCADE,
                    UNIQUE (server_id, api_key_id)
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

            # Create dependencies table for workflow dependencies
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'wf',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE,
                    FOREIGN KEY (depends_on) REFERENCES workflows (id) ON DELETE CASCADE
                )
            """
            )

            # Create n8n_folders table for caching remote folder structure
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS n8n_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    n8n_folder_id TEXT NOT NULL,
                    n8n_project_id TEXT NOT NULL,
                    folder_path TEXT NOT NULL,
                    server_id INTEGER NOT NULL,
                    last_synced TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
                    UNIQUE (n8n_folder_id, server_id)
                )
            """
            )

            # Create folder_mappings table for local-to-remote mappings
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS folder_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    local_path TEXT NOT NULL,
                    n8n_folder_id INTEGER NOT NULL,
                    sync_direction TEXT DEFAULT 'bidirectional',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (n8n_folder_id) REFERENCES n8n_folders(id) ON DELETE CASCADE,
                    UNIQUE (local_path, n8n_folder_id)
                )
            """
            )

            # Create server_credentials table for internal API auth
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS server_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER NOT NULL UNIQUE,
                    email TEXT NOT NULL,
                    session_cookie TEXT,
                    cookie_expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
                )
            """
            )

            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows (name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_servers_name ON servers (name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_servers_url ON servers (url)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_name ON api_keys (name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server_api_keys_server ON server_api_keys (server_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server_api_keys_key ON server_api_keys (api_key_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dependencies_workflow_id ON dependencies (workflow_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_n8n_folders_server ON n8n_folders (server_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_n8n_folders_path ON n8n_folders (folder_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_folder_mappings_local ON folder_mappings (local_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_server_credentials_server ON server_credentials (server_id)")

            # Record schema version
            conn.execute(
                """
                INSERT OR REPLACE INTO schema_info (version, applied_at, description)
                VALUES (?, ?, ?)
            """,
                (self.SCHEMA_VERSION, datetime.now(), "Server SSL verification setting"),
            )

            conn.commit()

    def migrate_database(self) -> None:
        """Apply migrations for existing databases"""
        current_version = self.get_schema_version()

        with self.get_connection() as conn:
            # Migration from version 3 to 4: Add is_primary column
            if current_version < 4:
                try:
                    conn.execute("ALTER TABLE server_api_keys ADD COLUMN is_primary BOOLEAN DEFAULT FALSE")
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO schema_info (version, applied_at, description)
                        VALUES (?, ?, ?)
                        """,
                        (4, datetime.now(), "Primary API key selection"),
                    )
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column already exists
                    pass

            # Migration from version 4 to 5: Add file column to workflows
            if current_version < 5:
                try:
                    conn.execute("ALTER TABLE workflows ADD COLUMN file TEXT")
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO schema_info (version, applied_at, description)
                        VALUES (?, ?, ?)
                        """,
                        (5, datetime.now(), "Custom workflow filenames"),
                    )
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column already exists
                    pass

            # Migration from version 5 to 6: Add folder sync tables
            if current_version < 6:
                # Create n8n_folders table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS n8n_folders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        n8n_folder_id TEXT NOT NULL,
                        n8n_project_id TEXT NOT NULL,
                        folder_path TEXT NOT NULL,
                        server_id INTEGER NOT NULL,
                        last_synced TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
                        UNIQUE (n8n_folder_id, server_id)
                    )
                """
                )

                # Create folder_mappings table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS folder_mappings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        local_path TEXT NOT NULL,
                        n8n_folder_id INTEGER NOT NULL,
                        sync_direction TEXT DEFAULT 'bidirectional',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (n8n_folder_id) REFERENCES n8n_folders(id) ON DELETE CASCADE,
                        UNIQUE (local_path, n8n_folder_id)
                    )
                """
                )

                # Create server_credentials table
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS server_credentials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_id INTEGER NOT NULL UNIQUE,
                        email TEXT NOT NULL,
                        session_cookie TEXT,
                        cookie_expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
                    )
                """
                )

                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_n8n_folders_server ON n8n_folders (server_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_n8n_folders_path ON n8n_folders (folder_path)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_folder_mappings_local ON folder_mappings (local_path)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_server_credentials_server ON server_credentials (server_id)")

                conn.execute(
                    """
                    INSERT OR REPLACE INTO schema_info (version, applied_at, description)
                    VALUES (?, ?, ?)
                    """,
                    (6, datetime.now(), "Folder sync support"),
                )
                conn.commit()

            # Migration from version 6 to 7: Reserved (scripts_path removed)
            if current_version < 7:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO schema_info (version, applied_at, description)
                    VALUES (?, ?, ?)
                    """,
                    (7, datetime.now(), "Reserved"),
                )
                conn.commit()

            # Migration from version 7 to 8: Add skip_ssl_verify to servers
            if current_version < 8:
                try:
                    conn.execute("ALTER TABLE servers ADD COLUMN skip_ssl_verify BOOLEAN DEFAULT FALSE")
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO schema_info (version, applied_at, description)
                        VALUES (?, ?, ?)
                        """,
                        (8, datetime.now(), "Server SSL verification setting"),
                    )
                    conn.commit()
                except sqlite3.OperationalError:
                    # Column already exists
                    pass

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
