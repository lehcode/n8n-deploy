#!/usr/bin/env python3
"""
Minimal unit tests for n8n_deploy_ configuration management
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that

from api.config import n8n_deploy_Config, get_config


class Testn8n_deploy_Config:
    """Test n8n_deploy_Config core functionality"""

    def test_config_creation_with_path_object(self, temp_dir):
        """Test creating config with Path object"""
        config = n8n_deploy_Config(base_folder=temp_dir)
        assert_that(config.base_folder).is_equal_to(temp_dir)

    def test_database_path_property(self, temp_dir):
        """Test database_path property returns correct path"""
        config = n8n_deploy_Config(base_folder=temp_dir)
        expected_path = temp_dir / "n8n-deploy.db"
        assert_that(config.database_path).is_equal_to(expected_path)

    def test_workflows_path_property(self, temp_dir):
        """Test workflows_path property returns correct path"""
        config = n8n_deploy_Config(base_folder=temp_dir)
        expected_path = temp_dir / "workflows"
        assert_that(config.workflows_path).is_equal_to(expected_path)

    def test_backups_path_property(self, temp_dir):
        """Test backups_path property returns correct path"""
        config = n8n_deploy_Config(base_folder=temp_dir)
        expected_path = temp_dir / "backups"
        assert_that(config.backups_path).is_equal_to(expected_path)


class TestGetConfig:
    """Test get_config function core functionality"""

    def test_get_config_flow_dir_parameter_priority(self, temp_dir):
        """Test parameter takes priority over environment variable"""
        with patch.dict(os.environ, {"N8N_FLOW_DIR": "/env/path"}):
            config = get_config(base_folder=temp_dir, flow_folder=temp_dir / "custom")
            assert_that(config.workflows_path).is_equal_to(temp_dir / "custom")

    def test_get_config_falls_back_to_current_directory(self, temp_dir):
        """Test fallback to current directory when no parameters given"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.cwd", return_value=temp_dir):
                config = get_config()
                assert_that(config.base_folder).is_equal_to(temp_dir)
