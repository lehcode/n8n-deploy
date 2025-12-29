"""Unit tests for N8nAPI push_workflow method."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from api.workflow.n8n_api import N8nAPI
from api.workflow.types import N8nApiErrorType, N8nApiResult


class TestPushWorkflow:
    """Tests for N8nAPI push_workflow method"""

    def test_push_workflow(self, temp_dir: Path) -> None:
        """Test push_workflow method pushes workflow to server"""
        # Setup
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.flow_folder = workflows_path
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        # Create workflow file
        workflow_data: Dict[str, Any] = {
            "id": "test_wf_456",
            "name": "Push Test Workflow",
            "active": False,
            "nodes": [],
            "connections": {},
        }
        workflow_file = workflows_path / "test_wf_456.json"
        with open(workflow_file, "w") as f:
            json.dump(workflow_data, f)

        # Mock workflow info from CRUD
        mock_wf = MagicMock()
        mock_wf.id = "test_wf_456"
        mock_wf.file_folder = str(workflows_path)

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # Mock methods
        with patch.object(
            api,
            "_get_n8n_credentials",
            return_value={
                "api_key": "test_key",
                "server_url": "http://test.com",
                "headers": {"X-N8N-API-KEY": "test_key"},
            },
        ):
            # Mock get_n8n_workflow_typed to return existing workflow (update case)
            with patch.object(api, "get_n8n_workflow_typed", return_value=N8nApiResult(success=True, data=workflow_data)):
                # Mock update_n8n_workflow
                with patch.object(
                    api, "update_n8n_workflow", return_value={"id": "test_wf_456", "name": "Push Test Workflow"}
                ):
                    # Mock get_n8n_version
                    with patch.object(api, "get_n8n_version", return_value="1.45.0"):
                        # Mock WorkflowCRUD (imported from api.workflow.crud)
                        with patch("api.workflow.crud.WorkflowCRUD") as mock_crud_class:
                            mock_crud = MagicMock()
                            mock_crud.get_workflow_info.return_value = {
                                "wf": mock_wf,
                                "name": "Push Test Workflow",
                            }
                            # Mock get_workflow_filename to return the actual filename
                            mock_crud.get_workflow_filename.return_value = "test_wf_456.json"
                            mock_crud_class.return_value = mock_crud

                            # Mock db.get_workflow for n8n_version update
                            mock_db.get_workflow.return_value = mock_wf

                            result = api.push_workflow("test_wf_456")

        assert_that(result).is_true()
        mock_db.increment_push_count.assert_called_once_with("test_wf_456")

    def test_push_workflow_file_not_found(self, temp_dir: Path) -> None:
        """Test push_workflow returns False when workflow file doesn't exist"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.flow_folder = workflows_path
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        # Mock workflow info but no file
        mock_wf = MagicMock()
        mock_wf.id = "nonexistent_wf"
        mock_wf.file_folder = str(workflows_path)

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        with patch("api.workflow.crud.WorkflowCRUD") as mock_crud_class:
            mock_crud = MagicMock()
            mock_crud.get_workflow_info.return_value = {
                "wf": mock_wf,
                "name": "Nonexistent Workflow",
            }
            # Mock get_workflow_filename to return a non-existent filename
            mock_crud.get_workflow_filename.return_value = "nonexistent_wf.json"
            mock_crud_class.return_value = mock_crud

            result = api.push_workflow("nonexistent_wf")

        assert_that(result).is_false()


