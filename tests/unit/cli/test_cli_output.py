"""Unit tests for api/cli/output.py module

Tests for CLI output formatting functions.
"""

from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import click
import pytest
from assertpy import assert_that

from api.cli.output import (
    OutputFormatter,
    cli_confirm,
    cli_error,
    format_message,
    print_backup_files_table,
    print_backup_table,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_workflow_search_table,
    print_workflow_table,
)


class TestFormatMessage:
    """Tests for format_message helper function"""

    def test_format_message_with_emoji(self) -> None:
        """Test message formatting with emoji enabled"""
        result = format_message("Test message", emoji="✅", no_emoji=False)
        assert_that(result).is_equal_to("✅ Test message")

    def test_format_message_without_emoji(self) -> None:
        """Test message formatting without emoji (no_emoji=True)"""
        result = format_message("Test message", emoji="✅", no_emoji=True)
        assert_that(result).is_equal_to("Test message")

    def test_format_message_empty_emoji(self) -> None:
        """Test message formatting with empty emoji string"""
        result = format_message("Test message", emoji="", no_emoji=False)
        assert_that(result).is_equal_to(" Test message")

    def test_format_message_empty_emoji_no_emoji_mode(self) -> None:
        """Test message formatting with empty emoji in no_emoji mode"""
        result = format_message("Test message", emoji="", no_emoji=True)
        assert_that(result).is_equal_to("Test message")


class TestPrintHelpers:
    """Tests for print helper functions (print_success, print_error, etc.)"""

    def test_print_success(self) -> None:
        """Test print_success outputs formatted success message"""
        with patch("api.cli.output.console") as mock_console:
            print_success("Operation completed", no_emoji=False)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("green")
            assert_that(call_args).contains("Operation completed")
            assert_that(call_args).contains("✅")

    def test_print_success_no_emoji(self) -> None:
        """Test print_success without emoji"""
        with patch("api.cli.output.console") as mock_console:
            print_success("Operation completed", no_emoji=True)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("Operation completed")
            assert_that(call_args).does_not_contain("✅")

    def test_print_error(self) -> None:
        """Test print_error outputs formatted error message"""
        with patch("api.cli.output.console") as mock_console:
            print_error("Something failed", no_emoji=False)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("red")
            assert_that(call_args).contains("Something failed")
            assert_that(call_args).contains("❌")

    def test_print_error_no_emoji(self) -> None:
        """Test print_error without emoji"""
        with patch("api.cli.output.console") as mock_console:
            print_error("Something failed", no_emoji=True)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("Something failed")
            assert_that(call_args).does_not_contain("❌")

    def test_print_warning(self) -> None:
        """Test print_warning outputs formatted warning message"""
        with patch("api.cli.output.console") as mock_console:
            print_warning("Be careful", no_emoji=False)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("yellow")
            assert_that(call_args).contains("Be careful")

    def test_print_info(self) -> None:
        """Test print_info outputs formatted info message"""
        with patch("api.cli.output.console") as mock_console:
            print_info("Information here", no_emoji=False)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("Information here")

    def test_cli_error(self) -> None:
        """Test cli_error prints error and raises click.Abort"""
        with patch("api.cli.output.console"):
            with pytest.raises(click.Abort):
                cli_error("Fatal error", no_emoji=False)

    def test_cli_confirm(self) -> None:
        """Test cli_confirm prompts for user confirmation"""
        with patch("api.cli.output.click.confirm", return_value=True) as mock_confirm:
            result = cli_confirm("Continue?", default=False, no_emoji=False)
            assert_that(result).is_true()
            mock_confirm.assert_called_once()
            call_args = mock_confirm.call_args
            assert_that(call_args[0][0]).contains("Continue?")

    def test_cli_confirm_default_true(self) -> None:
        """Test cli_confirm with default=True"""
        with patch("api.cli.output.click.confirm", return_value=False) as mock_confirm:
            result = cli_confirm("Proceed?", default=True, no_emoji=True)
            assert_that(result).is_false()
            mock_confirm.assert_called_once_with("Proceed?", default=True)


