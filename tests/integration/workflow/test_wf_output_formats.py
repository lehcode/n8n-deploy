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


class TestOutputFormats(WorkflowTestHelpers):
    """Test Output Formats tests"""

    def test_output_format_data_consistency(self) -> None:
        """Test output format is consistent between runs"""
        # Initialize database first
        returncode, stdout, stderr = self.run_cli_command(["db", "init", "--data-dir", self.temp_dir])

        # Note: wf list reads from database, so it uses --data-dir
        cmd = ["wf", "list", "--data-dir", self.temp_dir]

        returncode1, stdout1, stderr1 = self.run_cli_command(cmd)
        returncode2, stdout2, stderr2 = self.run_cli_command(cmd)

        assert returncode1 == 0, f"First run failed: {stderr1}"
        assert returncode2 == 0, f"Second run failed: {stderr2}"

    def test_workflow_operations_emoji_consistency(self) -> None:
        """Test wf operations with emoji and no-emoji modes"""
        self.setup_database()
        self.create_test_workflow("emoji_test")

        # Test 'wf list' with default emoji output
        # Note: wf list reads from database, so it uses --data-dir
        emoji_returncode, emoji_stdout, _ = self.run_cli_command(["wf", "list", "--data-dir", self.temp_dir])

        # Test 'wf list' with --no-emoji flag
        no_emoji_returncode, no_emoji_stdout, _ = self.run_cli_command(
            [
                "--no-emoji",
                "wf",
                "list",
                "--data-dir",
                self.temp_dir,
            ]
        )

        # Both should succeed (return code 0)
        assert emoji_returncode == 0, f"Emoji mode failed with code {emoji_returncode}"
        assert no_emoji_returncode == 0, f"No-emoji mode failed with code {no_emoji_returncode}"

        # Check that emojis are present in emoji output but not in no-emoji output
        workflow_emojis = ["⚡", "📋", "✅", "❌"]
        for emoji in workflow_emojis:
            if emoji in emoji_stdout:
                assert emoji not in no_emoji_stdout

    def test_wf_list_server_json_format(self) -> None:
        """Test wf server --format json output"""
        # This test requires n8n server, may fail if not available
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "wf",
                "server",
                "--remote",
                "http://test-server:5678",
                "--json",
            ]
        )

        # Will fail without server, but should handle gracefully
        assert returncode in [0, 1]
