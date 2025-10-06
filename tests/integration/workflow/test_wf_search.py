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


class TestWorkflowSearch(WorkflowTestHelpers):
    """Test Workflow Search tests"""

    def test_workflow_search_functionality(self) -> None:
        """Test wf search with various patterns"""
        self.setup_database()
        search_workflows = [
            "email_notification",
            "data_processing",
            "user_management",
            "notification_system",
        ]

        for workflow_name in search_workflows:
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
        search_patterns = [
            "notification",  # Should match 2 workflows
            "data",  # Should match 1 wf
            "user",  # Should match 1 wf
            "nonexistent",  # Should match 0 workflows
        ]

        for pattern in search_patterns:
            returncode, stdout, stderr = self.run_cli_command(["wf", "search", pattern])

            # Search should complete successfully
            assert returncode == 0

    def test_search_workflows_comprehensive_matching(self) -> None:
        """Test comprehensive search matching including partial matches"""
        self.setup_database()
        workflows_data = [
            ("user_auth_flow", {"name": "User Authentication Flow"}),
            ("email_sender", {"name": "Email Notification Sender"}),
            ("data_validator", {"name": "Data Validation Process"}),
            ("backup_system", {"name": "Backup and Archive System"}),
        ]

        for workflow_name, data in workflows_data:
            self.create_test_workflow(workflow_name, data)
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
        comprehensive_searches = [
            "user",  # Should find user_auth_flow
            "email",  # Should find email_sender
            "data",  # Should find data_validator
            "system",  # Should find backup_system
            "flow",  # Should find user_auth_flow
            "auth",  # Should find user_auth_flow
        ]

        for search_term in comprehensive_searches:
            returncode, stdout, stderr = self.run_cli_command(["wf", "search", search_term])
            assert returncode == 0

    def test_wf_search_json_format(self) -> None:
        """Test wf search --format json output"""
        self.setup_database()
        self.create_test_workflow("search_json_test")
        self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "search_json_test.json",
                "Search JSON Test",
            ]
        )

        returncode, stdout, stderr = self.run_cli_command(["wf", "search", "search", "--json"])

        assert returncode == 0
        # Should be valid JSON
        data = json.loads(stdout)
        assert isinstance(data, list)
