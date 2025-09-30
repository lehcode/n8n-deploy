#!/usr/bin/env python3
"""
Backup-related database operations for n8n-deploy

Handles backup metadata storage, retrieval, and management.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Iterator
from contextlib import contextmanager

from ..config import AppConfig
from .schema import SchemaApi


class BackupApi:
    """Manages backup-related database operations"""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize backup"""
        self.schema = SchemaApi(config=config, db_path=db_path)
        self.db_path = self.schema.db_path

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context for database connections"""
        with self.schema.get_connection() as conn:
            yield conn

    def create_backup_record(self, backup_metadata: Dict[str, Any]) -> bool:
        """Create a record of a backup operation"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO configurations (
                        name, backup_path, checksum, created_at, is_active
                    ) VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        backup_metadata.get("name", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                        backup_metadata.get("backup_path", ""),
                        backup_metadata.get("checksum", ""),
                        datetime.now(),
                        True,
                    ),
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def get_backup_history(self) -> List[Dict[str, Any]]:
        """Get history of all backup operations"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM configurations
                ORDER BY created_at DESC
            """
            )

            backups = []
            for row in cursor.fetchall():
                backup_info = {
                    "id": row["id"],
                    "name": row["name"],
                    "backup_path": row["backup_path"],
                    "checksum": row["checksum"],
                    "created_at": row["created_at"],
                    "is_active": bool(row["is_active"]),
                }
                backups.append(backup_info)

            return backups

    def get_backup_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get backup record by filename"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM configurations
                WHERE backup_path LIKE ?
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (f"%{filename}%",),
            )

            row = cursor.fetchone()
            if row is None:
                return None

            return {
                "id": row["id"],
                "name": row["name"],
                "backup_path": row["backup_path"],
                "checksum": row["checksum"],
                "created_at": row["created_at"],
                "is_active": bool(row["is_active"]),
            }

    def update_backup_status(self, backup_id: int, is_active: bool) -> bool:
        """Update backup status"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE configurations SET is_active = ? WHERE id = ?
            """,
                (is_active, backup_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_backup_record(self, backup_id: int) -> bool:
        """Delete backup record from database"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM configurations WHERE id = ?
            """,
                (backup_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Clean up old backup records, keeping only the most recent ones"""
        with self.get_connection() as conn:
            # Get backup IDs to delete (keeping the most recent keep_count)
            cursor = conn.execute(
                """
                SELECT id FROM configurations
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
            """,
                (keep_count,),
            )

            ids_to_delete = [row["id"] for row in cursor.fetchall()]

            if not ids_to_delete:
                return 0

            # Delete old backup records
            placeholders = ",".join("?" * len(ids_to_delete))
            cursor = conn.execute(
                f"""
                DELETE FROM configurations WHERE id IN ({placeholders})
            """,
                ids_to_delete,
            )

            conn.commit()
            return cursor.rowcount
