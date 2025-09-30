#!/usr/bin/env python3
"""
Unit tests for database CLI commands module

Tests the modular database commands: init, status, compact, backup
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.cli.db import db


class TestDatabaseCommands:
    """Test database command group and individual commands"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_db_group_help(self):
        """Test database group help output"""
        result = self.runner.invoke(db, ["--help"])
        assert result.exit_code == 0
        assert "Database management commands" in result.output
        assert "backup" in result.output
        assert "compact" in result.output
        assert "init" in result.output
        assert "status" in result.output

    def test_init_command_help(self):
        """Test init command help"""
        result = self.runner.invoke(db, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize n8n-deploy database" in result.output
        assert "--app-dir" in result.output
        assert "--no-emoji" in result.output
        assert "--force" in result.output

    def test_status_command_help(self):
        """Test status command help"""
        result = self.runner.invoke(db, ["status", "--help"])
        assert result.exit_code == 0
        assert "Show database status and statistics" in result.output
        assert "--app-dir" in result.output
        assert "--format" in result.output

    def test_compact_command_help(self):
        """Test compact command help"""
        result = self.runner.invoke(db, ["compact", "--help"])
        assert result.exit_code == 0
        assert "Compact database to optimize storage" in result.output
        assert "--app-dir" in result.output
        assert "--no-emoji" in result.output

    def test_backup_command_help(self):
        """Test backup command help"""
        result = self.runner.invoke(db, ["backup", "--help"])
        assert result.exit_code == 0
        assert "Create database backup" in result.output
        assert "--app-dir" in result.output

    @patch("api.cli.db.DBApi")
    @patch("api.config.AppConfig")
    def test_init_command_new_database(self, mock_config, mock_db):
        """Test init command with new database"""
        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.base_folder = Path(self.temp_dir)
        mock_config.return_value = mock_config_instance

        # Mock database path doesn't exist
        db_path = Path(self.temp_dir) / "n8n-deploy.db"

        result = self.runner.invoke(db, ["init", "--app-dir", self.temp_dir, "--no-emoji"])

        assert result.exit_code == 0
        assert "Database initialized" in result.output
        mock_db.assert_called_once()

    @patch("api.cli.db.DBApi")
    @patch("api.cli.db.get_config")
    def test_status_command_table_format(self, mock_get_config, mock_db):
        """Test status command with table format"""
        # Mock config
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Mock database manager and stats
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        mock_stats = MagicMock()
        mock_stats.database_path = str(Path(self.temp_dir) / "test.db")
        mock_stats.database_size = 1024
        mock_stats.schema_version = 1
        mock_stats.tables = {"workflows": 5, "api_keys": 2}
        mock_db_instance.get_database_stats.return_value = mock_stats

        result = self.runner.invoke(db, ["status", "--app-dir", self.temp_dir])

        assert result.exit_code == 0
        assert "Database Status" in result.output
        mock_db_instance.get_database_stats.assert_called_once()

    @patch("api.cli.db.DBApi")
    @patch("api.cli.db.get_config")
    def test_status_command_json_format(self, mock_get_config, mock_db):
        """Test status command with JSON format"""
        # Mock config
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Mock database manager and stats
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        mock_stats = MagicMock()
        mock_stats.database_path = str(Path(self.temp_dir) / "test.db")
        mock_stats.database_size = 1024
        mock_stats.schema_version = 1
        mock_stats.tables = {"workflows": 5, "api_keys": 2}
        mock_db_instance.get_database_stats.return_value = mock_stats

        result = self.runner.invoke(db, ["status", "--app-dir", self.temp_dir, "--format", "json"])

        assert result.exit_code == 0
        assert "database_path" in result.output
        assert "database_size" in result.output
        mock_db_instance.get_database_stats.assert_called_once()

    @patch("api.cli.db.DBApi")
    @patch("api.cli.db.get_config")
    def test_compact_command(self, mock_get_config, mock_db):
        """Test compact command"""
        # Mock config
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Mock database manager
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        result = self.runner.invoke(db, ["compact", "--app-dir", self.temp_dir, "--no-emoji"])

        assert result.exit_code == 0
        assert "Optimizing database" in result.output
        assert "Database optimization complete" in result.output
        mock_db_instance.compact.assert_called_once()

    @patch("api.cli.db.DBApi")
    @patch("api.cli.db.get_config")
    def test_backup_command_with_path(self, mock_get_config, mock_db):
        """Test backup command with specified path"""
        # Mock config
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Mock database manager
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        backup_path = str(Path(self.temp_dir) / "backup.db")
        result = self.runner.invoke(db, ["backup", backup_path, "--app-dir", self.temp_dir])

        assert result.exit_code == 0
        mock_db_instance.backup.assert_called_once_with(backup_path)

    @patch("api.cli.db.DBApi")
    @patch("api.cli.db.get_config")
    def test_backup_command_auto_path(self, mock_get_config, mock_db):
        """Test backup command with automatic path generation"""
        # Mock config
        mock_config = MagicMock()
        mock_config.backups_path = Path(self.temp_dir) / "backups"
        mock_get_config.return_value = mock_config

        # Mock database manager
        mock_db_instance = MagicMock()
        mock_db.return_value = mock_db_instance

        result = self.runner.invoke(db, ["backup", "--app-dir", self.temp_dir])

        assert result.exit_code == 0
        # Should call backup with generated path
        mock_db_instance.backup.assert_called_once()
        # Check that the path contains the expected pattern
        backup_call = mock_db_instance.backup.call_args[0][0]
        assert "n8n_deploy_backup_" in backup_call
        assert backup_call.endswith(".db")
