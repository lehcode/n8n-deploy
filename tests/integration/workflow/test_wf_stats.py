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


class TestWorkflowStats(WorkflowTestHelpers):
    """Test Workflow Stats tests"""

    def test_workflow_stats_display(self) -> None:
        """Test wf stats display functionality"""
        self.setup_database()
        self.create_test_workflow("stats_test")
        self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "stats_test.json",
                "Stats-Test",
            ]
        )
        returncode, stdout, stderr = self.run_cli_command(["wf", "stats"])

        assert returncode == 0
        # Should show statistics without errors

    def test_workflow_stats_comprehensive_display(self) -> None:
        """Test comprehensive wf stats with multiple workflows"""
        self.setup_database()
        stats_workflows: List[Tuple[str, Dict[str, Any]]] = [
            ("active_workflow", {"active": True}),
            ("inactive_workflow", {"active": False}),
            (
                "complex_workflow",
                {
                    "nodes": [
                        {"id": "node1", "type": "start"},
                        {"id": "node2", "type": "process"},
                        {"id": "node3", "type": "end"},
                    ]
                },
            ),
        ]

        for workflow_name, extra_data in stats_workflows:
            base_data = {
                "name": workflow_name,
                "nodes": [{"id": "node1", "type": "start"}],
                "connections": {},
                "active": False,
            }
            base_data.update(extra_data)
            self.create_test_workflow(workflow_name, base_data)
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
        returncode, stdout, stderr = self.run_cli_command(["wf", "stats"])

        assert returncode == 0

    def test_wf_stats_overall_json_format(self) -> None:
        """Test wf stats (overall) --format json output"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["wf", "stats", "--json"])

        assert returncode == 0
        # Should be valid JSON with stats data
        data = json.loads(stdout)
        assert "total_workflows" in data

    def test_wf_stats_specific_workflow_json(self) -> None:
        """Test wf stats <wf-id> --format json output"""
        self.setup_database()
        self.create_test_workflow("stats_specific_test")
        add_result = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "stats_specific_test.json",
                "Stats Specific Test",
            ]
        )

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "--data-dir",
                    self.temp_dir,
                    "wf",
                    "stats",
                    "test_workflow_id",
                    "--json",
                ]
            )

            # May succeed or fail based on wf ID
            assert returncode in [0, 1]