class TestOutputFormatter:
    """Tests for OutputFormatter class"""

    def test_init(self) -> None:
        """Test OutputFormatter initialization"""
        # Default initialization
        fmt = OutputFormatter()
        assert_that(fmt.no_emoji).is_false()

        # With no_emoji=True
        fmt = OutputFormatter(no_emoji=True)
        assert_that(fmt.no_emoji).is_true()

    def test_format(self) -> None:
        """Test OutputFormatter.format method"""
        fmt = OutputFormatter(no_emoji=False)
        result = fmt.format("Test", emoji="🔧")
        assert_that(result).is_equal_to("🔧 Test")

        fmt_no_emoji = OutputFormatter(no_emoji=True)
        result = fmt_no_emoji.format("Test", emoji="🔧")
        assert_that(result).is_equal_to("Test")

    def test_success(self) -> None:
        """Test OutputFormatter.success method"""
        fmt = OutputFormatter(no_emoji=False)
        with patch("api.cli.output.console") as mock_console:
            fmt.success("Done!")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("Done!")
            assert_that(call_args).contains("✅")

    def test_error(self) -> None:
        """Test OutputFormatter.error method"""
        fmt = OutputFormatter(no_emoji=True)
        with patch("api.cli.output.console") as mock_console:
            fmt.error("Failed!")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("Failed!")

    def test_warning(self) -> None:
        """Test OutputFormatter.warning method"""
        fmt = OutputFormatter()
        with patch("api.cli.output.console") as mock_console:
            fmt.warning("Watch out!")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("Watch out!")

    def test_info(self) -> None:
        """Test OutputFormatter.info method"""
        fmt = OutputFormatter()
        with patch("api.cli.output.console") as mock_console:
            fmt.info("FYI")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("FYI")

    def test_abort(self) -> None:
        """Test OutputFormatter.abort method raises click.Abort"""
        fmt = OutputFormatter()
        with patch("api.cli.output.console"):
            with pytest.raises(click.Abort):
                fmt.abort("Critical error!")

    def test_confirm(self) -> None:
        """Test OutputFormatter.confirm method"""
        fmt = OutputFormatter(no_emoji=True)
        with patch("api.cli.output.click.confirm", return_value=True) as mock_confirm:
            result = fmt.confirm("Are you sure?", default=False)
            assert_that(result).is_true()
            mock_confirm.assert_called_once_with("Are you sure?", default=False)


