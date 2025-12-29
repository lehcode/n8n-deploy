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


def _test_key_output(message: str, no_emoji: bool, emoji: str = "", indent: bool = False) -> None:
    """Output a message with optional emoji prefix.

    Args:
        message: The message text to output
        no_emoji: If True, output without emoji
        emoji: Emoji to prepend if no_emoji is False
        indent: If True, add indentation for sub-messages
    """
    prefix = "   " if indent else ""
    if no_emoji:
        print(f"{prefix}{message}")
    else:
        emoji_prefix = f"{emoji} " if emoji else ""
        print(f"{prefix}{emoji_prefix}{message}")


def _test_key_basic_validity(api_key: str) -> bool:
    """Test basic validity when no server URL is available."""
    print(f"   Testing basic validity only:")
    print(f"   Key length: {len(api_key)} characters")
    if len(api_key) > 8:
        print(f"   Key prefix: {api_key[:8]}...")
    else:
        print(f"   Key: {api_key}")
    return True


def _test_key_parse_response(data: Any) -> int:
    """Parse response data and return workflow count."""
    if isinstance(data, dict):
        return len(data.get("data", []))
    return len(data)


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
        from api.cli.verbose import log_error, log_request, log_response

        # Get API key from database
        api_key = self.get_api_key(key_name)
        if not api_key:
            _test_key_output(f"API key not found: {key_name}", no_emoji, "❌")
            return False

        # Determine server URL
        test_server = server_url or os.getenv("N8N_SERVER_URL")
        if not test_server:
            _test_key_output(
                "No server URL specified. Use --server-url option or set N8N_SERVER_URL environment variable",
                no_emoji,
                "⚠️",
            )
            return _test_key_basic_validity(api_key)

        _test_key_output(f"Testing API key '{key_name}' against server: {test_server}", no_emoji, "🧪")

        return self._execute_api_test(test_server, api_key, skip_ssl_verify, no_emoji, log_request, log_response, log_error)

    def _execute_api_test(
        self,
        test_server: str,
        api_key: str,
        skip_ssl_verify: bool,
        no_emoji: bool,
        log_request: Any,
        log_response: Any,
        log_error: Any,
    ) -> bool:
        """Execute the actual API test request."""
        import requests

        url = f"{test_server.rstrip('/')}/api/v1/workflows"
        headers = {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}

        try:
            start_time = log_request("GET", url, headers)
            response = requests.get(url, headers=headers, verify=not skip_ssl_verify, timeout=10)
            log_response(response.status_code, dict(response.headers), start_time)
            response.raise_for_status()

            workflow_count = _test_key_parse_response(response.json())
            _test_key_output("API key is valid and authenticated successfully", no_emoji, "✅")
            _test_key_output(f"Server responded with {workflow_count} workflows", no_emoji, indent=True)
            return True

        except requests.exceptions.Timeout:
            log_error("TIMEOUT", "Connection timed out after 10 seconds")
            _test_key_output(f"Connection to {test_server} timed out after 10 seconds", no_emoji, "❌")
            return False

        except requests.exceptions.SSLError as e:
            log_error("SSL", str(e))
            _test_key_output(f"SSL certificate verification failed: {e}", no_emoji, "❌")
            _test_key_output(
                "Use --skip-ssl-verify to bypass SSL verification (not recommended for production)", no_emoji, indent=True
            )
            return False

        except requests.exceptions.HTTPError as e:
            log_error("HTTP", str(e))
            _test_key_output(f"Authentication failed: {e}", no_emoji, "❌")
            _test_key_output("The API key may be invalid or expired", no_emoji, indent=True)
            return False

        except requests.exceptions.RequestException as e:
            log_error("REQUEST", str(e))
            _test_key_output(f"Failed to connect to server: {e}", no_emoji, "❌")
            return False

        except Exception as e:
            log_error("UNKNOWN", str(e))
            _test_key_output(f"Unexpected error during API key test: {e}", no_emoji, "❌")
            return False
