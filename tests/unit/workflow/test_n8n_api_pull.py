"""Unit tests for N8nAPI pull_workflow method."""

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from api.workflow.n8n_api import N8nAPI


class TestPullWorkflow:
    """Tests for N8nAPI pull_workflow method"""

    def test_pull_workflow(self, temp_dir: Path) -> None:
        """Test pull_workflow method retrieves and saves workflow"""
        # Setup
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.flow_folder = workflows_path
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        # Configure mock workflow data
        workflow_data: Dict[str, Any] = {
            "id": "test_wf_123",
            "name": "Test Workflow",
            "active": True,
            "nodes": [{"id": "node1", "type": "start"}],
            "connections": {},
        }

        # Mock get_workflow to return None (workflow not in DB)
        mock_db.get_workflow.return_value = None

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # Mock _get_n8n_credentials
        with patch.object(
            api,
            "_get_n8n_credentials",
            return_value={
                "api_key": "test_key",
                "server_url": "http://test.com",
                "headers": {"X-N8N-API-KEY": "test_key"},
            },
        ):
            # Mock get_n8n_workflow
            with patch.object(api, "get_n8n_workflow", return_value=workflow_data):
                # Mock get_n8n_version
                with patch.object(api, "get_n8n_version", return_value="1.45.0"):
                    # Mock WorkflowCRUD for name lookup (imported from api.workflow.crud)
                    with patch("api.workflow.crud.WorkflowCRUD") as mock_crud_class:
                        mock_crud = MagicMock()
                        mock_crud.get_workflow_info.side_effect = ValueError("Not found")
                        mock_crud_class.return_value = mock_crud

                        result = api.pull_workflow("test_wf_123")

        assert_that(result).is_true()

        # Verify file was created
        workflow_file = workflows_path / "test_wf_123.json"
        assert_that(workflow_file.exists()).is_true()

        # Verify file contents
        with open(workflow_file) as f:
            saved_data = json.load(f)
        assert_that(saved_data["id"]).is_equal_to("test_wf_123")
        assert_that(saved_data["name"]).is_equal_to("Test Workflow")

        # Verify database operations called
        mock_db.add_workflow.assert_called_once()
        mock_db.increment_pull_count.assert_called_once_with("test_wf_123")

    def test_pull_workflow_no_credentials(self, temp_dir: Path) -> None:
        """Test pull_workflow returns False when credentials unavailable"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # Mock _get_n8n_credentials to return None
        with patch.object(api, "_get_n8n_credentials", return_value=None):
            with patch("api.workflow.crud.WorkflowCRUD") as mock_crud_class:
                mock_crud = MagicMock()
                mock_crud.get_workflow_info.side_effect = ValueError("Not found")
                mock_crud_class.return_value = mock_crud

                result = api.pull_workflow("test_wf_123")

        assert_that(result).is_false()
