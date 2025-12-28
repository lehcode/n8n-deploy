#!/usr/bin/env python3
"""
Server resolution for n8n API operations

Handles resolving server URLs and API keys from various sources:
- Workflow-linked servers
- Environment variables
- CLI --remote flag
- Database lookups

Extracted from n8n_api.py to reduce complexity and improve testability.
"""

import os
from typing import Any, Dict, Optional, Tuple

from ..api_keys import KeyApi
from ..config import AppConfig
from ..db import DBApi
from ..db.servers import ServerCrud
from ..jwt_utils import check_jwt_expiration


class ServerResolver:
    """Resolves server URLs and API keys for n8n operations

    Resolution priority (lowest to highest):
    1. linked_server (workflow's server_id) - workflow-specific default
    2. ENV_VARIABLE (N8N_SERVER_URL) - system-wide default
    3. --remote flag - explicit override
    """

    def __init__(
        self,
        config: AppConfig,
        db: DBApi,
        api_manager: KeyApi,
        remote: Optional[str] = None,
        skip_ssl_verify: bool = False,
    ) -> None:
        """Initialize server resolver

        Args:
            config: Application configuration
            db: Database API for workflow lookups
            api_manager: API key manager
            remote: Optional --remote CLI flag value
            skip_ssl_verify: CLI override for SSL verification (from --skip-ssl-verify)
        """
        self.config = config
        self.db = db
        self.api_manager = api_manager
        self.remote = remote
        self.cli_skip_ssl_verify = skip_ssl_verify  # CLI override

        # Cache resolved values
        self._cached_url: Optional[str] = None
        self._cached_api_key: Optional[str] = None
        self._cached_skip_ssl_verify: Optional[bool] = None

    def clear_cache(self) -> None:
        """Clear cached server URL, API key, and SSL setting"""
        self._cached_url = None
        self._cached_api_key = None
        self._cached_skip_ssl_verify = None

    def resolve(self, workflow_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str], bool]:
        """Resolve server URL, API key, and SSL verification setting

        Args:
            workflow_id: Optional workflow ID to check for linked server

        Returns:
            tuple: (server_url, api_key, skip_ssl_verify) or (None, None, False) if resolution fails

        Note:
            skip_ssl_verify priority: CLI flag > server setting > False (default)
        """
        if not self.remote:
            return self._resolve_without_remote(workflow_id)
        return self._resolve_with_remote()

    def get_credentials(self, workflow_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get n8n API credentials

        Uses cached values if available, otherwise resolves server.

        Args:
            workflow_id: Optional workflow ID for linked server resolution

        Returns:
            Dict with api_key, server_url, skip_ssl_verify, and headers, or None if unavailable
        """
        try:
            if self._cached_url and self._cached_api_key and self._cached_skip_ssl_verify is not None:
                server_url = self._cached_url
                api_key = self._cached_api_key
                skip_ssl = self._cached_skip_ssl_verify
            else:
                resolved_url, resolved_key, resolved_ssl = self.resolve(workflow_id=workflow_id)
                if not resolved_url or not resolved_key:
                    print("⚠️  No API key available for the specified server")
                    return None
                # Cache the values
                self._cached_url = resolved_url
                self._cached_api_key = resolved_key
                self._cached_skip_ssl_verify = resolved_ssl
                server_url = resolved_url
                api_key = resolved_key
                skip_ssl = resolved_ssl

            return {
                "api_key": api_key,
                "server_url": server_url,
                "skip_ssl_verify": skip_ssl,
                "headers": {
                    "X-N8N-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
            }
        except Exception as e:
            print(f"❌ Failed to retrieve API key: {e}")
            return None

    def _resolve_without_remote(self, workflow_id: Optional[str]) -> Tuple[Optional[str], Optional[str], bool]:
        """Resolve when no --remote flag specified

        Priority: workflow linked server > environment variable
        """
        # Start with environment variable
        server_url = self.config.n8n_api_url if self.config else os.getenv("N8N_SERVER_URL", "")

        # Check if workflow has linked server - this overrides ENV
        if workflow_id:
            result = self._resolve_from_workflow(workflow_id)
            if result[0] is not None and result[1] is not None:
                return result

        # Use environment variable (no workflow link or workflow not found)
        return self._resolve_from_api_keys(server_url)

    def _resolve_with_remote(self) -> Tuple[Optional[str], Optional[str], bool]:
        """Resolve when --remote flag is specified

        Checks if remote is a server name or URL.
        """
        # Guard: this method should only be called when remote is set
        if not self.remote:
            return (None, None, False)

        remote = self.remote  # Now guaranteed to be str
        server_api = ServerCrud(config=self.config)

        # Try as server name first
        server = server_api.get_server_by_name(remote)
        if server:
            api_key = server_api.get_api_key_for_server(remote)
            if not api_key:
                print(f"⚠️  No API key linked to server '{remote}'")
                print(f"   Use: n8n-deploy server link {remote} <key_name>")
                return (None, None, False)
            self._check_expiration(api_key)
            # CLI flag overrides server setting
            skip_ssl = self.cli_skip_ssl_verify or server.get("skip_ssl_verify", False)
            return (server["url"], api_key, skip_ssl)

        # Try as URL
        if remote.startswith("http://") or remote.startswith("https://"):
            return self._resolve_from_url(server_api, remote)

        print(f"❌ Server '{remote}' not found")
        print(f"   Add it with: n8n-deploy server add {remote} <url>")
        return (None, None, False)

    def _resolve_from_workflow(self, workflow_id: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Try to resolve server from workflow's linked server"""
        workflow = self.db.get_workflow(workflow_id)
        if not workflow or not workflow.server_id:
            return (None, None, False)

        server_api = ServerCrud(config=self.config)
        server = server_api.get_server_by_id(workflow.server_id)
        if not server:
            return (None, None, False)

        api_key = server_api.get_api_key_for_server(server["name"])
        if api_key:
            self._check_expiration(api_key)
            # CLI flag overrides server setting
            skip_ssl = self.cli_skip_ssl_verify or server.get("skip_ssl_verify", False)
            return (server["url"], api_key, skip_ssl)

        # Linked server but no API key
        print(f"⚠️  No API key linked to server '{server['name']}'")
        print(f"   Use: n8n-deploy server link {server['name']} <key_name>")
        return (None, None, False)

    def _resolve_from_api_keys(self, server_url: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Resolve API key from stored keys or environment"""
        keys = self.api_manager.list_api_keys()
        if keys:
            api_key = self.api_manager.get_api_key(keys[0]["name"])
            self._check_expiration(api_key)
            # No server record, use CLI flag only
            return (server_url, api_key, self.cli_skip_ssl_verify)

        # Fallback to environment variable
        env_api_key = os.getenv("N8N_API_KEY")
        self._check_expiration(env_api_key)
        # No server record, use CLI flag only
        return (server_url, env_api_key, self.cli_skip_ssl_verify)

    def _resolve_from_url(self, server_api: ServerCrud, url: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Resolve from URL - check if registered, otherwise use first available key"""
        server = server_api.get_server_by_url(url)
        if server:
            api_key = server_api.get_api_key_for_server(server["name"])
            self._check_expiration(api_key)
            # CLI flag overrides server setting
            skip_ssl = self.cli_skip_ssl_verify or server.get("skip_ssl_verify", False)
            return (url, api_key, skip_ssl)

        # URL not in database - try first available API key or environment
        keys = self.api_manager.list_api_keys()
        if keys:
            api_key = self.api_manager.get_api_key(keys[0]["name"])
            self._check_expiration(api_key)
            # No server record, use CLI flag only
            return (url, api_key, self.cli_skip_ssl_verify)

        env_api_key = os.getenv("N8N_API_KEY")
        self._check_expiration(env_api_key)
        # No server record, use CLI flag only
        return (url, env_api_key, self.cli_skip_ssl_verify)

    def _check_expiration(self, api_key: Optional[str]) -> None:
        """Check if API key is expired and print warning"""
        if not api_key:
            return

        is_expired, exp_datetime, warning = check_jwt_expiration(api_key)
        if warning:
            print(f"{warning}")
            if is_expired:
                print("Generate a new API key from your n8n server settings")
