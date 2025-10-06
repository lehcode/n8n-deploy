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


class TestDbOperations(DatabaseTestHelpers):
    """Test Db Operations tests"""

    def test_database_compact_command(self) -> None:
        """Test db compact command optimizes database storage"""
        # Initialize database first
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Run compact command
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "compact"])

        assert returncode == 0
        assert "Optimizing database" in stdout
        assert "optimization complete" in stdout

    def test_database_compact_with_no_emoji(self) -> None:
        """Test db compact command with --no-emoji flag"""
        # Initialize database first
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Run compact with no-emoji (already applied via run_cli_command)
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "compact"])

        assert returncode == 0
        # Should not contain emoji when using --no-emoji
        assert "🎭" not in stdout
        assert "✅" not in stdout

    def test_empty_database_operations(self) -> None:
        """Test operations on empty database"""
        # Initialize empty database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        empty_db_operations = [
            ["wf", "list"],  # wf list doesn't need --data-dir
            ["--data-dir", self.temp_dir, "db", "status"],
        ]

        for op in empty_db_operations:
            returncode, stdout, stderr = self.run_cli_command(op)
            assert returncode == 0, f"Empty database operation failed: {op}\nSTDERR: {stderr}\nSTDOUT: {stdout}"

    def test_database_size_tracking(self) -> None:
        """Test database size is reasonable and tracked"""
        # Initialize database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        workflow_file = Path(self.temp_flow_dir) / "size_test.json"
        workflow_data = {
            "name": "Size Test Workflow",
            "nodes": [{"id": "node1", "type": "test"}],
            "connections": {},
        }
        workflow_file.write_text(json.dumps(workflow_data))
        self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "size_test",
            ]
        )

        final_size = db_path.stat().st_size

        # Database should be reasonable size (not too large)
        assert final_size < 10 * 1024 * 1024  # Less than 10MB for test data
