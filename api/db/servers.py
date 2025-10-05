#!/usr/bin/env python3
"""
Server management operations for n8n-deploy

Handles CRUD operations for n8n servers and their API key associations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..config import AppConfig
from .base import BaseDB


class ServerCrud(BaseDB):
    """Manages server CRUD operations and API key associations"""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize server CRUD with database connection"""
        super().__init__(config=config, db_path=db_path)

    def add_server(
        self,
        url: str,
        name: str,
        description: Optional[str] = None,
        is_active: bool = True,
    ) -> int:
        """
        Add a new n8n server

        Args:
            url: Server URL (e.g., http://n8n.example.com:5678)
            name: Unique server name
            description: Optional server description
            is_active: Server active status (default: True)

        Returns:
            int: Server ID

        Raises:
            sqlite3.IntegrityError: If server name already exists
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO servers (url, name, description, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (url, name, description, is_active, datetime.now()),
            )
            conn.commit()
            return int(cursor.lastrowid) if cursor.lastrowid else 0

    def get_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get server by name

        Args:
            name: Server name

        Returns:
            Server record as dict or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, url, name, description, is_active, created_at, last_used
                FROM servers
                WHERE name = ?
                """,
                (name,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "url": row[1],
                    "name": row[2],
                    "description": row[3],
                    "is_active": bool(row[4]),
                    "created_at": row[5],
                    "last_used": row[6],
                }
            return None

    def get_server_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get first active server matching URL

        Args:
            url: Server URL

        Returns:
            Server record as dict or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, url, name, description, is_active, created_at, last_used
                FROM servers
                WHERE url = ? AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (url,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "url": row[1],
                    "name": row[2],
                    "description": row[3],
                    "is_active": bool(row[4]),
                    "created_at": row[5],
                    "last_used": row[6],
                }
            return None

    def list_servers(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all servers

        Args:
            active_only: Only return active servers (default: False)

        Returns:
            List of server records as dicts
        """
        with self.get_connection() as conn:
            query = """
                SELECT id, url, name, description, is_active, created_at, last_used
                FROM servers
            """
            if active_only:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY created_at DESC"

            cursor = conn.execute(query)
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "url": row[1],
                    "name": row[2],
                    "description": row[3],
                    "is_active": bool(row[4]),
                    "created_at": row[5],
                    "last_used": row[6],
                }
                for row in rows
            ]

    def update_server(
        self,
        name: str,
        url: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """
        Update server details

        Args:
            name: Server name (identifier)
            url: New server URL (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            True if server was updated, False if not found
        """
        server = self.get_server_by_name(name)
        if not server:
            return False

        updates: List[str] = []
        params: List[Any] = []

        if url is not None:
            updates.append("url = ?")
            params.append(url)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            return True  # Nothing to update

        params.append(name)
        query = f"UPDATE servers SET {', '.join(updates)} WHERE name = ?"

        with self.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()
            return True

    def delete_server(self, name: str) -> bool:
        """
        Delete server and its API key associations

        Args:
            name: Server name

        Returns:
            True if server was deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM servers WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0

    def link_api_key(self, server_name: str, api_key_name: str) -> bool:
        """
        Link an API key to a server

        Args:
            server_name: Server name
            api_key_name: API key name

        Returns:
            True if link was created

        Raises:
            ValueError: If server or API key not found
            sqlite3.IntegrityError: If link already exists
        """
        server = self.get_server_by_name(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found")

        with self.get_connection() as conn:
            # Get API key ID
            cursor = conn.execute("SELECT id FROM api_keys WHERE name = ?", (api_key_name,))
            key_row = cursor.fetchone()
            if not key_row:
                raise ValueError(f"API key '{api_key_name}' not found")

            api_key_id = key_row[0]

            # Create link
            conn.execute(
                """
                INSERT INTO server_api_keys (server_id, api_key_id, created_at)
                VALUES (?, ?, ?)
                """,
                (server["id"], api_key_id, datetime.now()),
            )
            conn.commit()
            return True

    def unlink_api_key(self, server_name: str, api_key_name: str) -> bool:
        """
        Unlink an API key from a server

        Args:
            server_name: Server name
            api_key_name: API key name

        Returns:
            True if link was removed, False if not found
        """
        server = self.get_server_by_name(server_name)
        if not server:
            return False

        with self.get_connection() as conn:
            # Get API key ID
            cursor = conn.execute("SELECT id FROM api_keys WHERE name = ?", (api_key_name,))
            key_row = cursor.fetchone()
            if not key_row:
                return False

            api_key_id = key_row[0]

            # Remove link
            cursor = conn.execute(
                "DELETE FROM server_api_keys WHERE server_id = ? AND api_key_id = ?",
                (server["id"], api_key_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_server_api_keys(self, server_name: str) -> List[Dict[str, Any]]:
        """
        Get all API keys linked to a server

        Args:
            server_name: Server name

        Returns:
            List of API key records
        """
        server = self.get_server_by_name(server_name)
        if not server:
            return []

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT k.id, k.name, k.description, k.created_at, sk.created_at as linked_at
                FROM api_keys k
                JOIN server_api_keys sk ON k.id = sk.api_key_id
                WHERE sk.server_id = ?
                ORDER BY sk.created_at DESC
                """,
                (server["id"],),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3],
                    "linked_at": row[4],
                }
                for row in rows
            ]

    def get_api_key_for_server(self, server_name: str) -> Optional[str]:
        """
        Get the API key value for a server (most recently linked)

        Args:
            server_name: Server name

        Returns:
            API key value or None if no key linked
        """
        server = self.get_server_by_name(server_name)
        if not server:
            return None

        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT k.api_key
                FROM api_keys k
                JOIN server_api_keys sk ON k.id = sk.api_key_id
                WHERE sk.server_id = ?
                ORDER BY sk.created_at DESC
                LIMIT 1
                """,
                (server["id"],),
            )
            row = cursor.fetchone()
            if row:
                # Update last_used timestamp for the server
                conn.execute(
                    "UPDATE servers SET last_used = ? WHERE id = ?",
                    (datetime.now(), server["id"]),
                )
                conn.commit()
                return str(row[0]) if row[0] else None
            return None
