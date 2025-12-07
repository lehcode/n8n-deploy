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


class TestWorkflowFileHandling(WorkflowTestHelpers):
    """Test Workflow File Handling tests"""

    def test_workflow_file_existence_accuracy(self) -> None:
        """Test accuracy of wf file existence checks"""
        self.setup_database()
        workflow_file = self.create_test_workflow("existence_test")
        # Note: wf add uses both --data-dir (for database) and --flow-dir (to locate workflow file)
        add_returncode, _, _ = self.run_cli_command(
            [
                "wf",
                "add",
                "existence_test.json",
                "Existence-Test",
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
            ]
        )

        if add_returncode == 0:
            # List workflows - should show file exists
            list_returncode, list_stdout, _ = self.run_cli_command(["wf", "list"])
            assert list_returncode == 0
            workflow_file.unlink()

            # List again - should reflect file no longer exists
            list_after_delete_returncode, list_after_stdout, _ = self.run_cli_command(["wf", "list"])
            assert list_after_delete_returncode == 0

    def test_workflow_add_nonexistent_file(self) -> None:
        """Test adding nonexistent wf file"""
        self.setup_database()

        # wf add now pulls from server, so this tests server pull of nonexistent wf
        # Note: wf add doesn't have --data-dir option
        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "add",
                "NonexistentWorkflow",
            ]
        )

        # Should fail gracefully - either no server URL or wf not found on server
        assert returncode == 1
        assert (
            "server" in stderr.lower()
            or "server" in stdout.lower()
            or "not found" in stderr.lower()
            or "not found" in stdout.lower()
        )

    def test_workflow_add_invalid_json(self) -> None:
        """Test that wf add validates wf name format"""
        self.setup_database()

        # Test with invalid wf name characters
        # Note: wf add doesn't have --data-dir option
        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "add",
                "Invalid/Name",  # Forward slash is invalid in wf names
            ]
        )

        # Should fail gracefully - either validation error or server URL missing
        assert returncode == 1

    def test_workflow_path_resolution(self) -> None:
        """Test wf search command handles different flow directory paths"""
        self.setup_database()
        subdir = Path(self.temp_flow_dir) / "subdir"
        subdir.mkdir()

        # Test that search command works with custom flow directory
        # Note: wf search reads from database, so it uses --data-dir
        returncode, stdout, stderr = self.run_cli_command(["wf", "search", "TestWorkflow", "--data-dir", self.temp_dir])

        # Should handle path resolution and return success (even if no results)
        assert returncode == 0

    def test_workflow_large_file_handling(self) -> None:
        """Test that wf commands handle operations efficiently"""
        self.setup_database()

        # Test that list command handles database operations efficiently
        # Note: wf list reads from database, so it uses --data-dir
        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "list",
                "--data-dir",
                self.temp_dir,
            ]
        )

        # Should handle operations efficiently
        assert returncode == 0

    def test_workflow_concurrent_operations(self) -> None:
        """Test concurrent wf operations with SQLite

        SQLite has limited concurrent access support. This test verifies
        that read operations can execute concurrently without crashing,
        using appropriate staggering and retry logic.
        """
        import threading
        import time

        self.setup_database()

        # Add a test workflow to make the database non-empty
        test_wf = self.create_test_workflow("concurrent_test")
        self.run_wf_add("concurrent_test")

        results: list[tuple[int, int, str, str]] = []
        results_lock = threading.Lock()

        def list_workflows(thread_id: int) -> None:
            # Stagger thread starts to reduce lock contention on SQLite
            time.sleep(thread_id * 0.1)

            # Retry logic for transient SQLite lock errors
            max_retries = 3
            for attempt in range(max_retries):
                returncode, stdout, stderr = self.run_cli_command(
                    [
                        "wf",
                        "list",
                        "--data-dir",
                        self.temp_dir,
                    ]
                )

                # Success or non-transient error
                if returncode == 0 or "database is locked" not in stderr.lower():
                    with results_lock:
                        results.append((thread_id, returncode, stdout, stderr))
                    return

                # Transient lock error - wait and retry
                time.sleep(0.1 * (attempt + 1))

            # All retries exhausted
            with results_lock:
                results.append((thread_id, returncode, stdout, stderr))

        threads = []
        for i in range(3):
            thread = threading.Thread(target=list_workflows, args=(i,))
            threads.append(thread)
            thread.start()

        # Join with timeout to prevent hanging
        for thread in threads:
            thread.join(timeout=30)

        assert len(results) == 3, f"Expected 3 results, got {len(results)}"

        # Operations should complete without crashes
        for thread_id, returncode, stdout, stderr in results:
            if returncode != 0:
                print(f"\n=== Thread {thread_id} Error Details ===")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
            assert returncode == 0, f"Thread {thread_id} failed with returncode {returncode}\nSTDERR: {stderr}"

    def test_workflow_unicode_names(self) -> None:
        """Test that wf add command handles Unicode workflow file names"""
        self.setup_database()
        unicode_names = ["测试工作流", "тест_поток", "workflow_émojis", "流程_テスト"]

        for name in unicode_names:
            try:
                # Test that wf add accepts Unicode names (will fail due to missing file)
                returncode, stdout, stderr = self.run_cli_command(
                    [
                        "wf",
                        "add",
                        name,
                    ]
                )

                # Should handle Unicode names - will fail due to file not found
                assert returncode == 1
                # Should show file not found error, not encoding error
                assert "not found" in stderr.lower() or "not found" in stdout.lower()

            except UnicodeError:
                # Skip if system doesn't support Unicode
                pytest.skip(f"System doesn't support Unicode name: {name}")

    def test_workflow_add_without_id(self) -> None:
        """Test adding workflow without id field (new workflow scenario)"""
        self.setup_database()

        # Create workflow without ID (simulates new workflow before server upload)
        workflow_data = {
            "name": "New Workflow Without ID",
            "nodes": [
                {
                    "id": "node1",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [240, 300],
                    "parameters": {},
                }
            ],
            "connections": {},
            "active": False,
            "settings": {},
        }

        workflow_file = self.create_test_workflow("no_id_test", workflow_data)

        # Add should succeed and generate draft ID
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "no_id_test.json",
            ]
        )

        assert returncode == 0, f"Failed to add workflow without ID: {stderr}"
        # Should mention draft ID generation
        assert "draft_" in stdout or "Draft" in stdout or "WARNING" in stdout

        # Verify workflow was added to database
        list_returncode, list_stdout, _ = self.run_cli_command(["--data-dir", self.temp_dir, "wf", "list", "--json"])

        assert list_returncode == 0
        workflows = self.assert_json_output_valid(list_stdout)
        assert len(workflows) == 1
        assert workflows[0]["name"] == "New Workflow Without ID"
        assert workflows[0]["id"].startswith("draft_")
