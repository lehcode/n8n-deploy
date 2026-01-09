#!/usr/bin/env python3
"""Unit tests for wf pull CLI command."""

import importlib
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Import the module using importlib to avoid shadowing by __init__.py
pull_module = importlib.import_module("api.cli.wf.pull")


class TestPromptForFilename:
    """Tests for _prompt_for_filename function in non-interactive mode."""

    def test_non_interactive_uses_default_filename(self) -> None:
        """Test that non-interactive mode uses default filename without prompting."""
        with patch.object(pull_module, "is_interactive_mode", return_value=False):
            with patch.object(pull_module, "console") as mock_console:
                result = pull_module._prompt_for_filename("test123", no_emoji=False)

        assert result == "test123.json"
        mock_console.print.assert_called_once()
        assert "test123.json" in mock_console.print.call_args[0][0]

    def test_non_interactive_with_no_emoji(self) -> None:
        """Test non-interactive mode respects no_emoji flag."""
        with patch.object(pull_module, "is_interactive_mode", return_value=False):
            with patch.object(pull_module, "console") as mock_console:
                result = pull_module._prompt_for_filename("wf_abc", no_emoji=True)

        assert result == "wf_abc.json"
        printed_msg = mock_console.print.call_args[0][0]
        # When no_emoji=True, prefix should be empty string
        assert not printed_msg.startswith("Info:")

    def test_interactive_mode_prompts_user(self) -> None:
        """Test that interactive mode prompts the user."""
        with patch.object(pull_module, "is_interactive_mode", return_value=True):
            with patch.object(pull_module, "console"):
                with patch.object(pull_module.click, "prompt", return_value="custom-name") as mock_prompt:
                    result = pull_module._prompt_for_filename("wf123", no_emoji=False)

        mock_prompt.assert_called_once()
        assert result == "custom-name.json"

    def test_interactive_adds_json_extension(self) -> None:
        """Test that .json extension is added if missing."""
        with patch.object(pull_module, "is_interactive_mode", return_value=True):
            with patch.object(pull_module, "console"):
                with patch.object(pull_module.click, "prompt", return_value="my-workflow"):
                    result = pull_module._prompt_for_filename("wf123", no_emoji=False)

        assert result == "my-workflow.json"

    def test_interactive_preserves_json_extension(self) -> None:
        """Test that existing .json extension is not duplicated."""
        with patch.object(pull_module, "is_interactive_mode", return_value=True):
            with patch.object(pull_module, "console"):
                with patch.object(pull_module.click, "prompt", return_value="my-workflow.json"):
                    result = pull_module._prompt_for_filename("wf123", no_emoji=False)

        assert result == "my-workflow.json"


class TestPullResult:
    """Tests for PullResult dataclass."""

    def test_pull_result_creation(self) -> None:
        """Test PullResult dataclass creation."""
        result = pull_module.PullResult(workflow_id="wf123", success=True, message="Pulled successfully")
        assert result.workflow_id == "wf123"
        assert result.success is True
        assert result.message == "Pulled successfully"


