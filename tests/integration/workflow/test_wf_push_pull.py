#!/usr/bin/env python3
"""Integration tests for wf push/pull multi-workflow functionality."""

from typing import Tuple

import pytest

from .conftest import WorkflowTestHelpers


class TestWfPushMultiWorkflow(WorkflowTestHelpers):
    """Integration tests for multi-workflow push."""

    def _init_db(self) -> Tuple[int, str, str]:
        """Initialize database for tests."""
        return self.run_cli_command(["db", "init", "--no-emoji"])

    @pytest.fixture(autouse=True)
    def setup_test_env(self, setup_test_environment: None) -> None:
        """Set up test environment for each test."""
        self._init_db()

    def test_push_multiple_workflows_cli_syntax(self) -> None:
        """Test CLI accepts multiple workflow arguments."""
        # Create test workflows
        self.create_test_workflow("push_multi_test_1")
        self.create_test_workflow("push_multi_test_2")

        # Add to database
        self.run_wf_add("push_multi_test_1.json", flow_dir=self.temp_flow_dir)
        self.run_wf_add("push_multi_test_2.json", flow_dir=self.temp_flow_dir)

        # Test CLI argument parsing (will fail server connection but confirms syntax works)
        returncode, stdout, stderr = self.run_wf_push(
            ["push_multi_test_1", "push_multi_test_2"],
            flow_dir=self.temp_flow_dir,
            no_emoji=True,
        )

        # Should attempt both workflows (syntax accepted)
        combined = stdout + stderr
        assert "push_multi_test_1" in combined
        assert "push_multi_test_2" in combined
        # Progress indicators should appear
        assert "[1/2]" in combined
        assert "[2/2]" in combined

    def test_push_summary_output_format(self) -> None:
        """Test summary output format for multiple workflows."""
        # Create test workflows
        self.create_test_workflow("push_summary_1")
        self.create_test_workflow("push_summary_2")

        self.run_wf_add("push_summary_1.json", flow_dir=self.temp_flow_dir)
        self.run_wf_add("push_summary_2.json", flow_dir=self.temp_flow_dir)

        returncode, stdout, stderr = self.run_wf_push(
            ["push_summary_1", "push_summary_2"],
            flow_dir=self.temp_flow_dir,
            no_emoji=True,
        )

        combined = stdout + stderr
        # Should have summary section
        assert "Push Summary" in combined or "Summary" in combined

    def test_push_single_workflow_backwards_compatible(self) -> None:
        """Test single workflow push still works."""
        self.create_test_workflow("push_single_test")
        self.run_wf_add("push_single_test.json", flow_dir=self.temp_flow_dir)

        returncode, stdout, stderr = self.run_wf_push(
            ["push_single_test"],
            flow_dir=self.temp_flow_dir,
            no_emoji=True,
        )

        combined = stdout + stderr
        assert "push_single_test" in combined
        # Should NOT have progress indicator for single workflow
        assert "[1/1]" not in combined


class TestWfPullMultiWorkflow(WorkflowTestHelpers):
    """Integration tests for multi-workflow pull."""

    def _init_db(self) -> Tuple[int, str, str]:
        """Initialize database for tests."""
        return self.run_cli_command(["db", "init", "--no-emoji"])

    @pytest.fixture(autouse=True)
    def setup_test_env(self, setup_test_environment: None) -> None:
        """Set up test environment for each test."""
        self._init_db()

    def test_pull_multiple_workflows_cli_syntax(self) -> None:
        """Test CLI accepts multiple workflow arguments for pull."""
        # Create workflows in database first
        self.create_test_workflow("pull_multi_test_1")
        self.create_test_workflow("pull_multi_test_2")
        self.run_wf_add("pull_multi_test_1.json", flow_dir=self.temp_flow_dir)
        self.run_wf_add("pull_multi_test_2.json", flow_dir=self.temp_flow_dir)

        # Test CLI argument parsing
        returncode, stdout, stderr = self.run_wf_pull(
            ["pull_multi_test_1", "pull_multi_test_2"],
            flow_dir=self.temp_flow_dir,
            non_interactive=True,
            no_emoji=True,
        )

        combined = stdout + stderr
        assert "pull_multi_test_1" in combined
        assert "pull_multi_test_2" in combined
        # Progress indicators should appear
        assert "[1/2]" in combined
        assert "[2/2]" in combined

    def test_pull_summary_output_format(self) -> None:
        """Test summary output format for multiple workflows."""
        self.create_test_workflow("pull_summary_1")
        self.create_test_workflow("pull_summary_2")
        self.run_wf_add("pull_summary_1.json", flow_dir=self.temp_flow_dir)
        self.run_wf_add("pull_summary_2.json", flow_dir=self.temp_flow_dir)

        returncode, stdout, stderr = self.run_wf_pull(
            ["pull_summary_1", "pull_summary_2"],
            flow_dir=self.temp_flow_dir,
            non_interactive=True,
            no_emoji=True,
        )

        combined = stdout + stderr
        assert "Pull Summary" in combined or "Summary" in combined

    def test_pull_filename_warning_for_multiple(self) -> None:
        """Test warning when --filename used with multiple workflows."""
        self.create_test_workflow("pull_fn_warn_1")
        self.create_test_workflow("pull_fn_warn_2")
        self.run_wf_add("pull_fn_warn_1.json", flow_dir=self.temp_flow_dir)
        self.run_wf_add("pull_fn_warn_2.json", flow_dir=self.temp_flow_dir)

        # Run with --filename and multiple workflows
        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "pull",
                "pull_fn_warn_1",
                "pull_fn_warn_2",
                "--flow-dir",
                self.temp_flow_dir,
                "--filename",
                "custom.json",
                "--non-interactive",
                "--no-emoji",
            ]
        )

        combined = stdout + stderr
        assert "Warning" in combined
        assert "--filename ignored" in combined

    def test_pull_single_workflow_backwards_compatible(self) -> None:
        """Test single workflow pull still works."""
        self.create_test_workflow("pull_single_test")
        self.run_wf_add("pull_single_test.json", flow_dir=self.temp_flow_dir)

        returncode, stdout, stderr = self.run_wf_pull(
            ["pull_single_test"],
            flow_dir=self.temp_flow_dir,
            non_interactive=True,
            no_emoji=True,
        )

        combined = stdout + stderr
        assert "pull_single_test" in combined
        # Should NOT have progress indicator for single workflow
        assert "[1/1]" not in combined
