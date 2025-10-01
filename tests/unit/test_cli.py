"""
Unit tests for CLI functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
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

        # Validate version format (X.Y.Z)
        import re

        version_pattern = r"n8n-deploy, version \d+\.\d+\.\d+"
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

    def test_app_dir_flag_position(self):
        """Test --app-dir flag is not available at root level but is on commands"""
        # Should fail at root level
        result = self.runner.invoke(cli, ["--app-dir", "/tmp", "--help"])
        assert result.exit_code != 0
        assert "No such option" in result.output

        # Should work on wf list command
        result = self.runner.invoke(cli, ["wf", "list", "--app-dir", "/tmp", "--help"])
        assert result.exit_code == 0


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

        version_pattern = r"n8n-deploy, version \d+\.\d+\.\d+"
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
    """Tests for CustomGroup class methods (0% coverage)"""

    def test_get_command(self):
        """TODO: Test CustomGroup.get_command method"""
        pytest.skip("TODO: Implement test for CustomGroup.get_command (disables prefix matching)")

    def test_format_usage(self):
        """TODO: Test CustomGroup.format_usage method"""
        pytest.skip("TODO: Implement test for CustomGroup.format_usage")
