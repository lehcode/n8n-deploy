#!/usr/bin/env python3
"""
API Key Management for n8n_deploy_
Storage and management of API keys for n8n and external services
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import AppConfig
from .db import DBApi
from .db.apikeys import ApiKeyCrud


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
    """API key storage and management (business logic layer)"""

    def __init__(self, db: DBApi, config: Optional[AppConfig] = None) -> None:
        self.config = config
        self.db = db
        # Use the CRUD layer for database operations
        self.crud = ApiKeyCrud(config=config)

    def add_api_key(
        self,
        name: str,
        api_key: str,
        description: Optional[str] = None,
    ) -> int:
        """Add a new API key to storage"""
        return self.crud.add_api_key(name, api_key, description)

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Retrieve API key by name"""
        return self.crud.get_api_key(key_name)

    def list_api_keys(self, unmask: bool = False) -> List[Dict[str, Any]]:
        """List all stored API keys metadata

        Args:
            unmask: If True, include actual API key values (security warning!)
        """
        return self.crud.list_api_keys(unmask=unmask)

    def deactivate_api_key(self, key_name: str) -> bool:
        """Deactivate an API key (soft delete)"""
        success = self.crud.deactivate_api_key(key_name)

        if success:
            print(f"✅ API key deactivated: {key_name}")
        else:
            print(f"❌ API key not found or already inactive: {key_name}")

        return success

    def delete_api_key(self, key_name: str, confirm: bool = False) -> bool:
        """Permanently delete an API key"""

        if not confirm:
            print("⚠️  Use --confirm flag to permanently delete API key")
            return False

        success = self.crud.delete_api_key(key_name)

        if success:
            print(f"✅ API key permanently deleted: {key_name}")
        else:
            print(f"❌ API key not found: {key_name}")

        return success

    def test_api_key(self, key_name: str) -> bool:
        """Test if an API key is valid and accessible"""

        api_key = self.get_api_key(key_name)
        if not api_key:
            print(f"❌ API key not found: {key_name}")
            return False

        # Basic validation - key exists and is accessible
        print("✅ API key is accessible")
        print(f"   Key length: {len(api_key)} characters")
        print(f"   Key prefix: {api_key[:8]}..." if len(api_key) > 8 else f"   Key: {api_key}")

        # TODO: Add service-specific validation (e.g., test n8n connection)
        return True
