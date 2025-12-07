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

    def activate_api_key(self, key_name: str) -> bool:
        """Activate an API key (restore from soft delete)"""
        success = self.crud.activate_api_key(key_name)

        if success:
            print(f"✅ API key activated: {key_name}")
        else:
            print(f"❌ API key not found or already active: {key_name}")

        return success

    def deactivate_api_key(self, key_name: str) -> bool:
        """Deactivate an API key (soft delete)"""
        success = self.crud.deactivate_api_key(key_name)

        if success:
            print(f"✅ API key deactivated: {key_name}")
        else:
            print(f"❌ API key not found or already inactive: {key_name}")

        return success

    def delete_api_key(self, key_name: str, force: bool = False, no_emoji: bool = False) -> bool:
        """Permanently delete an API key"""

        if not force:
            if no_emoji:
                print("Use --force flag to permanently delete API key")
            else:
                print("⚠️  Use --force flag to permanently delete API key")
            return False

        success = self.crud.delete_api_key(key_name)

        if success:
            if no_emoji:
                print(f"API key permanently deleted: {key_name}")
            else:
                print(f"✅ API key permanently deleted: {key_name}")
        else:
            if no_emoji:
                print(f"API key not found: {key_name}")
            else:
                print(f"❌ API key not found: {key_name}")

        return success

    def test_api_key(
        self, key_name: str, server_url: Optional[str] = None, skip_ssl_verify: bool = False, no_emoji: bool = False
    ) -> bool:
        """Test if an API key is valid and can authenticate with n8n server

        Args:
            key_name: Name of the API key to test
            server_url: Server URL to test against (uses N8N_SERVER_URL if not specified)
            skip_ssl_verify: Skip SSL certificate verification
            no_emoji: Use text-only output without emojis

        Returns:
            True if test succeeds, False otherwise
        """
        import os
        import requests

        # Get API key from database
        api_key = self.get_api_key(key_name)
        if not api_key:
            if no_emoji:
                print(f"API key not found: {key_name}")
            else:
                print(f"❌ API key not found: {key_name}")
            return False

        # Determine server URL
        test_server = server_url or os.getenv("N8N_SERVER_URL")
        if not test_server:
            if no_emoji:
                print("No server URL specified. Use --server-url option or set N8N_SERVER_URL environment variable")
            else:
                print("⚠️  No server URL specified. Use --server-url option or set N8N_SERVER_URL environment variable")
            print(f"   Testing basic validity only:")
            print(f"   Key length: {len(api_key)} characters")
            print(f"   Key prefix: {api_key[:8]}..." if len(api_key) > 8 else f"   Key: {api_key}")
            return True

        # Test against n8n server
        if no_emoji:
            print(f"Testing API key '{key_name}' against server: {test_server}")
        else:
            print(f"🧪 Testing API key '{key_name}' against server: {test_server}")

        try:
            from api.cli.verbose import log_error, log_request, log_response

            # Make a simple authenticated request to /api/v1/workflows
            url = f"{test_server.rstrip('/')}/api/v1/workflows"
            headers = {
                "X-N8N-API-KEY": api_key,
                "Content-Type": "application/json",
            }

            start_time = log_request("GET", url, headers)
            response = requests.get(url, headers=headers, verify=not skip_ssl_verify, timeout=10)
            log_response(response.status_code, dict(response.headers), start_time)
            response.raise_for_status()

            # Parse response
            data = response.json()
            workflow_count = len(data.get("data", [])) if isinstance(data, dict) else len(data)

            if no_emoji:
                print(f"API key is valid and authenticated successfully")
                print(f"Server responded with {workflow_count} workflows")
            else:
                print(f"✅ API key is valid and authenticated successfully")
                print(f"   Server responded with {workflow_count} workflows")

            return True

        except requests.exceptions.Timeout:
            log_error("TIMEOUT", f"Connection timed out after 10 seconds")
            if no_emoji:
                print(f"Connection to {test_server} timed out after 10 seconds")
            else:
                print(f"❌ Connection to {test_server} timed out after 10 seconds")
            return False
        except requests.exceptions.SSLError as e:
            log_error("SSL", str(e))
            if no_emoji:
                print(f"SSL certificate verification failed: {e}")
                print("Use --skip-ssl-verify to bypass SSL verification (not recommended for production)")
            else:
                print(f"❌ SSL certificate verification failed: {e}")
                print("   Use --skip-ssl-verify to bypass SSL verification (not recommended for production)")
            return False
        except requests.exceptions.HTTPError as e:
            log_error("HTTP", str(e))
            if no_emoji:
                print(f"Authentication failed: {e}")
                print("The API key may be invalid or expired")
            else:
                print(f"❌ Authentication failed: {e}")
                print("   The API key may be invalid or expired")
            return False
        except requests.exceptions.RequestException as e:
            log_error("REQUEST", str(e))
            if no_emoji:
                print(f"Failed to connect to server: {e}")
            else:
                print(f"❌ Failed to connect to server: {e}")
            return False
        except Exception as e:
            log_error("UNKNOWN", str(e))
            if no_emoji:
                print(f"Unexpected error during API key test: {e}")
            else:
                print(f"❌ Unexpected error during API key test: {e}")
            return False
