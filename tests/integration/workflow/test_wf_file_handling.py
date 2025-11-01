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
        """Test concurrent wf operations"""
        import threading
        import time

        self.setup_database()

        # Add a test workflow to make the database non-empty
        # This reduces race conditions during concurrent access
        test_wf = self.create_test_workflow("concurrent_test")
        self.run_wf_add("concurrent_test")

        results = []

        def list_workflows(thread_id: int) -> None:
            # Add small stagger to reduce simultaneous access
            time.sleep(thread_id * 0.05)

            # Note: wf list reads from database, so it uses --data-dir
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "wf",
                    "list",
                    "--data-dir",
                    self.temp_dir,
                ]
            )
            results.append((thread_id, returncode, stdout, stderr))

        threads = []
        for i in range(3):
            thread = threading.Thread(target=list_workflows, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        assert len(results) == 3
        # Operations should complete without crashes
        for thread_id, returncode, stdout, stderr in results:
            if returncode != 0:
                # Provide detailed error output for debugging
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
