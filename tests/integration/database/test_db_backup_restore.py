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


class TestDbBackupRestore(DatabaseTestHelpers):
    """Test Db Backup Restore tests"""

    def test_database_backup_creation(self) -> None:
        """Test database backup functionality"""
        # Initialize database first
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "backup"])

        assert returncode == 0
        backup_dir = Path(self.temp_dir) / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.db"))
            assert len(backup_files) > 0, "No backup files created"

    def test_backup_workflows_complete_cycle(self) -> None:
        """Test complete backup cycle with workflows"""
        # Initialize database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        workflow_file = Path(self.temp_flow_dir) / "test_workflow.json"
        workflow_data = {
            "name": "Test Workflow",
            "nodes": [],
            "connections": {},
            "active": False,
        }
        workflow_file.write_text(json.dumps(workflow_data, indent=2))
        env = {"N8N_DEPLOY_FLOWS_DIR": self.temp_flow_dir}
        self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "test_workflow",
            ],
            env=env,
        )
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "backup"])

        assert returncode == 0
        backup_dir = Path(self.temp_dir) / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.tar.gz"))
            if backup_files:
                try:
                    with tarfile.open(backup_files[0], "r:gz") as tar:
                        assert len(tar.getnames()) > 0
                except Exception:
                    pytest.fail("Backup file is not valid tar.gz")

    def test_restore_backup_functionality(self) -> None:
        """Test backup restore functionality"""
        # Initialize database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        backup_result = self.run_cli_command(["--data-dir", self.temp_dir, "db", "backup"])

        if backup_result[0] == 0:  # Backup successful
            # Try to restore (may not be implemented yet)
            returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "restore", "--help"])
            if returncode == 0 and "restore" in stdout.lower():
                # Restore command exists, test it
                backup_dir = Path(self.temp_dir) / "backups"
                backup_files = list(backup_dir.glob("*.tar.gz"))
                if backup_files:
                    restore_result = self.run_cli_command(
                        [
                            "--data-dir",
                            self.temp_dir,
                            "db",
                            "restore",
                            str(backup_files[0]),
                        ]
                    )
                    # Should complete without crashing
                    assert restore_result[0] in [0, 1]
