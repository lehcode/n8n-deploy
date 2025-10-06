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


class TestWorkflowIntegration(WorkflowTestHelpers):
    """Test Workflow Integration tests"""

    def test_workflow_type_classification(self) -> None:
        """Test wf search handles different wf name patterns"""
        self.setup_database()
        workflow_names = [
            "api_workflow",
            "scheduled_workflow",
            "manual_workflow",
        ]

        for name in workflow_names:
            # Test that search command handles different naming patterns
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "--data-dir",
                    self.temp_dir,
                    "wf",
                    "search",
                    name,
                ]
            )

            # Should succeed (returns 0 even with no results)
            assert returncode == 0

    def test_workflow_environment_variable_integration(self) -> None:
        """Test wf operations respect environment variables"""
        self.setup_database()
        env = {"N8N_DEPLOY_FLOWS_DIR": self.temp_flow_dir}

        # Test that search command uses environment variable for flow directory
        returncode, stdout, stderr = self.run_cli_command(["wf", "list"], env=env)

        # Should use environment variable for flow directory and succeed
        assert returncode == 0
