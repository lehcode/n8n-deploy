#!/usr/bin/env python3
"""
Unit tests for CLI help functionality

Tests the --help flag and help command behavior in the modular CLI structure.
"""

import pytest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.cli import cli


class TestCLIHelp:
    """Test CLI help functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_help_command_content(self):
        """Test help command contains required sections"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        # Required sections
        assert "Usage:" in result.output
        assert "Commands:" in result.output
        assert "Options:" in result.output

        # Main help should still contain emojis
        assert "🎭" in result.output

    def test_basic_help_command(self):
        """Test basic help functionality"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output

    def test_subcommand_help_access(self):
        """Test accessing subcommand help"""
        result = self.runner.invoke(cli, ["wf", "list", "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_help_content_completeness(self):
        """Test help content includes all expected commands"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        # Check for expected command groups
        expected_command_groups = ["apikey", "db", "wf"]
        for command_group in expected_command_groups:
            assert command_group in result.output, f"Command group '{command_group}' not found in help"

    def test_subcommand_help_consistency(self):
        """Test subcommand help is accessible"""
        # Test db subcommand help
        result = self.runner.invoke(cli, ["db", "--help"])
        assert result.exit_code == 0
        assert "Database management commands" in result.output

        # Test apikey subcommand help
        result = self.runner.invoke(cli, ["apikey", "--help"])
        assert result.exit_code == 0
        assert "API key management commands" in result.output


class TestCLIHelpVersionCombinations:
    """Test help and version flag combinations"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_help_version_precedence(self):
        """Test behavior when both --help and --version are used"""
        # When both flags are present, should silently exit
        result = self.runner.invoke(cli, ["--help", "--version"])
        assert result.exit_code == 0
        # Should exit silently with no output when both flags are used
        assert result.output == ""
