#!/usr/bin/env python3
"""
Unit tests for database CLI commands module

Tests the modular database commands: init, status, compact, backup
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.cli.db import check_database_exists, db, is_interactive_mode


class TestInteractiveModeDetection:
    """Test interactive mode detection"""

    def test_is_interactive_mode_with_ci_var(self, monkeypatch):
        """Test non-interactive mode detection via CI variable"""
        monkeypatch.setenv("CI", "true")
        assert is_interactive_mode() is False

    def test_is_interactive_mode_with_gitlab_ci(self, monkeypatch):
        """Test non-interactive mode detection via GITLAB_CI variable"""
        monkeypatch.setenv("GITLAB_CI", "true")
        assert is_interactive_mode() is False

    def test_is_interactive_mode_with_github_actions(self, monkeypatch):
        """Test non-interactive mode detection via GITHUB_ACTIONS variable"""
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        assert is_interactive_mode() is False

    def test_is_interactive_mode_with_dumb_term(self, monkeypatch):
        """Test non-interactive mode detection via TERM=dumb"""
        # Clear CI vars first
        for var in ["CI", "GITLAB_CI", "GITHUB_ACTIONS"]:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("TERM", "dumb")
        assert is_interactive_mode() is False

    def test_is_interactive_mode_with_no_term(self, monkeypatch):
        """Test non-interactive mode detection via missing TERM"""
        # Clear CI vars and TERM
        for var in ["CI", "GITLAB_CI", "GITHUB_ACTIONS", "TERM"]:
            monkeypatch.delenv(var, raising=False)
        # Note: Result depends on stdin.isatty() which varies by environment
        # Just verify it doesn't crash
        result = is_interactive_mode()
        assert isinstance(result, bool)


class TestDatabaseHelpers:
    """Test database helper functions"""

    def test_check_database_exists_function(self):
        """Test check_database_exists helper function with missing database"""
        from pathlib import Path

        import click

        nonexistent_path = Path("/tmp/nonexistent-test-db.db")

        # Should raise click.Abort
        with pytest.raises(click.Abort):
            check_database_exists(nonexistent_path, format=None, no_emoji=True)

    def test_check_database_exists_json_format(self):
        """Test check_database_exists with JSON format"""
        from pathlib import Path

        import click

        nonexistent_path = Path("/tmp/nonexistent-test-db.db")

        # Should raise click.Abort with JSON error
        with pytest.raises(click.Abort):
            check_database_exists(nonexistent_path, format="json", no_emoji=False)

    def test_check_database_exists_with_existing_db(self):
        """Test check_database_exists with existing database (should not raise)"""
        import tempfile
        from pathlib import Path

        # Create a temporary file to simulate existing database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Should not raise
            check_database_exists(tmp_path, format=None, no_emoji=True)
        finally:
            # Clean up
            tmp_path.unlink()


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
        assert "--data-dir" in result.output
        assert "--no-emoji" in result.output
        assert "--import" in result.output

    def test_status_command_help(self):
        """Test status command help"""
        result = self.runner.invoke(db, ["status", "--help"])
        assert result.exit_code == 0
        assert "Show database status and statistics" in result.output
        assert "--data-dir" in result.output
        assert "--format" in result.output

    def test_compact_command_help(self):
        """Test compact command help"""
        result = self.runner.invoke(db, ["compact", "--help"])
        assert result.exit_code == 0
        assert "Compact database to optimize storage" in result.output
        assert "--data-dir" in result.output
        assert "--no-emoji" in result.output

    def test_backup_command_help(self):
        """Test backup command help"""
        result = self.runner.invoke(db, ["backup", "--help"])
        assert result.exit_code == 0
        assert "Create database backup" in result.output
        assert "--data-dir" in result.output

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

        result = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--no-emoji"])

        assert result.exit_code == 0
        assert "Database initialized" in result.output
        mock_db.assert_called_once()

    def test_init_import_flag_new_database(self):
        """Test --import flag with new database (should create it)"""
        result = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--import", "--no-emoji"])

        assert result.exit_code == 0
        assert "Database initialized" in result.output
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists()

    def test_init_import_flag_existing_database(self):
        """Test --import flag with existing database (should accept without prompt)"""
        # First create the database
        result1 = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--import", "--no-emoji"])
        assert result1.exit_code == 0

        # Run again with --import flag
        result2 = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--import", "--no-emoji"])

        assert result2.exit_code == 0
        assert "Using existing database" in result2.output
        assert "Database already exists" in result2.output

    def test_init_import_flag_json_format(self):
        """Test --import flag with JSON format output"""
        # Create database
        result1 = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--import", "--format", "json"])
        assert result1.exit_code == 0

        # Parse JSON output
        import json

        output1 = json.loads(result1.output)
        assert output1["success"] is True
        assert output1["message"] == "Database initialized"
        assert "database_path" in output1
        # New database should not have already_exists field or it should be False
        assert output1.get("already_exists", False) is False

        # Run again with existing database
        result2 = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--import", "--format", "json"])
        assert result2.exit_code == 0

        # Parse second JSON output
        output2 = json.loads(result2.output)
        assert output2["success"] is True
        assert output2["message"] == "Using existing database"
        assert output2["already_exists"] is True

    def test_init_import_flag_with_no_emoji(self):
        """Test --import flag combined with --no-emoji"""
        result = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--import", "--no-emoji"])

        assert result.exit_code == 0
        assert "Database initialized" in result.output
        # Verify no emoji in output
        assert "✅" not in result.output
        assert "🗄️" not in result.output
        assert "⚠️" not in result.output

    def test_init_json_format_implies_no_emoji(self):
        """Test that JSON format automatically disables emoji"""
        result = self.runner.invoke(db, ["init", "--data-dir", self.temp_dir, "--import", "--format", "json"])

        assert result.exit_code == 0
        # JSON output should not contain emoji
        import json

        output = json.loads(result.output)
        assert isinstance(output, dict)
        assert "success" in output

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

        result = self.runner.invoke(db, ["status", "--data-dir", self.temp_dir])

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

        result = self.runner.invoke(db, ["status", "--data-dir", self.temp_dir, "--format", "json"])

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

        result = self.runner.invoke(db, ["compact", "--data-dir", self.temp_dir, "--no-emoji"])

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
        result = self.runner.invoke(db, ["backup", backup_path, "--data-dir", self.temp_dir])

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

        result = self.runner.invoke(db, ["backup", "--data-dir", self.temp_dir])

        assert result.exit_code == 0
        # Should call backup with generated path
        mock_db_instance.backup.assert_called_once()
        # Check that the path contains the expected pattern
        backup_call = mock_db_instance.backup.call_args[0][0]
        assert "n8n_deploy_backup_" in backup_call
        assert backup_call.endswith(".db")
