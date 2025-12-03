#!/usr/bin/env python3
"""
Database test helpers and shared utilities.

Provides DatabaseTestHelpers mixin class with common database CLI operations
to reduce code duplication across database E2E tests.
"""

import json
from pathlib import Path
from typing import Optional, Tuple

import pytest

from ..e2e_base import E2ETestBase
from tests.helpers import assert_json_output_valid as _assert_json_valid


class DatabaseTestHelpers(E2ETestBase):
    """Helper methods for database E2E testing"""

    def run_db_init(
        self,
        data_dir: Optional[str] = None,
        filename: Optional[str] = None,
        output_json: bool = False,
        no_emoji: bool = True,
        stdin_input: str = "",
    ) -> Tuple[int, str, str]:
        """Execute 'db init' command with common parameters"""
        args = ["db", "init"]

        if data_dir:
            args.extend(["--data-dir", data_dir])
        if filename:
            args.extend(["--db-filename", filename])
        if output_json:
            args.append("--json")
        if no_emoji:
            args.append("--no-emoji")

        return self.run_cli_command(args, stdin_input=stdin_input)

    def run_db_status(
        self,
        data_dir: Optional[str] = None,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'db status' command with common parameters"""
        args = ["db", "status"]

        if data_dir:
            args.extend(["--data-dir", data_dir])
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_db_backup(
        self,
        backup_path: Optional[str] = None,
        data_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Execute 'db backup' command with common parameters"""
        args = ["db", "backup"]

        if backup_path:
            args.append(backup_path)
        if data_dir:
            args.extend(["--data-dir", data_dir])

        return self.run_cli_command(args)

    def run_db_compact(
        self,
        data_dir: Optional[str] = None,
        no_emoji: bool = True,
    ) -> Tuple[int, str, str]:
        """Execute 'db compact' command with common parameters"""
        args = ["db", "compact"]

        if data_dir:
            args.extend(["--data-dir", data_dir])
        if no_emoji:
            args.append("--no-emoji")

        return self.run_cli_command(args)

    def assert_database_exists(self, data_dir: str, filename: str = "n8n-deploy.db") -> None:
        """Assert database file exists at expected location"""
        db_path = Path(data_dir) / filename
        assert db_path.exists(), f"Database file not found at {db_path}"

    def assert_database_not_exists(self, data_dir: str, filename: str = "n8n-deploy.db") -> None:
        """Assert database file does not exist"""
        db_path = Path(data_dir) / filename
        assert not db_path.exists(), f"Database file should not exist at {db_path}"

    def assert_json_output_valid(self, stdout: str) -> dict:
        """Assert stdout contains valid JSON and return parsed data"""
        return _assert_json_valid(stdout)

    def assert_backup_exists(self, backup_path: str) -> None:
        """Assert backup file exists"""
        assert Path(backup_path).exists(), f"Backup file not found: {backup_path}"

    def get_database_size(self, data_dir: str, filename: str = "n8n-deploy.db") -> int:
        """Get database file size in bytes"""
        db_path = Path(data_dir) / filename
        if not db_path.exists():
            return 0
        return db_path.stat().st_size