class TestPushWorkflow404Handling:
    """Tests for push_workflow handling of 404 errors (stale workflow IDs)"""

    def test_push_workflow_404_creates_new_and_updates_id(self, temp_dir: Path) -> None:
        """Test that 404 response creates new workflow and updates local ID"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.flow_folder = workflows_path
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        # Create workflow file with old ID
        old_workflow_id = "stale_wf_123"
        new_server_id = "new_server_456"
        workflow_data: Dict[str, Any] = {
            "id": old_workflow_id,
            "name": "Test Workflow",
            "nodes": [],
            "connections": {},
        }
        workflow_file = workflows_path / f"{old_workflow_id}.json"
        with open(workflow_file, "w") as f:
            json.dump(workflow_data, f)

        # Mock workflow object
        mock_wf = MagicMock()
        mock_wf.id = old_workflow_id
        mock_wf.name = "Test Workflow"
        mock_wf.file = f"{old_workflow_id}.json"
        mock_wf.file_folder = str(workflows_path)
        mock_wf.server_id = None
        mock_wf.status = "active"
        mock_wf.created_at = datetime.now(timezone.utc)
        mock_wf.push_count = 0
        mock_wf.pull_count = 0
        mock_wf.scripts_path = None

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        with patch.object(
            api,
            "_get_n8n_credentials",
            return_value={
                "api_key": "test_key",
                "server_url": "http://test.com",
                "headers": {"X-N8N-API-KEY": "test_key"},
            },
        ):
            # Mock get_n8n_workflow_typed to return 404 (stale ID)
            with patch.object(
                api,
                "get_n8n_workflow_typed",
                return_value=N8nApiResult(success=False, error_type=N8nApiErrorType.NOT_FOUND, error_message="Not found"),
            ):
                # Mock create_n8n_workflow to return new ID
                with patch.object(api, "create_n8n_workflow", return_value={"id": new_server_id, "name": "Test Workflow"}):
                    with patch.object(api, "get_n8n_version", return_value="1.45.0"):
                        with patch("api.workflow.crud.WorkflowCRUD") as mock_crud_class:
                            mock_crud = MagicMock()
                            mock_crud.get_workflow_info.return_value = {
                                "wf": mock_wf,
                                "name": "Test Workflow",
                            }
                            mock_crud.get_workflow_filename.return_value = f"{old_workflow_id}.json"
                            mock_crud_class.return_value = mock_crud

                            # Mock db.get_workflow for ID update
                            mock_db.get_workflow.return_value = mock_wf

                            result = api.push_workflow(old_workflow_id)

        assert_that(result).is_true()
        # Verify old ID was deleted and new ID was added
        mock_db.delete_workflow.assert_called_once_with(old_workflow_id)
        mock_db.add_workflow.assert_called_once()

        # Verify the JSON file was updated with new ID
        with open(workflow_file, "r") as f:
            updated_data = json.load(f)
        assert_that(updated_data["id"]).is_equal_to(new_server_id)

    def test_push_workflow_network_error_aborts(self, temp_dir: Path) -> None:
        """Test that network errors abort push without creating new workflow"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.flow_folder = workflows_path
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        # Create workflow file
        workflow_id = "test_wf_789"
        workflow_data: Dict[str, Any] = {
            "id": workflow_id,
            "name": "Test Workflow",
            "nodes": [],
            "connections": {},
        }
        workflow_file = workflows_path / f"{workflow_id}.json"
        with open(workflow_file, "w") as f:
            json.dump(workflow_data, f)

        # Mock workflow object
        mock_wf = MagicMock()
        mock_wf.id = workflow_id
        mock_wf.file_folder = str(workflows_path)

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        with patch.object(
            api,
            "_get_n8n_credentials",
            return_value={
                "api_key": "test_key",
                "server_url": "http://test.com",
                "headers": {"X-N8N-API-KEY": "test_key"},
            },
        ):
            # Mock get_n8n_workflow_typed to return network error
            with patch.object(
                api,
                "get_n8n_workflow_typed",
                return_value=N8nApiResult(
                    success=False, error_type=N8nApiErrorType.NETWORK_ERROR, error_message="Connection refused"
                ),
            ):
                with patch("api.workflow.crud.WorkflowCRUD") as mock_crud_class:
                    mock_crud = MagicMock()
                    mock_crud.get_workflow_info.return_value = {
                        "wf": mock_wf,
                        "name": "Test Workflow",
                    }
                    mock_crud.get_workflow_filename.return_value = f"{workflow_id}.json"
                    mock_crud_class.return_value = mock_crud

                    result = api.push_workflow(workflow_id)

        # Push should fail
        assert_that(result).is_false()
        # create_n8n_workflow should NOT have been called (no duplicate created)
        # Database should remain unchanged
        mock_db.delete_workflow.assert_not_called()
        mock_db.add_workflow.assert_not_called()

    def test_push_workflow_auth_error_aborts(self, temp_dir: Path) -> None:
        """Test that auth errors abort push"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.flow_folder = workflows_path
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        # Create workflow file
        workflow_id = "test_wf_auth"
        workflow_data: Dict[str, Any] = {
            "id": workflow_id,
            "name": "Test Workflow",
            "nodes": [],
            "connections": {},
        }
        workflow_file = workflows_path / f"{workflow_id}.json"
        with open(workflow_file, "w") as f:
            json.dump(workflow_data, f)

        mock_wf = MagicMock()
        mock_wf.id = workflow_id
        mock_wf.file_folder = str(workflows_path)

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        with patch.object(
            api,
            "_get_n8n_credentials",
            return_value={
                "api_key": "test_key",
                "server_url": "http://test.com",
                "headers": {"X-N8N-API-KEY": "test_key"},
            },
        ):
            # Mock get_n8n_workflow_typed to return auth error
            with patch.object(
                api,
                "get_n8n_workflow_typed",
                return_value=N8nApiResult(
                    success=False, error_type=N8nApiErrorType.AUTH_FAILURE, error_message="Invalid API key"
                ),
            ):
                with patch("api.workflow.crud.WorkflowCRUD") as mock_crud_class:
                    mock_crud = MagicMock()
                    mock_crud.get_workflow_info.return_value = {
                        "wf": mock_wf,
                        "name": "Test Workflow",
                    }
                    mock_crud.get_workflow_filename.return_value = f"{workflow_id}.json"
                    mock_crud_class.return_value = mock_crud

                    result = api.push_workflow(workflow_id)

        assert_that(result).is_false()
        mock_db.delete_workflow.assert_not_called()
        mock_db.add_workflow.assert_not_called()