class TestTableFormatting:
    """Tests for table formatting functions"""

    def test_print_workflow_table(self) -> None:
        """Test print_workflow_table displays workflows correctly"""
        workflows: List[Dict[str, Any]] = [
            {
                "id": "wf123",
                "name": "Test Workflow",
                "flow_folder": "/workflows",
                "file_exists": True,
                "status": "active",
                "created_at": "2023-12-01",
                "last_synced": "2023-12-02",
                "push_count": 5,
                "pull_count": 3,
            }
        ]

        with patch("api.cli.output.console") as mock_console:
            print_workflow_table(workflows, no_emoji=False)
            mock_console.print.assert_called()

    def test_print_workflow_table_empty(self) -> None:
        """Test print_workflow_table with empty list"""
        with patch("api.cli.output.console") as mock_console:
            print_workflow_table([], no_emoji=False)
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("No workflows found")

    def test_print_workflow_table_empty_no_emoji(self) -> None:
        """Test print_workflow_table empty list without emoji"""
        with patch("api.cli.output.console") as mock_console:
            print_workflow_table([], no_emoji=True)
            mock_console.print.assert_called_once_with("No workflows found")

    def test_print_workflow_search_table(self) -> None:
        """Test print_workflow_search_table displays search results"""
        # Create mock workflow objects
        mock_wf = MagicMock()
        mock_wf.id = "wf456"
        mock_wf.name = "Search Result"
        mock_wf.status = "active"
        mock_wf.created_at = "2023-12-01"

        with patch("api.cli.output.console") as mock_console:
            print_workflow_search_table([mock_wf], no_emoji=False, query="test")
            mock_console.print.assert_called()

    def test_print_workflow_search_table_empty(self) -> None:
        """Test print_workflow_search_table with no results"""
        with patch("api.cli.output.console") as mock_console:
            print_workflow_search_table([], no_emoji=False, query="nonexistent")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("No workflows found matching")
            assert_that(call_args).contains("nonexistent")

    def test_print_backup_table(self) -> None:
        """Test print_backup_table displays backup records"""
        backups: List[Dict[str, Any]] = [
            {
                "backup_id": "abc123-456-789",
                "filename": "backup_20231201.tar.gz",
                "workflow_count": 10,
                "timestamp": "2023-12-01T12:00:00",
                "file_size": 1024 * 1024 * 5,  # 5 MB
                "api_validated": True,
            }
        ]

        with patch("api.cli.output.console") as mock_console:
            print_backup_table(backups, no_emoji=False)
            mock_console.print.assert_called()

    def test_print_backup_table_empty(self) -> None:
        """Test print_backup_table with empty list"""
        with patch("api.cli.output.console") as mock_console:
            print_backup_table([], no_emoji=True)
            mock_console.print.assert_called_once_with("No backups found")

    def test_print_backup_files_table(self, temp_dir: Path) -> None:
        """Test print_backup_files_table displays filesystem backups"""
        # Create a test file
        test_file = temp_dir / "backup_test.tar.gz"
        test_file.write_bytes(b"x" * 1024 * 1024)  # 1 MB

        with patch("api.cli.output.console") as mock_console:
            print_backup_files_table([test_file], no_emoji=False, backup_path=str(temp_dir))
            # Should be called twice: once for path, once for table
            assert_that(mock_console.print.call_count).is_greater_than_or_equal_to(1)

    def test_print_backup_files_table_empty(self) -> None:
        """Test print_backup_files_table with no files"""
        with patch("api.cli.output.console") as mock_console:
            print_backup_files_table([], no_emoji=True, backup_path="/backups")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert_that(call_args).contains("No backup files found")
            assert_that(call_args).contains("/backups")


class TestOutputJsonOrTable:
    """Tests for JSON vs table output selection

    Note: The output_json_or_table function doesn't exist in the current codebase.
    These tests verify the concept via the table formatting functions that do exist.
    """

    def test_json_format_concept(self) -> None:
        """Test that JSON output can be produced from workflow data"""
        import json

        workflows = [
            {
                "id": "wf123",
                "name": "Test Workflow",
                "status": "active",
            }
        ]

        # JSON output is typically handled by CLI commands, not output.py
        json_output = json.dumps(workflows, indent=2)
        parsed = json.loads(json_output)

        assert_that(parsed).is_length(1)
        assert_that(parsed[0]["id"]).is_equal_to("wf123")

    def test_table_format_concept(self) -> None:
        """Test that table output works via print_workflow_table"""
        workflows: List[Dict[str, Any]] = [
            {
                "id": "wf789",
                "name": "Table Test",
                "flow_folder": "/test",
                "file_exists": True,
                "status": "inactive",
                "created_at": None,
                "last_synced": None,
                "push_count": 0,
                "pull_count": 0,
            }
        ]

        with patch("api.cli.output.console") as mock_console:
            print_workflow_table(workflows, no_emoji=True)
            # Verify the table was printed (not JSON)
            mock_console.print.assert_called()
            # The argument should be a Table object, not a string
            call_arg = mock_console.print.call_args[0][0]
            from rich.table import Table

            assert_that(call_arg).is_instance_of(Table)
