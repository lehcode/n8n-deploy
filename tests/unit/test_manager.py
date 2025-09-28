#!/usr/bin/env python3
"""
Unit tests for n8n_deploy_ workflow manager
"""

import pytest
import json
import tarfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock, mock_open

from assertpy import assert_that

from api.manager import WorkflowManager
from api.models import Workflow, WorkflowType, WorkflowStatus
from api.config import n8n_deploy_Config


class TestWorkflowManagerInitialization:
    """Test WorkflowManager initialization"""

    @pytest.mark.parametrize(
        "init_method,has_config,has_api_manager",
        [("config", True, True), ("base_path", False, False), ("default", True, True)],
    )
    def test_manager_initialization_methods(
        self, temp_dir, test_config, init_method, has_config, has_api_manager
    ):
        """Test manager initialization with different methods"""
        if init_method == "config":
            manager = WorkflowManager(config=test_config)
            expected_config = test_config
            expected_base_path = test_config.workflows_path
        elif init_method == "base_path":
            base_path = temp_dir / "workflows"
            base_path.mkdir(exist_ok=True)
            manager = WorkflowManager(base_path=base_path)
            expected_config = None
            expected_base_path = base_path
        else:  # default
            with patch("api.manager.get_config") as mock_get_config:
                # Use temp directory for mock paths to avoid permission issues
                mock_base = temp_dir / "mock"
                mock_base.mkdir()

                mock_config = Mock()
                mock_config.workflows_path = mock_base / "workflows"
                mock_config.database_path = mock_base / "n8n-deploy.db"
                mock_config.base_folder = mock_base
                mock_config.backups_path = mock_base / "backups"
                mock_get_config.return_value = mock_config
                manager = WorkflowManager()
                expected_config = mock_config
                expected_base_path = mock_config.workflows_path

        if has_config:
            assert_that(manager.config).is_equal_to(expected_config)
        else:
            assert_that(manager.config).is_none()

        assert_that(manager.base_path).is_equal_to(expected_base_path)
        assert_that(manager.db).is_not_none()

        if has_api_manager:
            assert_that(manager.api_manager).is_not_none()


class TestWorkflowOperations:
    """Test core workflow operations"""

    def test_list_workflows_empty(self, test_manager):
        """Test listing workflows from empty database"""
        # Clear any default workflows first
        with test_manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.commit()

        workflows = test_manager.list_workflows()
        assert_that(workflows).is_empty()

    def test_list_workflows_populated(self, test_manager, test_workflows_list):
        """Test listing workflows from populated database"""
        # Clear any existing workflows
        with test_manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.commit()

        # Add test workflows
        for wf_data in test_workflows_list:
            workflow = Workflow(**wf_data)
            test_manager.db.create_workflow(workflow)

        workflows = test_manager.list_workflows()
        assert_that(len(workflows)).is_equal_to(len(test_workflows_list))

        # Verify workflow data
        workflow_ids = [wf["id"] for wf in workflows]
        expected_ids = [wf["id"] for wf in test_workflows_list]
        assert set(workflow_ids) == set(expected_ids)

    def test_get_workflow_info_existing(self, test_manager, mock_workflow_data):
        """Test getting workflow info for existing workflow"""
        # Add workflow to database
        workflow = Workflow(**mock_workflow_data)
        test_manager.db.create_workflow(workflow)

        # Get workflow info
        info = test_manager.get_workflow_info(workflow.id)

        assert info is not None
        assert info["id"] == workflow.id
        assert info["name"] == workflow.name
        assert info["type"] == workflow.type
        assert info["file"] == workflow.file_path

    def test_get_workflow_info_nonexistent(self, test_manager):
        """Test getting workflow info for non-existent workflow"""
        with pytest.raises(ValueError, match="Unknown workflow ID"):
            test_manager.get_workflow_info("nonexistent_workflow")


class TestBackupOperations:
    """Test backup and restore operations"""

    def test_create_workflow_backup_success(self, test_manager, mock_workflow_data):
        """Test creating backup of a single workflow successfully"""
        # Clear database and add single workflow
        with test_manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.commit()

        # Create workflow in database
        workflow = Workflow(**mock_workflow_data)
        test_manager.db.create_workflow(workflow)

        # Create workflow file on filesystem
        file_path = test_manager.base_path / workflow.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump({"id": workflow.id, "name": workflow.name, "nodes": []}, f)

        # Test backup creation
        backup_result = test_manager.create_workflow_backup(workflow.id)

        # Verify backup structure
        assert backup_result is not None
        assert isinstance(backup_result, dict)
        assert "backup_id" in backup_result
        assert "filename" in backup_result
        assert "workflow_id" in backup_result

        # Verify file naming convention: n8n_deploy_workflow_{id}_YYYYMMDD_HHMMSS.tar.gz
        filename = backup_result["filename"]
        assert filename.startswith(f"n8n_deploy_workflow_{workflow.id}_")
        assert filename.endswith(".tar.gz")

        # Verify backup contains single workflow
        assert backup_result["workflow_count"] == 1
        assert backup_result["workflow_id"] == workflow.id

    def test_create_workflow_backup_nonexistent_workflow(self, test_manager):
        """Test backup fails for non-existent workflow"""
        with pytest.raises(
            ValueError, match="Workflow 'nonexistent' not found in database"
        ):
            test_manager.create_workflow_backup("nonexistent")

    def test_create_workflow_backup_missing_file(
        self, test_manager, mock_workflow_data
    ):
        """Test backup fails when workflow file is missing"""
        # Add workflow to database but don't create file
        workflow = Workflow(**mock_workflow_data)
        test_manager.db.create_workflow(workflow)

        with pytest.raises(FileNotFoundError, match="Workflow file not found"):
            test_manager.create_workflow_backup(workflow.id)
