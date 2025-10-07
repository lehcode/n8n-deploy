#!/usr/bin/env python3
"""
Unit tests for API key CLI commands module

Tests the modular API key commands: add, list, activate, deactivate, delete, test
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.cli.apikey import apikey


class TestAPIKeyCommands:
    """Test API key command group and individual commands"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_apikey_group_help(self):
        """Test API key group help output"""
        result = self.runner.invoke(apikey, ["--help"])
        assert result.exit_code == 0
        assert "API key management commands" in result.output
        assert "add" in result.output
        assert "list" in result.output
        assert "delete" in result.output
        assert "test" in result.output

    def test_add_command_help(self):
        """Test add command help"""
        result = self.runner.invoke(apikey, ["add", "--help"])
        assert result.exit_code == 0
        assert "Add new API key" in result.output
        assert "--name" in result.output
        assert "--description" in result.output
        assert "--server" in result.output

    def test_list_command_help(self):
        """Test list command help"""
        result = self.runner.invoke(apikey, ["list", "--help"])
        assert result.exit_code == 0
        assert "List all stored API keys" in result.output
        assert "--unmask" in result.output

    def test_activate_command_help(self):
        """Test activate command help"""
        result = self.runner.invoke(apikey, ["activate", "--help"])
        assert result.exit_code == 0
        assert "Activate API key" in result.output
        assert "KEY_NAME" in result.output

    def test_deactivate_command_help(self):
        """Test deactivate command help"""
        result = self.runner.invoke(apikey, ["deactivate", "--help"])
        assert result.exit_code == 0
        assert "Deactivate API key" in result.output
        assert "KEY_NAME" in result.output

    def test_delete_command_help(self):
        """Test delete command help"""
        result = self.runner.invoke(apikey, ["delete", "--help"])
        assert result.exit_code == 0
        assert "Permanently delete an API key" in result.output
        assert "--force" in result.output

    def test_test_command_help(self):
        """Test test command help"""
        result = self.runner.invoke(apikey, ["test", "--help"])
        assert result.exit_code == 0
        assert "Test API key validity" in result.output
        assert "KEY_NAME" in result.output

    @patch("api.cli.apikey.KeyApi")
    @patch("api.config.AppConfig")
    def test_add_command_with_name(self, mock_config, mock_api_manager):
        """Test add command with key name"""
        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.base_folder = Path(self.temp_dir)
        mock_config.return_value = mock_config_instance

        # Mock API manager
        mock_manager_instance = MagicMock()
        mock_api_manager.return_value = mock_manager_instance
        mock_manager_instance.add_api_key.return_value = True

        # Test add command with stdin input (use valid JWT format)
        result = self.runner.invoke(apikey, ["add", "--name", "test_key"], input="eyJhbGci.eyJzdWI.signature\n")

        assert result.exit_code == 0
        mock_manager_instance.add_api_key.assert_called_once()

    @patch("api.cli.apikey.KeyApi")
    @patch("api.config.AppConfig")
    def test_list_command_empty(self, mock_config, mock_api_manager):
        """Test list command with no API keys"""
        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.base_folder = Path(self.temp_dir)
        mock_config.return_value = mock_config_instance

        # Mock API manager
        mock_manager_instance = MagicMock()
        mock_api_manager.return_value = mock_manager_instance
        mock_manager_instance.list_api_keys.return_value = []

        result = self.runner.invoke(apikey, ["list"])

        assert result.exit_code == 0
        assert "No API keys found" in result.output
        mock_manager_instance.list_api_keys.assert_called_once()

    @patch("api.cli.apikey.KeyApi")
    @patch("api.config.AppConfig")
    def test_activate_command_functionality(self, mock_config, mock_api_manager):
        """Test activate command functionality"""
        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.base_folder = Path(self.temp_dir)
        mock_config.return_value = mock_config_instance

        # Mock API manager
        mock_manager_instance = MagicMock()
        mock_api_manager.return_value = mock_manager_instance
        mock_manager_instance.activate_api_key.return_value = True

        result = self.runner.invoke(apikey, ["activate", "test_key"])

        assert result.exit_code == 0
        mock_manager_instance.activate_api_key.assert_called_once_with("test_key")

    @patch("api.cli.apikey.KeyApi")
    @patch("api.config.AppConfig")
    def test_deactivate_command_functionality(self, mock_config, mock_api_manager):
        """Test deactivate command functionality"""
        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.base_folder = Path(self.temp_dir)
        mock_config.return_value = mock_config_instance

        # Mock API manager
        mock_manager_instance = MagicMock()
        mock_api_manager.return_value = mock_manager_instance
        mock_manager_instance.deactivate_api_key.return_value = True

        result = self.runner.invoke(apikey, ["deactivate", "test_key"])

        assert result.exit_code == 0
        mock_manager_instance.deactivate_api_key.assert_called_once_with("test_key")

    @patch("api.cli.apikey.KeyApi")
    @patch("api.config.AppConfig")
    def test_test_command_functionality(self, mock_config, mock_api_manager):
        """Test test command functionality"""
        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.base_folder = Path(self.temp_dir)
        mock_config.return_value = mock_config_instance

        # Mock API manager
        mock_manager_instance = MagicMock()
        mock_api_manager.return_value = mock_manager_instance
        mock_manager_instance.test_api_key.return_value = True

        result = self.runner.invoke(apikey, ["test", "test_key"])

        assert result.exit_code == 0
        mock_manager_instance.test_api_key.assert_called_once_with(
            "test_key", server_url=None, skip_ssl_verify=False, no_emoji=False
        )

    @patch("api.cli.apikey.KeyApi")
    @patch("api.config.AppConfig")
    def test_delete_command_with_confirmation(self, mock_config, mock_api_manager):
        """Test delete command with confirmation"""
        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.base_folder = Path(self.temp_dir)
        mock_config.return_value = mock_config_instance

        # Mock API manager
        mock_manager_instance = MagicMock()
        mock_api_manager.return_value = mock_manager_instance
        mock_manager_instance.delete_api_key.return_value = True

        result = self.runner.invoke(apikey, ["delete", "test_key", "--force"])

        assert result.exit_code == 0
        mock_manager_instance.delete_api_key.assert_called_once_with("test_key", force=True, no_emoji=False)
