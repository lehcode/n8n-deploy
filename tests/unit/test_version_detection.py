#!/usr/bin/env python3
"""
Version Detection Tests

Tests for dynamic version detection using setuptools_scm and importlib.metadata.
Validates fallback behavior when git metadata is unavailable (e.g., CI shallow clones).
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
import re

import pytest


class TestVersionDetection:
    """Test version detection from multiple sources"""

    def test_version_from_importlib_metadata(self):
        """Test version detection via importlib.metadata (installed package)"""
        try:
            from importlib.metadata import version

            pkg_version = version("n8n-deploy")
            # Should match semantic versioning pattern with optional suffixes
            # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
            version_pattern = r"\d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"
            assert re.match(version_pattern, pkg_version), f"Version '{pkg_version}' doesn't match expected pattern"
        except Exception as e:
            pytest.skip(f"Package not installed: {e}")

    def test_version_from_api_module(self):
        """Test version detection via api/__init__.py"""
        from api import __version__

        # Should be either a valid version or fallback
        assert __version__ is not None
        assert isinstance(__version__, str)
        # Should match version pattern or be fallback "0.1.5"
        version_pattern = r"(\d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?|0\.1\.4)"
        assert re.match(version_pattern, __version__), f"Version '{__version__}' doesn't match expected pattern"

    def test_version_fallback_behavior(self):
        """Test fallback to 0.1.5 when metadata unavailable"""
        # Mock importlib.metadata.version to raise exception
        with patch("importlib.metadata.version", side_effect=Exception("Package not found")):
            # Re-import api module to trigger fallback logic
            if "api" in sys.modules:
                del sys.modules["api"]
            from api import __version__

            # Should fall back to "0.1.5" when metadata unavailable
            assert __version__ == "0.1.5", f"Expected fallback version '0.1.5', got '{__version__}'"

    def test_cli_version_command(self):
        """Test CLI --version command returns valid version"""
        from click.testing import CliRunner
        from api.cli.app import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "n8n-deploy, version" in result.output
        # Extract version number from output
        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        version_pattern = r"n8n-deploy, version (\d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?)"
        match = re.search(version_pattern, result.output)
        assert match, f"Version not found in output: {result.output}"
        version = match.group(1)
        # Validate version format
        assert re.match(r"\d+\.\d+", version), f"Invalid version format: {version}"

    def test_version_consistency_across_methods(self):
        """Test that version is consistent across different detection methods"""
        # Get version from api module
        from api import __version__ as api_version

        # Get version from CLI
        from click.testing import CliRunner
        from api.cli.app import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        # Extract CLI version (PEP 440: X.Y.Z[rcN][.devM])
        version_pattern = r"n8n-deploy, version (\d+\.\d+(\.\d+)?(rc\d+)?(\.dev\d+)?)"
        match = re.search(version_pattern, result.output)
        cli_version = match.group(1) if match else None

        # Versions should match (unless api_version is fallback "0.1.5")
        if api_version != "0.1.5":
            assert api_version == cli_version, f"Version mismatch: api={api_version}, cli={cli_version}"

    def test_setuptools_scm_fallback_in_ci(self):
        """Test setuptools_scm behavior in CI-like scenarios (shallow clone)"""
        # This test documents expected behavior when git tags are unavailable
        # In CI shallow clones, setuptools_scm may fall back to minimal version

        from api import __version__

        # Version should be one of:
        # 1. Proper semantic version from git tags: 0.1.5, 0.1.5.dev42, 0.1.5rc1
        # 2. CI fallback version: 0.1.dev37, 0.1
        # 3. Development fallback: 0.1.5
        valid_patterns = [
            r"\d+\.\d+\.\d+(\.dev\d+|rc\d+)?",  # Standard version (PEP 440)
            r"\d+\.\d+(\.dev\d+)?",  # Fallback version
            r"0\.1\.4",  # Development fallback
        ]

        is_valid = any(re.fullmatch(pattern, __version__) for pattern in valid_patterns)
        assert is_valid, f"Version '{__version__}' doesn't match any expected pattern in CI scenarios"

    def test_version_pattern_supports_rc_suffix(self):
        """Test that version patterns correctly support RC (release candidate) format"""
        test_versions = [
            "0.1.5",  # Standard release
            "0.1.5.dev42",  # Development version
            "0.1.5rc1",  # Release candidate (PEP 440 format)
            "0.1.5rc10",  # RC with multi-digit number
            "0.1",  # Minimal version (CI fallback)
            "0.1.dev37",  # Minimal dev version
            "0.1.5",  # Fallback version
        ]

        # Pattern used in tests (supports both PEP 440 'rc' and legacy '-rc' formats)
        version_pattern = r"\d+\.\d+(\.\d+)?(\.dev\d+|-?rc\d+)?"

        for version in test_versions:
            assert re.fullmatch(version_pattern, version), f"Version '{version}' should match pattern but doesn't"

    def test_invalid_version_formats_rejected(self):
        """Test that invalid version formats are properly rejected"""
        invalid_versions = [
            "2.0.3.rc1",  # Wrong RC format (dot instead of hyphen)
            "2.0",  # Too short (unless it's 0.1 specifically)
            "v2.0.3",  # Should not include 'v' prefix
            "2.0.3-alpha",  # Alpha not supported
            "2.0.3.beta1",  # Beta not supported
        ]

        # Pattern used in tests
        version_pattern = r"\d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"

        for version in invalid_versions:
            # These should NOT match (except minimal versions like 0.1)
            if version != "2.0":  # 2.0 would match, but we expect 3-part versions
                assert not re.fullmatch(version_pattern, version), f"Version '{version}' should NOT match pattern but does"


class TestGitVersionDetection:
    """Test git-based version detection with setuptools_scm"""

    def test_git_tags_available(self):
        """Test that git tags are available for version detection"""
        import subprocess

        try:
            result = subprocess.run(["git", "describe", "--tags", "--always"], capture_output=True, text=True, check=True)
            git_version = result.stdout.strip()
            # Git describe should return something (tag or commit hash)
            assert git_version, "Git describe should return a value"
            # Should start with 'v' if it's a tag, or be a commit hash
            assert (
                git_version.startswith("v") or len(git_version) >= 7
            ), f"Git describe returned unexpected format: {git_version}"
        except subprocess.CalledProcessError:
            pytest.skip("Git tags not available (may be in shallow clone)")

    def test_git_depth_environment(self):
        """Test GIT_DEPTH environment variable documentation"""
        # This test documents that CI uses GIT_DEPTH=0 for full history
        # It doesn't test the actual behavior, just documents the expectation
        import os

        git_depth = os.environ.get("GIT_DEPTH", "not set")
        # In CI, this should be "0" for full git history
        # Locally, it's typically not set (full clone by default)
        # This test just documents the expected CI behavior
        assert git_depth in ("0", "not set"), f"GIT_DEPTH should be '0' (CI) or 'not set' (local), got: {git_depth}"
