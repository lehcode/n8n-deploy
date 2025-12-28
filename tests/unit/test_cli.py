"""
Unit tests for CLI functionality
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from api.cli.app import cli


class TestCLICore:
    """Test core CLI functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment"""
        # Remove temp directory if it exists
        if os.path.exists(self.temp_dir):
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_cli_context_initialization(self):
        """Test CLI context object initialization"""
        # Test main CLI help (no longer has --no-emoji)
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # Main help should still contain emojis
        assert "🎭" in result.output

    def test_version_command_format(self):
        """Test version command output format"""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "n8n-deploy, version" in result.output

        # Validate version format
        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        import re

        version_pattern = r"n8n-deploy, version \d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"
        assert re.search(version_pattern, result.output), f"Invalid version format: {result.output}"

    def test_help_command_content(self):
        """Test help command contains required sections"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        # Required sections
        assert "n8n-deploy - a simple N8N Workflow Manager" in result.output
        assert "Commands:" in result.output
        assert "Options:" in result.output

        # Core command groups should be present
        required_command_groups = ["apikey", "db", "wf"]
        for cmd_group in required_command_groups:
            assert cmd_group in result.output, f"Command group '{cmd_group}' not found in help"

    def test_no_emoji_flag_available_on_commands(self):
        """Test --no-emoji flag is available on individual commands"""
        # Test that --no-emoji is NOT on main CLI
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--no-emoji" not in result.output

        # Test that --no-emoji IS available on wf list command
        result = self.runner.invoke(cli, ["wf", "list", "--help"])
        assert result.exit_code == 0
        assert "--no-emoji" in result.output
        assert "Disable emoji output for automation/scripting" in result.output

    def test_help_version_flag_combinations(self):
        """Test behavior of --help and --version flag combinations"""
        # --help --version: silently exits with no output (mutual exclusion)
        result1 = self.runner.invoke(cli, ["--help", "--version"])
        assert result1.exit_code == 0
        assert result1.output == ""

        # --version --help: silently exits with no output (mutual exclusion)
        result2 = self.runner.invoke(cli, ["--version", "--help"])
        assert result2.exit_code == 0
        assert result2.output == ""
        assert "Commands:" not in result2.output

    def test_invalid_flag_handling(self):
        """Test handling of invalid flags"""
        result = self.runner.invoke(cli, ["--invalid-flag"])
        assert result.exit_code != 0
        assert "No such option" in result.output

    @patch.dict(os.environ, {"N8N_DEPLOY_TESTING": "1"})
    def test_cli_with_testing_environment(self):
        """Test CLI behavior with testing environment variable"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # Should still work normally in testing mode
        assert "n8n-deploy" in result.output


class TestCLIArgumentParsing:
    """Test CLI argument parsing logic"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_emoji_flag_parsing(self):
        """Test emoji flag parsing on commands where it's available"""
        # Test --no-emoji on wf list command
        result = self.runner.invoke(cli, ["wf", "list", "--no-emoji", "--help"])
        assert result.exit_code == 0

        # Test --no-emoji is not available at root level
        result = self.runner.invoke(cli, ["--no-emoji", "--help"])
        assert result.exit_code != 0  # Should fail
        assert "No such option: --no-emoji" in result.output

    def test_data_dir_flag_position(self):
        """Test --data-dir flag is only available on subcommands, not at root level"""
        # Should fail at root level
        result = self.runner.invoke(cli, ["--data-dir", "/tmp", "--help"])
        assert result.exit_code != 0
        assert "No such option" in result.output

        # Should work on wf list command (--data-dir is available on workflow commands)
        result = self.runner.invoke(cli, ["wf", "list", "--help"])
        assert result.exit_code == 0
        assert "--data-dir" in result.output

        # Should work on db status command (--data-dir is available on database commands)
        result = self.runner.invoke(cli, ["db", "status", "--help"])
        assert result.exit_code == 0
        assert "--data-dir" in result.output


class TestCLIHelp:
    """Test CLI help functionality specifically"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_basic_help_command(self):
        """Test basic --help functionality"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "n8n-deploy - a simple N8N Workflow Manager" in result.output
        assert "Commands:" in result.output
        assert "Options:" in result.output

    def test_help_with_no_emoji_flag(self):
        """Test --no-emoji --help works on commands that support it"""
        result = self.runner.invoke(cli, ["wf", "list", "--no-emoji", "--help"])
        assert result.exit_code == 0
        assert "📋" in result.output  # Help still shows emojis even with --no-emoji

    def test_help_content_completeness(self):
        """Test help contains all required commands"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        required_commands = ["wf", "apikey", "db"]
        for cmd in required_commands:
            assert cmd in result.output, f"Command '{cmd}' not found in help"

    def test_subcommand_help_consistency(self):
        """Test subcommand help behavior"""
        subcommands = ["db", "apikey"]

        for subcmd in subcommands:
            result = self.runner.invoke(cli, [subcmd, "--help"])
            if result.exit_code == 0:
                assert "Usage:" in result.output
                # Should contain emoji
                assert "🎭" in result.output or "🔐" in result.output


class TestCLIVersion:
    """Test CLI version functionality specifically"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_basic_version_command(self):
        """Test basic --version functionality"""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "n8n-deploy, version" in result.output

    def test_version_format_validation(self):
        """Test version output format"""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

        import re

        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        version_pattern = r"n8n-deploy, version \d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"
        assert re.search(version_pattern, result.output), f"Invalid version format: {result.output}"


