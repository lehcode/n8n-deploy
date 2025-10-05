#!/usr/bin/env python3
"""
API Key Management for n8n_deploy_
Storage and management of API keys for n8n and external services
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .config import AppConfig
from .db import DBApi


@dataclass
class ApiKey:
    """API Key data model"""

    id: int
    name: str
    plain_key: str  # API key
    created_at: datetime
    is_active: bool = True
    description: Optional[str] = None


class KeyApi:
    """API key storage and management"""

    def __init__(self, db: DBApi, config: Optional[AppConfig] = None) -> None:
        self.config = config
        self.db = db

    def add_api_key(
        self,
        name: str,
        api_key: str,
        description: Optional[str] = None,
        expires_days: Optional[int] = None,  # Kept for backwards compatibility, but ignored
    ) -> int:
        """Add a new API key to storage"""
        with self.db.get_connection() as conn:
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

    def get_api_key(self, key_name: str, update_last_used: bool = True) -> Optional[str]:
        """Retrieve API key by name"""
        with self.db.get_connection() as conn:
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

    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List all stored API keys metadata"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, name, created_at, description, is_active
                FROM api_keys
                ORDER BY created_at DESC
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
                keys.append(key_data)

            return keys

    def deactivate_api_key(self, key_name: str) -> bool:
        """Deactivate an API key (soft delete)"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE api_keys SET is_active = 0
                WHERE name = ? AND is_active = 1
            """,
                (key_name,),
            )
            conn.commit()

            if cursor.rowcount > 0:
                print(f"✅ API key deactivated: {key_name}")
                return True
            else:
                print(f"❌ API key not found or already inactive: {key_name}")
                return False

    def delete_api_key(self, key_name: str, confirm: bool = False) -> bool:
        """Permanently delete an API key"""

        if not confirm:
            print("⚠️  Use --confirm flag to permanently delete API key")
            return False

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM api_keys WHERE name = ?
            """,
                (key_name,),
            )
            conn.commit()

            if cursor.rowcount > 0:
                print(f"✅ API key permanently deleted: {key_name}")
                return True
            else:
                print(f"❌ API key not found: {key_name}")
                return False

    def test_api_key(self, key_name: str) -> bool:
        """Test if an API key is valid and accessible"""

        api_key = self.get_api_key(key_name, update_last_used=False)
        if not api_key:
            print(f"❌ API key not found: {key_name}")
            return False

        # Basic validation - key exists and is accessible
        print("✅ API key is accessible")
        print(f"   Key length: {len(api_key)} characters")
        print(f"   Key prefix: {api_key[:8]}..." if len(api_key) > 8 else f"   Key: {api_key}")

        # TODO: Add service-specific validation (e.g., test n8n connection)
        return True