class TestOutputPullSummary:
    """Tests for _output_pull_summary function."""

    def test_single_workflow_success(self) -> None:
        """Test summary output for single successful workflow."""
        results = [pull_module.PullResult("wf1", True, "OK")]
        with patch.object(pull_module, "console") as mock_console:
            pull_module._output_pull_summary(results, no_emoji=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "wf1" in call_args
        assert "green" in call_args

    def test_single_workflow_failure(self) -> None:
        """Test summary output for single failed workflow."""
        results = [pull_module.PullResult("wf1", False, "Network error")]
        with patch.object(pull_module, "console") as mock_console:
            pull_module._output_pull_summary(results, no_emoji=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "wf1" in call_args
        assert "Network error" in call_args
        assert "red" in call_args

    def test_multiple_workflows_all_success(self) -> None:
        """Test summary output for multiple successful workflows."""
        results = [
            pull_module.PullResult("wf1", True, "OK"),
            pull_module.PullResult("wf2", True, "OK"),
            pull_module.PullResult("wf3", True, "OK"),
        ]
        with patch.object(pull_module, "console") as mock_console:
            pull_module._output_pull_summary(results, no_emoji=False)

        assert mock_console.print.call_count >= 5
        all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "wf1" in all_output
        assert "wf2" in all_output
        assert "wf3" in all_output
        assert "3" in all_output

    def test_multiple_workflows_partial_failure(self) -> None:
        """Test summary output for partial failure."""
        results = [
            pull_module.PullResult("wf1", True, "OK"),
            pull_module.PullResult("wf2", False, "Error"),
            pull_module.PullResult("wf3", True, "OK"),
        ]
        with patch.object(pull_module, "console") as mock_console:
            pull_module._output_pull_summary(results, no_emoji=False)

        all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "succeeded" in all_output
        assert "failed" in all_output

    def test_no_emoji_output(self) -> None:
        """Test summary output with --no-emoji flag."""
        results = [
            pull_module.PullResult("wf1", True, "OK"),
            pull_module.PullResult("wf2", True, "OK"),
        ]
        with patch.object(pull_module, "console") as mock_console:
            pull_module._output_pull_summary(results, no_emoji=True)

        all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "[OK]" in all_output
        assert "[green]" not in all_output


class TestPullCommand:
    """Tests for pull CLI command with multi-workflow support."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create Click test runner."""
        return CliRunner()

    def test_single_workflow_success(self, runner: CliRunner) -> None:
        """Test single workflow pull succeeds."""
        with patch.object(pull_module, "get_config") as mock_config:
            with patch("api.cli.db.check_database_exists"):
                with patch.object(pull_module, "WorkflowApi") as mock_api:
                    mock_config.return_value = MagicMock()
                    mock_api.return_value.get_workflow_info.return_value = {}
                    mock_api.return_value.pull_workflow.return_value = True

                    result = runner.invoke(pull_module.pull, ["wf1", "--data-dir", "/tmp"])

        assert result.exit_code == 0
        assert "wf1" in result.output

    def test_multiple_workflows_all_succeed(self, runner: CliRunner) -> None:
        """Test multiple workflows all succeed."""
        with patch.object(pull_module, "get_config") as mock_config:
            with patch("api.cli.db.check_database_exists"):
                with patch.object(pull_module, "WorkflowApi") as mock_api:
                    mock_config.return_value = MagicMock()
                    mock_api.return_value.get_workflow_info.return_value = {}
                    mock_api.return_value.pull_workflow.return_value = True

                    result = runner.invoke(pull_module.pull, ["wf1", "wf2", "wf3", "--data-dir", "/tmp"])

        assert result.exit_code == 0
        assert "wf1" in result.output
        assert "wf2" in result.output
        assert "wf3" in result.output
        assert "All 3" in result.output

    def test_multiple_workflows_partial_failure(self, runner: CliRunner) -> None:
        """Test partial failure returns non-zero exit code."""
        with patch.object(pull_module, "get_config") as mock_config:
            with patch("api.cli.db.check_database_exists"):
                with patch.object(pull_module, "WorkflowApi") as mock_api:
                    mock_config.return_value = MagicMock()
                    mock_api.return_value.get_workflow_info.return_value = {}
                    mock_api.return_value.pull_workflow.side_effect = [True, False, True]

                    result = runner.invoke(pull_module.pull, ["wf1", "wf2", "wf3", "--data-dir", "/tmp"])

        assert result.exit_code != 0
        assert "2 succeeded" in result.output
        assert "1 failed" in result.output

    def test_filename_ignored_for_multiple(self, runner: CliRunner) -> None:
        """Test --filename is ignored when pulling multiple workflows."""
        with patch.object(pull_module, "get_config") as mock_config:
            with patch("api.cli.db.check_database_exists"):
                with patch.object(pull_module, "WorkflowApi") as mock_api:
                    mock_config.return_value = MagicMock()
                    mock_api.return_value.get_workflow_info.return_value = {}
                    mock_api.return_value.pull_workflow.return_value = True

                    result = runner.invoke(pull_module.pull, ["wf1", "wf2", "--data-dir", "/tmp", "--filename", "custom.json"])

        assert "Warning" in result.output
        assert "--filename ignored" in result.output

    def test_progress_indicator_shown(self, runner: CliRunner) -> None:
        """Test progress indicator shown for multiple workflows."""
        with patch.object(pull_module, "get_config") as mock_config:
            with patch("api.cli.db.check_database_exists"):
                with patch.object(pull_module, "WorkflowApi") as mock_api:
                    mock_config.return_value = MagicMock()
                    mock_api.return_value.get_workflow_info.return_value = {}
                    mock_api.return_value.pull_workflow.return_value = True

                    result = runner.invoke(pull_module.pull, ["wf1", "wf2", "wf3", "--data-dir", "/tmp"])

        assert "[1/3]" in result.output
        assert "[2/3]" in result.output
        assert "[3/3]" in result.output

    def test_no_prompt_for_multiple_new_workflows(self, runner: CliRunner) -> None:
        """Test no interactive prompt for multiple new workflows."""
        with patch.object(pull_module, "get_config") as mock_config:
            with patch("api.cli.db.check_database_exists"):
                with patch.object(pull_module, "WorkflowApi") as mock_api:
                    with patch.object(pull_module, "is_interactive_mode", return_value=True):
                        mock_config.return_value = MagicMock()
                        # Simulate new workflows (not in database)
                        mock_api.return_value.get_workflow_info.side_effect = ValueError("Not found")
                        mock_api.return_value.pull_workflow.return_value = True

                        result = runner.invoke(pull_module.pull, ["wf1", "wf2", "--data-dir", "/tmp"])

        # Should use default filenames without prompting
        assert "Using default filename" in result.output
        assert result.exit_code == 0

    def test_remote_option_passed(self, runner: CliRunner) -> None:
        """Test --remote option is passed to WorkflowApi."""
        with patch.object(pull_module, "get_config") as mock_config:
            with patch("api.cli.db.check_database_exists"):
                with patch.object(pull_module, "WorkflowApi") as mock_api:
                    mock_config.return_value = MagicMock()
                    mock_api.return_value.get_workflow_info.return_value = {}
                    mock_api.return_value.pull_workflow.return_value = True

                    runner.invoke(pull_module.pull, ["wf1", "--data-dir", "/tmp", "--remote", "staging"])

        mock_api.assert_called_once()
        call_kwargs = mock_api.call_args[1]
        assert call_kwargs["remote"] == "staging"
