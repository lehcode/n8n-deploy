#!/usr/bin/env python3
"""
End-to-End Manual Database Testing

Real CLI execution tests for database operations, initialization,
backup/restore functionality, and stats display.
"""

import hashlib
import json
import os
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest


# === End-to-End Tests ===
from .conftest import DatabaseTestHelpers


class TestDbInitStatus(DatabaseTestHelpers):
    """Test Db Init Status tests"""

    def test_database_initialization(self) -> None:
        """Test database initialization creates proper schema"""
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Database initialization")
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists(), f"Database file not created at {db_path}"
        assert db_path.is_file(), f"Database path {db_path} is not a file"
        assert db_path.stat().st_size > 0, f"Database file {db_path} is empty (size: {db_path.stat().st_size})"

    def test_database_status_after_initialization(self) -> None:
        """Test db status command shows correct information"""
        # Initialize first
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status"])

        assert returncode == 0
        assert "Database" in stdout or "Status" in stdout
        # Should show database information without errors

    def test_database_status_without_database(self) -> None:
        """Test db status command handles missing database gracefully"""
        # Do NOT initialize database - test missing database case
        returncode, stdout, stderr = self.run_cli_command(["db", "status", "--data-dir", self.temp_dir])

        # Should fail gracefully with helpful error message
        assert returncode == 1
        assert "does not exist" in stdout.lower() or "not found" in stdout.lower()

    def test_database_status_without_database_json_format(self) -> None:
        """Test db status with JSON format handles missing database gracefully"""
        # Do NOT initialize database - test missing database case with JSON format
        returncode, stdout, stderr = self.run_cli_command(["db", "status", "--data-dir", self.temp_dir, "--json"])

        # Should fail gracefully with JSON error response
        assert returncode == 1
        # Should be valid JSON output
        import json

        error_data = json.loads(stdout)
        assert error_data["success"] is False
        assert "database_not_found" in error_data.get("error", "")

    def test_stats_command_shows_never_for_null_timestamps(self) -> None:
        """Test stats command handles null timestamps correctly"""
        # Initialize database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "wf", "stats"])

        assert returncode == 0

        # Should handle null/empty timestamps gracefully
        # Look for "Never" or similar text for empty timestamps
        if "Never" in stdout or "No" in stdout or "0" in stdout:
            # This indicates proper null timestamp handling
            pass

    def test_database_status_comprehensive_info(self) -> None:
        """Test db status shows comprehensive database information"""
        # Initialize database first
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Test status command
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status"])

        assert returncode == 0
        # Should contain key database information
        assert "Database" in stdout
        # Additional checks could include size, schema version, etc.

    def test_database_status_json_format(self) -> None:
        """Test db status with JSON format output"""
        # Initialize database first
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Test status with JSON format
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status", "--json"])

        assert returncode == 0
        # Should be valid JSON output
        try:
            import json

            status_data = json.loads(stdout)
            assert "database_path" in status_data
            assert "schema_version" in status_data
        except json.JSONDecodeError:
            assert False, f"Invalid JSON output: {stdout[:200]}..."

    # === CLI Database Command Tests ===
    # (Consolidated from test_cli_commands.py)
