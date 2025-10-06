#!/usr/bin/env python3
"""
Minimal unit tests for n8n_deploy_ configuration management
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from assertpy import assert_that

from api.config import AppConfig, get_config


# === Configuration Tests ===
class TestAppConfig:
    """Test AppConfig core functionality"""

    def test_config_creation_with_path_object(self, temp_dir):
        """Test creating config with Path object"""
        config = AppConfig(base_folder=temp_dir)
        assert_that(config.base_folder).is_equal_to(temp_dir)

    def test_database_path_property(self, temp_dir):
        """Test database_path property returns correct path"""
        config = AppConfig(base_folder=temp_dir)
        expected_path = temp_dir / "n8n-deploy.db"
        assert_that(config.database_path).is_equal_to(expected_path)

    def test_workflows_path_property(self, temp_dir):
        """Test workflows_path property returns base_folder when no flow_folder specified"""
        config = AppConfig(base_folder=temp_dir)
        # When no flow_folder is specified, workflows_path returns base_folder directly
        expected_path = temp_dir
        assert_that(config.workflows_path).is_equal_to(expected_path)

    def test_backups_path_property(self, temp_dir):
        """Test backups_path property returns correct path"""
        config = AppConfig(base_folder=temp_dir)
        expected_path = temp_dir  # Now defaults to base folder instead of base_folder/backups
        assert_that(config.backups_path).is_equal_to(expected_path)


# === Get Config Function Tests ===
class TestGetConfig:
    """Test get_config function core functionality"""

    def test_get_config_flow_dir_parameter_priority(self, temp_dir):
        """Test parameter takes priority over environment variable"""
        with patch.dict(os.environ, {"N8N_DEPLOY_FLOWS_DIR": "/env/path"}):
            config = get_config(base_folder=temp_dir, flow_folder=temp_dir / "custom")
            assert_that(config.workflows_path).is_equal_to(temp_dir / "custom")

    def test_get_config_uses_cwd_as_default(self, temp_dir):
        """Test that get_config uses current working directory as default"""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config()
            # Should use current working directory as base folder
            assert_that(config.base_folder).is_equal_to(Path.cwd())
            assert_that(config.workflows_path).is_equal_to(Path.cwd())

    def test_get_config_defaults_to_cwd_when_app_dir_not_exists(self):
        """Test that N8N_DEPLOY_DATA defaults to cwd when path doesn't exist"""
        with patch.dict(os.environ, {"N8N_DEPLOY_DATA_DIR": "/nonexistent/path"}):
            config = get_config()
            # Should fall back to current working directory
            assert_that(config.base_folder).is_equal_to(Path.cwd())

    def test_get_config_defaults_to_cwd_when_app_dir_is_file(self, temp_dir):
        """Test that N8N_DEPLOY_DATA defaults to cwd when path is a file"""
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test")

        with patch.dict(os.environ, {"N8N_DEPLOY_DATA_DIR": str(test_file)}):
            config = get_config()
            # Should fall back to current working directory
            assert_that(config.base_folder).is_equal_to(Path.cwd())

    def test_get_config_defaults_to_cwd_when_flow_dir_not_exists(self):
        """Test that N8N_DEPLOY_FLOWS defaults to cwd when path doesn't exist"""
        with patch.dict(os.environ, {"N8N_DEPLOY_FLOWS_DIR": "/nonexistent/flow/path"}):
            config = get_config()
            # Should fall back to current working directory
            assert_that(config.workflows_path).is_equal_to(Path.cwd())

    def test_get_config_defaults_to_cwd_when_flow_dir_is_file(self, temp_dir):
        """Test that N8N_DEPLOY_FLOWS defaults to cwd when path is a file"""
        test_file = temp_dir / "flow_file.txt"
        test_file.write_text("test")

        with patch.dict(os.environ, {"N8N_DEPLOY_FLOWS_DIR": str(test_file)}):
            config = get_config()
            # Should fall back to current working directory
            assert_that(config.workflows_path).is_equal_to(Path.cwd())
