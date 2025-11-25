#!/usr/bin/env python3
"""
CLI __main__.py module entry point tests
"""

import subprocess
import sys
from pathlib import Path
import pytest

from assertpy import assert_that


class TestCLIMainModule:
    """Test CLI __main__.py module entry point functionality"""

    def test_main_module_executable(self):
        """Test that CLI module can be executed via python -m"""
        result = subprocess.run(
            [sys.executable, "-m", "api.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")

    def test_main_module_version(self):
        """Test version output through main module"""
        result = subprocess.run(
            [sys.executable, "-m", "api.cli", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )
        assert_that(result.returncode).is_equal_to(0)
        # Match semantic version with optional dev/rc suffix
        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        assert_that(result.stdout).matches(r"\d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?")

    def test_main_module_no_args(self):
        """Test main module behavior with no arguments"""
        result = subprocess.run(
            [sys.executable, "-m", "api.cli"], capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent.parent
        )
        assert_that(result.returncode).is_equal_to(0)
        assert_that(result.stdout).contains("Usage:")

    def test_main_module_invalid_command(self):
        """Test main module with invalid command"""
        result = subprocess.run(
            [sys.executable, "-m", "api.cli", "invalid_command"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )
        assert_that(result.returncode).is_not_equal_to(0)

    def test_main_module_entry_point_consistency(self):
        """Test that -m api.cli behaves like n8n-deploy command"""
        # Test help output consistency
        result_module = subprocess.run(
            [sys.executable, "-m", "api.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent,
        )

        # Should have same basic structure as direct CLI
        assert_that(result_module.returncode).is_equal_to(0)
        assert_that(result_module.stdout).contains("n8n-deploy")
        assert_that(result_module.stdout).contains("Commands:")