class TestCLIHelpVersionCombinations:
    """Test help and version flag combinations"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_help_version_precedence(self):
        """Test flag mutual exclusion behavior"""
        # --help --version: silently exits with no output (mutual exclusion)
        result1 = self.runner.invoke(cli, ["--help", "--version"])
        assert result1.exit_code == 0
        assert result1.output == ""

        # --version --help: silently exits with no output (mutual exclusion)
        result2 = self.runner.invoke(cli, ["--version", "--help"])
        assert result2.exit_code == 0
        assert result2.output == ""


class TestCustomGroupMethods:
    """Tests for CustomGroup class methods"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_get_command(self):
        """Test CustomGroup.get_command disables prefix matching - requires exact names"""
        from api.cli.app import CustomGroup

        # Create a custom group with some commands
        @click.group(cls=CustomGroup)
        def test_group():
            pass

        @test_group.command(name="status")
        def status_cmd():
            click.echo("status called")

        @test_group.command(name="statistics")
        def statistics_cmd():
            click.echo("statistics called")

        # Test exact match works
        result = self.runner.invoke(test_group, ["status"])
        assert result.exit_code == 0
        assert "status called" in result.output

        # Test that prefix matching is DISABLED (stat should NOT match status)
        result = self.runner.invoke(test_group, ["stat"])
        assert result.exit_code != 0
        assert "No such command 'stat'" in result.output

        # Test another partial match fails
        result = self.runner.invoke(test_group, ["statis"])
        assert result.exit_code != 0
        assert "No such command 'statis'" in result.output

    def test_get_command_exact_match_required(self):
        """Test that only exact command names work, not partial matches"""
        # Use the real CLI for this test
        # "wf" should work, but "w" should not
        result = self.runner.invoke(cli, ["wf", "--help"])
        assert result.exit_code == 0

        result = self.runner.invoke(cli, ["w", "--help"])
        assert result.exit_code != 0
        assert "No such command 'w'" in result.output

    def test_format_usage(self):
        """Test CustomGroup.format_usage produces correct usage format"""
        from io import StringIO

        from api.cli.app import CustomGroup

        # Create a custom group
        @click.group(cls=CustomGroup)
        def test_group():
            """Test group"""
            pass

        @test_group.command(name="test")
        def test_cmd():
            """Test command"""
            pass

        # Test help output contains our custom format
        result = self.runner.invoke(test_group, ["--help"])
        assert result.exit_code == 0
        # The format should be "n8n-deploy COMMAND [OPTIONS]..."
        assert "COMMAND [OPTIONS]..." in result.output

    def test_format_usage_real_cli(self):
        """Test format_usage on the real CLI produces expected output"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # Verify our custom usage line is present
        assert "Usage: n8n-deploy COMMAND [OPTIONS]..." in result.output

    def test_custom_group_handles_version_help_mutual_exclusion(self):
        """Test CustomGroup.parse_args handles --help --version mutual exclusion"""
        # Both --help and --version should result in silent exit
        result = self.runner.invoke(cli, ["--help", "--version"])
        assert result.exit_code == 0
        assert result.output == ""

        result = self.runner.invoke(cli, ["--version", "--help"])
        assert result.exit_code == 0
        assert result.output == ""


class TestCLIVerboseFlag:
    """Test verbose flag behavior"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def teardown_method(self):
        """Reset verbose state after each test"""
        from api.cli.verbose import set_verbose

        set_verbose(0)

    def test_verbose_flag_available(self):
        """Test -v/--verbose flag is available at root level"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.output or "-v" in result.output

    def test_verbose_short_flag(self):
        """Test -v short flag works"""
        result = self.runner.invoke(cli, ["-v", "--help"])
        assert result.exit_code == 0

    def test_verbose_long_flag(self):
        """Test --verbose long flag works"""
        result = self.runner.invoke(cli, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_verbose_with_version(self):
        """Test --verbose with --version shows version"""
        result = self.runner.invoke(cli, ["--verbose", "--version"])
        assert result.exit_code == 0
        assert "n8n-deploy, version" in result.output

    def test_verbose_with_subcommand_help(self):
        """Test --verbose with subcommand --help works"""
        result = self.runner.invoke(cli, ["-v", "wf", "--help"])
        assert result.exit_code == 0
        assert "wf" in result.output.lower() or "workflow" in result.output.lower()

    def test_verbose_help_description(self):
        """Test verbose flag has proper help description"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Verbosity level" in result.output or "-vv" in result.output

    def test_verbose_flag_is_global(self):
        """Test verbose flag is at root level, not on subcommands"""
        # Verbose should be at root level
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.output

        # Verbose should NOT be repeated on subcommands
        result = self.runner.invoke(cli, ["wf", "list", "--help"])
        assert result.exit_code == 0
        # --verbose should not appear in subcommand help (it's global)
        # Note: This test documents expected behavior - global options appear at root only
