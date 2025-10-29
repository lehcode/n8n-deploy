#!/usr/bin/env python3
"""
API Keys database CRUD operations

Handles all database operations for API key management including
creation, retrieval, listing, deactivation, and deletion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..config import AppConfig
from .base import BaseDB


class ApiKeyCrud(BaseDB):
    """Database CRUD operations for API keys"""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize API key CRUD operations"""
        super().__init__(config=config, db_path=db_path)

    def add_api_key(
        self,
        name: str,
        api_key: str,
        description: Optional[str] = None,
    ) -> int:
        """Add a new API key to storage

        Args:
            name: Unique name for the API key
            api_key: The actual API key value
            description: Optional description

        Returns:
            The ID of the newly created API key

        Raises:
            RuntimeError: If key creation fails
            sqlite3.IntegrityError: If key name already exists
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO api_keys (name, api_key, description, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    name,
                    api_key,
                    description,
                    True,
                    datetime.now(),
                ),
            )
            conn.commit()
            key_id = cursor.lastrowid

        if key_id is None:
            raise RuntimeError("Failed to create API key: lastrowid is None")

        return key_id

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Retrieve API key value by name

        Args:
            key_name: Name of the API key to retrieve

        Returns:
            The API key value if found and active, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, api_key
                FROM api_keys
                WHERE name = ? AND is_active = 1
                ORDER BY created_at DESC LIMIT 1
            """,
                (key_name,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            key_id, plain_key = row

            # Return key
            return str(plain_key) if plain_key is not None else None

    def list_api_keys(self, unmask: bool = False) -> List[Dict[str, Any]]:
        """List all stored API keys metadata

        Args:
            unmask: If True, include actual API key values (security warning!)

        Returns:
            List of dictionaries containing API key metadata with linked server names
        """
        with self.get_connection() as conn:
            if unmask:
                cursor = conn.execute(
                    """
                    SELECT
                        ak.id,
                        ak.name,
                        ak.created_at,
                        ak.description,
                        ak.is_active,
                        ak.api_key,
                        s.url as server_url
                    FROM api_keys ak
                    LEFT JOIN server_api_keys sak ON ak.id = sak.api_key_id
                    LEFT JOIN servers s ON sak.server_id = s.id
                    ORDER BY ak.created_at DESC
                """
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT
                        ak.id,
                        ak.name,
                        ak.created_at,
                        ak.description,
                        ak.is_active,
                        s.url as server_url
                    FROM api_keys ak
                    LEFT JOIN server_api_keys sak ON ak.id = sak.api_key_id
                    LEFT JOIN servers s ON sak.server_id = s.id
                    ORDER BY ak.created_at DESC
                """
                )

            keys = []
            for row in cursor.fetchall():
                key_data = {
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "description": row[3],
                    "is_active": bool(row[4]),
                }
                if unmask:
                    key_data["api_key"] = row[5]
                    key_data["server_url"] = row[6] if row[6] else None
                else:
                    key_data["server_url"] = row[5] if row[5] else None
                keys.append(key_data)

            return keys

    def activate_api_key(self, key_name: str) -> bool:
        """Activate an API key (restore from soft delete)

        Args:
            key_name: Name of the API key to activate

        Returns:
            True if activation succeeded, False if key not found or already active
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE api_keys SET is_active = 1
                WHERE name = ? AND is_active = 0
            """,
                (key_name,),
            )
            conn.commit()

            return cursor.rowcount > 0

    def deactivate_api_key(self, key_name: str) -> bool:
        """Deactivate an API key (soft delete)

        Args:
            key_name: Name of the API key to deactivate

        Returns:
            True if deactivation succeeded, False if key not found or already inactive
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE api_keys SET is_active = 0
                WHERE name = ? AND is_active = 1
            """,
                (key_name,),
            )
            conn.commit()

            return cursor.rowcount > 0

    def delete_api_key(self, key_name: str) -> bool:
        """Permanently delete an API key from database

        Args:
            key_name: Name of the API key to delete

        Returns:
            True if deletion succeeded, False if key not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM api_keys WHERE name = ?
            """,
                (key_name,),
            )
            conn.commit()

            return cursor.rowcount > 0

    def api_key_exists(self, key_name: str) -> bool:
        """Check if an API key exists by name

        Args:
            key_name: Name of the API key to check

        Returns:
            True if the API key exists (active or inactive), False otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM api_keys WHERE name = ?
            """,
                (key_name,),
            )
            result = cursor.fetchone()
            count: int = int(result[0]) if result else 0
            return count > 0
