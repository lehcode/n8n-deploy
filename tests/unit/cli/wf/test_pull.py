#!/usr/bin/env python3
"""Unit tests for wf pull CLI command."""

import importlib
from unittest.mock import patch

import pytest

# Import the module using importlib to avoid shadowing by __init__.py
pull_module = importlib.import_module("api.cli.wf.pull")


class TestPromptForFilename:
    """Tests for _prompt_for_filename function in non-interactive mode."""

    def test_non_interactive_uses_default_filename(self) -> None:
        """Test that non-interactive mode uses default filename without prompting."""
        with patch.object(pull_module, "is_interactive_mode", return_value=False):
            with patch.object(pull_module, "console") as mock_console:
                result = pull_module._prompt_for_filename("test123", no_emoji=False)

        assert result == "test123.json"
        mock_console.print.assert_called_once()
        assert "test123.json" in mock_console.print.call_args[0][0]

    def test_non_interactive_with_no_emoji(self) -> None:
        """Test non-interactive mode respects no_emoji flag."""
        with patch.object(pull_module, "is_interactive_mode", return_value=False):
            with patch.object(pull_module, "console") as mock_console:
                result = pull_module._prompt_for_filename("wf_abc", no_emoji=True)

        assert result == "wf_abc.json"
        printed_msg = mock_console.print.call_args[0][0]
        # When no_emoji=True, prefix should be empty string
        assert not printed_msg.startswith("Info:")

    def test_interactive_mode_prompts_user(self) -> None:
        """Test that interactive mode prompts the user."""
        with patch.object(pull_module, "is_interactive_mode", return_value=True):
            with patch.object(pull_module, "console"):
                with patch.object(pull_module.click, "prompt", return_value="custom-name") as mock_prompt:
                    result = pull_module._prompt_for_filename("wf123", no_emoji=False)

        mock_prompt.assert_called_once()
        assert result == "custom-name.json"

    def test_interactive_adds_json_extension(self) -> None:
        """Test that .json extension is added if missing."""
        with patch.object(pull_module, "is_interactive_mode", return_value=True):
            with patch.object(pull_module, "console"):
                with patch.object(pull_module.click, "prompt", return_value="my-workflow"):
                    result = pull_module._prompt_for_filename("wf123", no_emoji=False)

        assert result == "my-workflow.json"

    def test_interactive_preserves_json_extension(self) -> None:
        """Test that existing .json extension is not duplicated."""
        with patch.object(pull_module, "is_interactive_mode", return_value=True):
            with patch.object(pull_module, "console"):
                with patch.object(pull_module.click, "prompt", return_value="my-workflow.json"):
                    result = pull_module._prompt_for_filename("wf123", no_emoji=False)

        assert result == "my-workflow.json"
