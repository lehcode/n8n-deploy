#!/usr/bin/env python3
"""Unit tests for server CLI command."""

from typing import Any, Dict, List
from unittest.mock import patch

import pytest


class TestHandleApiKeyDecision:
    """Tests for _handle_api_key_decision function non-interactive behavior."""

    def test_non_interactive_defaults_to_preserve(self) -> None:
        """Test that non-interactive mode defaults to preserve API keys."""
        from api.cli.server import _handle_api_key_decision

        linked_keys: List[Dict[str, Any]] = [{"name": "test-key"}]

        with patch("api.cli.server.is_interactive_mode", return_value=False):
            with patch("api.cli.server.console"):
                result = _handle_api_key_decision(
                    server_name="test-server",
                    linked_keys=linked_keys,
                    key_action=None,
                    no_emoji=False,
                )

        assert result == "preserve"

    def test_explicit_key_action_overrides_non_interactive(self) -> None:
        """Test that explicit key_action is used regardless of interactivity."""
        from api.cli.server import _handle_api_key_decision

        linked_keys: List[Dict[str, Any]] = [{"name": "test-key"}]

        # With explicit key_action, should return that action
        result = _handle_api_key_decision(
            server_name="test-server",
            linked_keys=linked_keys,
            key_action="delete",
            no_emoji=False,
        )

        assert result == "delete"

    def test_empty_linked_keys_returns_preserve(self) -> None:
        """Test that empty linked keys returns preserve without prompting."""
        from api.cli.server import _handle_api_key_decision

        linked_keys: List[Dict[str, Any]] = []

        result = _handle_api_key_decision(
            server_name="test-server",
            linked_keys=linked_keys,
            key_action=None,
            no_emoji=False,
        )

        assert result == "preserve"

    def test_interactive_prompts_user(self) -> None:
        """Test that interactive mode prompts the user."""
        from api.cli.server import _handle_api_key_decision

        linked_keys: List[Dict[str, Any]] = [{"name": "test-key"}]

        with patch("api.cli.server.is_interactive_mode", return_value=True):
            with patch("api.cli.server.console"):
                with patch("api.cli.server.click.prompt", return_value=2) as mock_prompt:
                    result = _handle_api_key_decision(
                        server_name="test-server",
                        linked_keys=linked_keys,
                        key_action=None,
                        no_emoji=False,
                    )

        mock_prompt.assert_called_once()
        assert result == "delete"  # Option 2 is delete
