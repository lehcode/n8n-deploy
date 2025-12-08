#!/usr/bin/env python3
"""
Database CRUD operations for folder sync functionality

Handles n8n_folders, folder_mappings, and server_credentials tables.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from ..config import AppConfig
from ..models import FolderMapping, N8nFolder, ServerCredentials, SyncDirection
from .base import BaseDB


class FolderDB(BaseDB):
    """CRUD operations for folder sync tables"""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize folder database manager"""
        super().__init__(config=config, db_path=db_path)

    # ==================== N8N FOLDERS ====================

    def add_n8n_folder(self, folder: N8nFolder) -> int:
        """
        Add a new n8n folder to the database

        Args:
            folder: N8nFolder model instance

        Returns:
            ID of the inserted folder

        Raises:
            sqlite3.IntegrityError: If folder already exists for this server
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO n8n_folders (n8n_folder_id, n8n_project_id, folder_path, server_id, last_synced)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    folder.n8n_folder_id,
                    folder.n8n_project_id,
                    folder.folder_path,
                    folder.server_id,
                    folder.last_synced,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_n8n_folder(self, folder_id: int) -> Optional[N8nFolder]:
        """Get n8n folder by local database ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM n8n_folders WHERE id = ?",
                (folder_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_n8n_folder(row)
            return None

    def get_n8n_folder_by_path(self, folder_path: str, server_id: int) -> Optional[N8nFolder]:
        """Get n8n folder by path and server"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM n8n_folders WHERE folder_path = ? AND server_id = ?",
                (folder_path, server_id),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_n8n_folder(row)
            return None

    def get_n8n_folder_by_remote_id(self, n8n_folder_id: str, server_id: int) -> Optional[N8nFolder]:
        """Get n8n folder by remote n8n UUID and server"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM n8n_folders WHERE n8n_folder_id = ? AND server_id = ?",
                (n8n_folder_id, server_id),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_n8n_folder(row)
            return None

    def list_n8n_folders(self, server_id: Optional[int] = None) -> List[N8nFolder]:
        """List all n8n folders, optionally filtered by server"""
        with self.get_connection() as conn:
            if server_id:
                cursor = conn.execute(
                    "SELECT * FROM n8n_folders WHERE server_id = ? ORDER BY folder_path",
                    (server_id,),
                )
            else:
                cursor = conn.execute("SELECT * FROM n8n_folders ORDER BY server_id, folder_path")
            return [self._row_to_n8n_folder(row) for row in cursor.fetchall()]

    def update_n8n_folder_sync_time(self, folder_id: int) -> None:
        """Update the last_synced timestamp for a folder"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE n8n_folders SET last_synced = ? WHERE id = ?",
                (datetime.now(timezone.utc), folder_id),
            )
            conn.commit()

    def delete_n8n_folder(self, folder_id: int) -> bool:
        """Delete an n8n folder by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM n8n_folders WHERE id = ?",
                (folder_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def upsert_n8n_folder(self, folder: N8nFolder) -> int:
        """Insert or update n8n folder based on remote ID and server"""
        existing = self.get_n8n_folder_by_remote_id(folder.n8n_folder_id, folder.server_id)
        if existing:
            with self.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE n8n_folders
                    SET folder_path = ?, n8n_project_id = ?, last_synced = ?
                    WHERE id = ?
                    """,
                    (
                        folder.folder_path,
                        folder.n8n_project_id,
                        datetime.now(timezone.utc),
                        existing.id,
                    ),
                )
                conn.commit()
            return existing.id or 0
        return self.add_n8n_folder(folder)

    def _row_to_n8n_folder(self, row: sqlite3.Row) -> N8nFolder:
        """Convert database row to N8nFolder model"""
        return N8nFolder(
            id=row["id"],
            n8n_folder_id=row["n8n_folder_id"],
            n8n_project_id=row["n8n_project_id"],
            folder_path=row["folder_path"],
            server_id=row["server_id"],
            last_synced=row["last_synced"],
            created_at=row["created_at"],
        )

    # ==================== FOLDER MAPPINGS ====================

    def add_folder_mapping(self, mapping: FolderMapping) -> int:
        """
        Add a new folder mapping

        Args:
            mapping: FolderMapping model instance

        Returns:
            ID of the inserted mapping
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO folder_mappings (local_path, n8n_folder_id, sync_direction)
                VALUES (?, ?, ?)
                """,
                (
                    mapping.local_path,
                    mapping.n8n_folder_id,
                    mapping.sync_direction,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_folder_mapping(self, mapping_id: int) -> Optional[FolderMapping]:
        """Get folder mapping by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM folder_mappings WHERE id = ?",
                (mapping_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_folder_mapping(row)
            return None

    def get_folder_mapping_by_local_path(self, local_path: str) -> Optional[FolderMapping]:
        """Get folder mapping by local path"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM folder_mappings WHERE local_path = ?",
                (local_path,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_folder_mapping(row)
            return None

    def list_folder_mappings(self, n8n_folder_id: Optional[int] = None) -> List[FolderMapping]:
        """List all folder mappings, optionally filtered by n8n folder"""
        with self.get_connection() as conn:
            if n8n_folder_id:
                cursor = conn.execute(
                    "SELECT * FROM folder_mappings WHERE n8n_folder_id = ?",
                    (n8n_folder_id,),
                )
            else:
                cursor = conn.execute("SELECT * FROM folder_mappings ORDER BY local_path")
            return [self._row_to_folder_mapping(row) for row in cursor.fetchall()]

    def update_folder_mapping(self, mapping_id: int, sync_direction: SyncDirection) -> bool:
        """Update folder mapping sync direction"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE folder_mappings SET sync_direction = ? WHERE id = ?",
                (sync_direction.value, mapping_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_folder_mapping(self, mapping_id: int) -> bool:
        """Delete a folder mapping by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM folder_mappings WHERE id = ?",
                (mapping_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_folder_mapping(self, row: sqlite3.Row) -> FolderMapping:
        """Convert database row to FolderMapping model"""
        return FolderMapping(
            id=row["id"],
            local_path=row["local_path"],
            n8n_folder_id=row["n8n_folder_id"],
            sync_direction=SyncDirection(row["sync_direction"]),
            created_at=row["created_at"],
        )

    # ==================== SERVER CREDENTIALS ====================

    def save_server_credentials(self, credentials: ServerCredentials) -> int:
        """
        Save or update server credentials

        Args:
            credentials: ServerCredentials model instance

        Returns:
            ID of the credentials record
        """
        with self.get_connection() as conn:
            # Check if credentials exist for this server
            cursor = conn.execute(
                "SELECT id FROM server_credentials WHERE server_id = ?",
                (credentials.server_id,),
            )
            existing = cursor.fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE server_credentials
                    SET email = ?, session_cookie = ?, cookie_expires_at = ?, updated_at = ?
                    WHERE server_id = ?
                    """,
                    (
                        credentials.email,
                        credentials.session_cookie,
                        credentials.cookie_expires_at,
                        datetime.now(timezone.utc),
                        credentials.server_id,
                    ),
                )
                conn.commit()
                existing_id: int = existing["id"]
                return existing_id
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO server_credentials
                    (server_id, email, session_cookie, cookie_expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        credentials.server_id,
                        credentials.email,
                        credentials.session_cookie,
                        credentials.cookie_expires_at,
                    ),
                )
                conn.commit()
                return cursor.lastrowid or 0

    def get_server_credentials(self, server_id: int) -> Optional[ServerCredentials]:
        """Get credentials for a server"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM server_credentials WHERE server_id = ?",
                (server_id,),
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_server_credentials(row)
            return None

    def update_session_cookie(
        self,
        server_id: int,
        session_cookie: str,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Update only the session cookie for a server"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE server_credentials
                SET session_cookie = ?, cookie_expires_at = ?, updated_at = ?
                WHERE server_id = ?
                """,
                (
                    session_cookie,
                    expires_at,
                    datetime.now(timezone.utc),
                    server_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_server_credentials(self, server_id: int) -> bool:
        """Delete credentials for a server"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM server_credentials WHERE server_id = ?",
                (server_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_server_credentials(self, row: sqlite3.Row) -> ServerCredentials:
        """Convert database row to ServerCredentials model"""
        return ServerCredentials(
            id=row["id"],
            server_id=row["server_id"],
            email=row["email"],
            session_cookie=row["session_cookie"],
            cookie_expires_at=row["cookie_expires_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
