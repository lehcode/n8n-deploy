#!/usr/bin/env python3
"""
Unit tests for CLI version functionality

Tests the --version flag and version command behavior in the modular CLI structure.
"""

import pytest
import tempfile
import os
import re
from pathlib import Path
from click.testing import CliRunner

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from api.cli import cli


class TestCLIVersion:
    """Test CLI version functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.runner = CliRunner()

    def test_version_command_format(self):
        """Test version command output format"""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "n8n-deploy, version" in result.output

        # Validate version format
        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        version_pattern = r"n8n-deploy, version \d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"
        assert re.search(version_pattern, result.output), f"Invalid version format: {result.output}"

    def test_basic_version_command(self):
        """Test basic version command functionality"""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output

    def test_version_format_validation(self):
        """Test version format follows semantic versioning"""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

        # Extract version number and validate format
        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        version_line = result.output.strip()
        version_match = re.search(r"(\d+\.\d+(?:\.\d+)?)", version_line)
        assert version_match, f"Version format invalid: {version_line}"

        version_parts = version_match.group(1).split(".")
        assert len(version_parts) in [2, 3], "Version should have 2 or 3 parts (major.minor or major.minor.patch)"

        # All parts should be numeric
        for part in version_parts:
            assert part.isdigit(), f"Version part '{part}' should be numeric"
