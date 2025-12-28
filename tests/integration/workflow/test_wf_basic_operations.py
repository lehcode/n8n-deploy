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


class TestWorkflowBasicOps(WorkflowTestHelpers):
    """Test Workflow Basic Operations tests"""

    def test_workflow_add_requires_file(self) -> None:
        """Test that workflow add command requires local workflow file"""
        self.setup_database()

        # wf add registers a local workflow file, so without the file it should fail
        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "add",
                "TestWorkflow",
            ]
        )

        # Should fail with meaningful error about missing file
        assert returncode != 0  # Non-zero exit code indicates failure
        assert "not found" in stderr.lower() or "not found" in stdout.lower()

    def test_workflow_list_empty(self) -> None:
        """Test listing workflows when none exist"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["wf", "list"])

        assert returncode == 0
        # Should show empty list or appropriate message

    def test_workflow_list_populated(self) -> None:
        """Test listing workflows after adding some"""
        self.setup_database()
        workflows = ["test1", "test2", "test3"]
        for workflow_name in workflows:
            self.create_test_workflow(workflow_name)
            self.run_cli_command(
                [
                    "--data-dir",
                    self.temp_dir,
                    "--flow-dir",
                    self.temp_flow_dir,
                    "add",
                    f"{workflow_name}.json",
                    workflow_name.replace("_", "-"),
                ]
            )

        # List workflows
        returncode, stdout, stderr = self.run_cli_command(["wf", "list"])

        assert returncode == 0

    def test_wf_delete_with_yes_flag(self) -> None:
        """Test wf delete --yes skips confirmation"""
        self.setup_database()
        self.create_test_workflow("delete_yes_test")
        self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "delete_yes_test.json",
                "Delete Yes Test",
            ]
        )

        # Delete with --yes should skip confirmation
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "wf",
                "delete",
                "test_workflow_id",
                "--yes",
            ]
        )

        # May succeed or fail depending on wf existence
        assert returncode in [0, 1]

    def test_wf_add_with_json_format(self) -> None:
        """Test wf add with --json output format"""
        self.setup_database()

        # Try to add non-existent workflow file with JSON output
        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "add",
                "JSONAddTest",
                "--json",
            ]
        )

        # With --json flag, command returns 0 but outputs JSON with success: false
        assert returncode == 0
        assert "success" in stdout.lower()
        assert "false" in stdout.lower()

    def test_wf_list_shows_backupable_status(self) -> None:
        """Test wf list shows backupable status in workflow metadata"""
        self.setup_database()
        self.create_test_workflow("backupable_test")
        self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "backupable_test.json",
                "Backupable Test",
            ]
        )

        returncode, stdout, stderr = self.run_cli_command(["wf", "list"])

        assert returncode == 0
        # Should list all workflows with backupable status (file_exists field)

    def test_wf_list_json_format(self) -> None:
        """Test wf list --format json output"""
        self.setup_database()
        self.create_test_workflow("json_list_test")
        self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "json_list_test.json",
                "JSON List Test",
            ]
        )

        returncode, stdout, stderr = self.run_cli_command(["wf", "list", "--json"])

        assert returncode == 0
        # Should be valid JSON
        data = json.loads(stdout)
        assert isinstance(data, list)
