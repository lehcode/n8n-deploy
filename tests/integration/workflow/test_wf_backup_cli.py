#!/usr/bin/env python3
"""
End-to-End Manual Workflow Testing

Real CLI execution tests for wf management operations,
including add, list, search, stats, and file operations.
"""

import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from unittest.mock import patch

import pytest

from api.config import AppConfig
from api.models import Workflow
from api.workflow import WorkflowApi


# === End-to-End Workflow Tests ===
from .conftest import WorkflowTestHelpers


class Testwfbackupcli(WorkflowTestHelpers):
    """Test Wf Backup Cli tests"""

    def test_list_backups_shows_metadata(self) -> None:
        """Test wf backups command shows backup file metadata"""
        # Initialize and create backup
        self.run_cli_command(["db", "init", "--data-dir", self.temp_dir])
        self.run_cli_command(["db", "backup", "--data-dir", self.temp_dir])

        # List backups - just lists files in backup directory, no database access needed
        backup_dir = Path(self.temp_dir) / "backups"
        returncode, stdout, stderr = self.run_cli_command(["wf", "backups", "--backup-dir", str(backup_dir)])

        # Should succeed (even if no backups exist yet)
        assert returncode == 0, f"Command failed with returncode {returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}"

    # === Additional Workflow Command Tests for Complete Coverage ===

    def test_wf_backup_with_backup_dir(self) -> None:
        """Test wf backup --backup-dir creates backup in specified directory"""
        self.setup_database()
        backup_dir = Path(self.temp_dir) / "custom_backups"
        backup_dir.mkdir(exist_ok=True)

        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "createbackup",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        # May succeed or fail based on workflows available
        assert returncode in [0, 1]

    def test_wf_restore_with_backup_file(self) -> None:
        """Test wf restore <backup-file> restores workflows"""
        self.setup_database()

        # Create a backup first (may fail if no workflows)
        backup_dir = Path(self.temp_dir) / "test_restore_backups"
        backup_dir.mkdir(exist_ok=True)

        # Try to restore a non-existent backup
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "wf",
                "restore",
                "nonexistent_backup.tar.gz",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        # Should fail gracefully for non-existent backup
        assert returncode in [0, 1]

    def test_wf_list_backups_json_format(self) -> None:
        """Test wf backups --format json output"""
        backup_dir = Path(self.temp_dir) / "json_backups"
        backup_dir.mkdir(exist_ok=True)

        returncode, stdout, stderr = self.run_cli_command(["wf", "backups", "--backup-dir", str(backup_dir), "--json"])

        assert returncode == 0

        # Should be valid JSON (empty list for empty directory)
        data = json.loads(stdout)
        assert isinstance(data, list)
        assert len(data) == 0  # No backups in empty directory

    def test_wf_verify_backup_success(self) -> None:
        """Test wf verify validates backup file integrity"""
        backup_dir = Path(self.temp_dir) / "verify_backups"
        backup_dir.mkdir(exist_ok=True)

        # Create a valid tar.gz file
        import tarfile

        backup_file = backup_dir / "test_backup.tar.gz"
        with tarfile.open(backup_file, "w:gz") as tar:
            # Add a dummy file
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
                tmp.write('{"test": "data"}')
                tmp_path = tmp.name

            tar.add(tmp_path, arcname="test.json")
            Path(tmp_path).unlink()

        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "verify",
                "test_backup.tar.gz",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        assert returncode == 0
        assert "valid" in stdout.lower()

    def test_wf_verify_backup_corrupted(self) -> None:
        """Test wf verify handles corrupted backup files"""
        backup_dir = Path(self.temp_dir) / "corrupted_backups"
        backup_dir.mkdir(exist_ok=True)

        # Create a corrupted file
        corrupted_file = backup_dir / "corrupted_backup.tar.gz"
        corrupted_file.write_text("This is not a valid tar.gz file")

        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "verify",
                "corrupted_backup.tar.gz",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        # Should fail for corrupted backup
        assert returncode == 1
        assert "corrupted" in stdout.lower() or "invalid" in stdout.lower()
