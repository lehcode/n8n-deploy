#!/usr/bin/env python3
"""Unit tests for wf push CLI command."""

import importlib
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Import the module using importlib to avoid shadowing by __init__.py
push_module = importlib.import_module("api.cli.wf.push")


class TestPushResult:
    """Tests for PushResult dataclass."""

    def test_push_result_creation(self) -> None:
        """Test PushResult dataclass creation."""
        result = push_module.PushResult(workflow_id="wf123", success=True, message="Pushed successfully")
        assert result.workflow_id == "wf123"
        assert result.success is True
        assert result.message == "Pushed successfully"


class TestOutputPushSummary:
    """Tests for _output_push_summary function."""

    def test_single_workflow_success(self) -> None:
        """Test summary output for single successful workflow."""
        results = [push_module.PushResult("wf1", True, "OK")]
        with patch.object(push_module, "console") as mock_console:
            push_module._output_push_summary(results, no_emoji=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "wf1" in call_args
        assert "green" in call_args

    def test_single_workflow_failure(self) -> None:
        """Test summary output for single failed workflow."""
        results = [push_module.PushResult("wf1", False, "Network error")]
        with patch.object(push_module, "console") as mock_console:
            push_module._output_push_summary(results, no_emoji=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "wf1" in call_args
        assert "Network error" in call_args
        assert "red" in call_args

    def test_multiple_workflows_all_success(self) -> None:
        """Test summary output for multiple successful workflows."""
        results = [
            push_module.PushResult("wf1", True, "OK"),
            push_module.PushResult("wf2", True, "OK"),
            push_module.PushResult("wf3", True, "OK"),
        ]
        with patch.object(push_module, "console") as mock_console:
            push_module._output_push_summary(results, no_emoji=False)

        # Should have multiple prints (header, 3 results, blank line, summary)
        assert mock_console.print.call_count >= 5
        all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "wf1" in all_output
        assert "wf2" in all_output
        assert "wf3" in all_output
        assert "3" in all_output  # "All 3 workflow(s)"

    def test_multiple_workflows_partial_failure(self) -> None:
        """Test summary output for partial failure."""
        results = [
            push_module.PushResult("wf1", True, "OK"),
            push_module.PushResult("wf2", False, "Error"),
            push_module.PushResult("wf3", True, "OK"),
        ]
        with patch.object(push_module, "console") as mock_console:
            push_module._output_push_summary(results, no_emoji=False)

        all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "2 succeeded" in all_output or "succeeded" in all_output
        assert "1 failed" in all_output or "failed" in all_output

    def test_multiple_workflows_all_fail(self) -> None:
        """Test summary output when all workflows fail."""
        results = [
            push_module.PushResult("wf1", False, "Error 1"),
            push_module.PushResult("wf2", False, "Error 2"),
        ]
        with patch.object(push_module, "console") as mock_console:
            push_module._output_push_summary(results, no_emoji=False)

        all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "2" in all_output  # "All 2 workflow(s) failed"

    def test_no_emoji_output(self) -> None:
        """Test summary output with --no-emoji flag."""
        results = [
            push_module.PushResult("wf1", True, "OK"),
            push_module.PushResult("wf2", True, "OK"),
        ]
        with patch.object(push_module, "console") as mock_console:
            push_module._output_push_summary(results, no_emoji=True)

        all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
        # Should use [OK] instead of color formatting
        assert "[OK]" in all_output
        # Should not contain rich color markup
        assert "[green]" not in all_output


class TestPushCommand:
    """Tests for push CLI command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click test runner."""
        return CliRunner()

    def test_single_workflow_success(self, runner: CliRunner) -> None:
        """Test single workflow push succeeds."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = True

                result = runner.invoke(push_module.push, ["wf1", "--data-dir", "/tmp"])

        assert result.exit_code == 0
        assert "wf1" in result.output

    def test_single_workflow_failure(self, runner: CliRunner) -> None:
        """Test single workflow push fails."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = False

                result = runner.invoke(push_module.push, ["wf1", "--data-dir", "/tmp"])

        assert result.exit_code != 0
        assert "wf1" in result.output

    def test_multiple_workflows_all_succeed(self, runner: CliRunner) -> None:
        """Test multiple workflows all succeed."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = True

                result = runner.invoke(push_module.push, ["wf1", "wf2", "wf3", "--data-dir", "/tmp"])

        assert result.exit_code == 0
        assert "wf1" in result.output
        assert "wf2" in result.output
        assert "wf3" in result.output
        assert "All 3" in result.output

    def test_multiple_workflows_partial_failure(self, runner: CliRunner) -> None:
        """Test partial failure returns non-zero exit code."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                # First and third succeed, second fails
                mock_api.return_value.push_workflow.side_effect = [True, False, True]

                result = runner.invoke(push_module.push, ["wf1", "wf2", "wf3", "--data-dir", "/tmp"])

        assert result.exit_code != 0
        assert "2 succeeded" in result.output
        assert "1 failed" in result.output

    def test_multiple_workflows_all_fail(self, runner: CliRunner) -> None:
        """Test all failures returns non-zero exit code."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = False

                result = runner.invoke(push_module.push, ["wf1", "wf2", "--data-dir", "/tmp"])

        assert result.exit_code != 0
        assert "All 2" in result.output and "failed" in result.output

    def test_no_workflows_error(self, runner: CliRunner) -> None:
        """Test error when no workflow IDs provided."""
        result = runner.invoke(push_module.push, ["--data-dir", "/tmp"])

        # nargs=-1 with required=True should error
        assert result.exit_code != 0

    def test_progress_indicator_shown(self, runner: CliRunner) -> None:
        """Test progress indicator shown for multiple workflows."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = True

                result = runner.invoke(push_module.push, ["wf1", "wf2", "wf3", "--data-dir", "/tmp"])

        assert "[1/3]" in result.output
        assert "[2/3]" in result.output
        assert "[3/3]" in result.output

    def test_exception_continues_processing(self, runner: CliRunner) -> None:
        """Test that exception on one workflow doesn't stop others."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.side_effect = [True, Exception("Network error"), True]

                result = runner.invoke(push_module.push, ["wf1", "wf2", "wf3", "--data-dir", "/tmp"])

        # Should process all 3
        assert "[1/3]" in result.output
        assert "[2/3]" in result.output
        assert "[3/3]" in result.output
        # Should show 2 succeeded, 1 failed
        assert "2 succeeded" in result.output

    def test_no_emoji_output(self, runner: CliRunner) -> None:
        """Test --no-emoji produces plain text output."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = True

                result = runner.invoke(push_module.push, ["wf1", "wf2", "--data-dir", "/tmp", "--no-emoji"])

        assert result.exit_code == 0
        assert "[OK]" in result.output
        # Rich color codes should not be present in plain text
        assert "\x1b[" not in result.output

    def test_remote_option_passed(self, runner: CliRunner) -> None:
        """Test --remote option is passed to WorkflowApi."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = True

                runner.invoke(push_module.push, ["wf1", "--data-dir", "/tmp", "--remote", "staging"])

        mock_api.assert_called_once()
        call_kwargs = mock_api.call_args[1]
        assert call_kwargs["remote"] == "staging"

    def test_skip_ssl_verify_option_passed(self, runner: CliRunner) -> None:
        """Test --skip-ssl-verify option is passed to WorkflowApi."""
        with patch.object(push_module, "get_config") as mock_config:
            with patch.object(push_module, "WorkflowApi") as mock_api:
                mock_config.return_value = MagicMock()
                mock_api.return_value.push_workflow.return_value = True

                runner.invoke(push_module.push, ["wf1", "--data-dir", "/tmp", "--skip-ssl-verify"])

        mock_api.assert_called_once()
        call_kwargs = mock_api.call_args[1]
        assert call_kwargs["skip_ssl_verify"] is True
