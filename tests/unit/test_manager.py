#!/usr/bin/env python3
"""
Unit tests for n8n_deploy_ wf manager
"""

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest
from assertpy import assert_that

from api.config import AppConfig
from api.models import Workflow
from api.workflow import WorkflowApi


# === Manager Initialization Tests ===
class TestWorkflowApiInitialization:
    """Test WorkflowApi initialization"""

    @pytest.mark.parametrize(
        "init_method,has_config,has_api_manager",
        [("config", True, True), ("base_path", True, True), ("default", True, True)],
    )
    def test_manager_initialization_methods(
        self, temp_dir: Path, test_config: AppConfig, init_method: str, has_config: bool, has_api_manager: bool
    ) -> None:
        """Test manager initialization with different methods"""
        if init_method == "config":
            manager = WorkflowApi(config=test_config)
            expected_config = test_config
            expected_base_path = test_config.workflows_path
        elif init_method == "base_path":
            base_path = temp_dir / "workflows"
            base_path.mkdir(exist_ok=True)
            manager = WorkflowApi(base_path=base_path)
            assert manager.config is not None
            expected_config = manager.config  # Now we create a config
            expected_base_path = manager.config.workflows_path
        else:  # default
            with patch("api.config.get_config") as mock_get_config:
                # Use temp directory for mock paths to avoid permission issues
                mock_base = temp_dir / "mock"
                mock_base.mkdir()

                mock_config = Mock()
                mock_config.workflows_path = mock_base / "workflows"
                mock_config.database_path = mock_base / "n8n-deploy.db"
                mock_config.base_folder = mock_base
                mock_config.backups_path = mock_base / "backups"
                mock_get_config.return_value = mock_config
                manager = WorkflowApi()
                expected_config = mock_config
                expected_base_path = mock_config.workflows_path

        if has_config:
            assert_that(manager.config).is_equal_to(expected_config)
        else:
            assert_that(manager.config).is_none()

        assert_that(manager.config.workflows_path).is_equal_to(expected_base_path)
        assert_that(manager.db).is_not_none()

        if has_api_manager:
            assert_that(manager.key_api).is_not_none()


# === Workflow Operations Tests ===
class TestWorkflowOperations:
    """Test core wf operations"""

    def test_list_workflows_empty(self, test_manager: WorkflowApi) -> None:
        """Test listing workflows from empty database"""
        with test_manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.commit()

        workflows = test_manager.list_workflows()
        assert_that(workflows).is_empty()

    def test_list_workflows_populated(self, test_manager: WorkflowApi, test_workflows_list: List[Dict[str, Any]]) -> None:
        """Test listing workflows from populated database"""
        with test_manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.commit()

        for wf_data in test_workflows_list:
            wf = Workflow(**wf_data)
            test_manager.db.add_workflow(wf)

        workflows = test_manager.list_workflows()
        assert_that(len(workflows)).is_equal_to(len(test_workflows_list))

        workflow_ids = [wf["id"] for wf in workflows]
        expected_ids = [wf["id"] for wf in test_workflows_list]
        assert set(workflow_ids) == set(expected_ids)

    def test_get_workflow_info_existing(self, test_manager: WorkflowApi, mock_workflow_data: Dict[str, Any]) -> None:
        """Test getting workflow info for existing wf"""
        wf = Workflow(**mock_workflow_data)
        test_manager.db.add_workflow(wf)

        info = test_manager.get_workflow_info(wf.id)

        assert info is not None
        assert info["id"] == wf.id
        assert info["name"] == wf.name

    def test_get_workflow_info_nonexistent(self, test_manager: WorkflowApi) -> None:
        """Test getting workflow info for non-existent workflow"""
        with pytest.raises(ValueError, match="Unknown workflow ID"):
            test_manager.get_workflow_info("nonexistent_workflow")


# === n8n Server Integration Tests ===
class TestN8nApiIntegration:
    """Test n8n server API integration functionality"""

    def test_get_n8n_credentials_with_stored_api_key(self, test_manager: WorkflowApi) -> None:
        """Test getting credentials from stored API key"""
        # Mock API key manager to return a key and set server URL via environment
        # N8N_API_URL is used by config.n8n_api_url property
        with (
            patch.dict("os.environ", {"N8N_API_URL": "http://localhost:5678"}),
            patch.object(test_manager.key_api, "list_api_keys", return_value=[{"name": "test_key"}]),
            patch.object(test_manager.key_api, "get_api_key", return_value="test_api_key_12345"),
        ):
            credentials = test_manager.n8n_api._get_n8n_credentials()

            assert credentials is not None
            assert credentials["api_key"] == "test_api_key_12345"
            assert credentials["server_url"] == "http://localhost:5678"
            assert credentials["headers"]["X-N8N-API-KEY"] == "test_api_key_12345"
            assert credentials["headers"]["Content-Type"] == "application/json"

    def test_get_n8n_credentials_with_environment_variable(self, test_manager: WorkflowApi) -> None:
        """Test fallback to N8N_API_KEY environment variable"""
        # Mock API key manager to return None (no stored keys)
        with (
            patch.object(test_manager.key_api, "get_api_key", return_value=None),
            patch.object(test_manager.key_api, "list_api_keys", return_value=[]),
            patch.dict("os.environ", {"N8N_API_URL": "http://localhost:5678", "N8N_API_KEY": "env_api_key_54321"}),
        ):
            credentials = test_manager.n8n_api._get_n8n_credentials()

            assert credentials is not None
            assert credentials["api_key"] == "env_api_key_54321"
            assert credentials["server_url"] == "http://localhost:5678"
            assert credentials["headers"]["X-N8N-API-KEY"] == "env_api_key_54321"

    def test_get_n8n_credentials_no_key_available(self, test_manager: WorkflowApi) -> None:
        """Test behavior when no API key is available"""
        with (
            patch.object(test_manager.key_api, "get_api_key", return_value=None),
            patch.object(test_manager.key_api, "list_api_keys", return_value=[]),
            patch.dict("os.environ", {}, clear=True),
        ):
            credentials = test_manager.n8n_api._get_n8n_credentials()
            assert credentials is None

    @patch("api.workflow.http_client.requests.get")
    def test_make_n8n_request_with_timeout(self, mock_get: Mock, test_manager: WorkflowApi) -> None:
        """Test that requests include proper timeout"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {}  # Required for verbose logging
        mock_get.return_value = mock_response

        # Mock credentials
        with patch.object(
            test_manager.n8n_api, "_get_n8n_credentials", return_value={"headers": {"X-N8N-API-KEY": "test_key"}}
        ):
            test_manager.n8n_api._make_n8n_request("GET", "api/v1/workflows")

            # Verify timeout parameter was passed
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs["timeout"] == 10

    @patch("api.workflow.http_client.requests.get")
    def test_make_n8n_request_handles_timeout_exception(self, mock_get: Mock, test_manager: WorkflowApi) -> None:
        """Test request timeout handling"""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        with patch.object(
            test_manager.n8n_api, "_get_n8n_credentials", return_value={"headers": {"X-N8N-API-KEY": "test_key"}}
        ):
            result = test_manager.n8n_api._make_n8n_request("GET", "api/v1/workflows")
            assert result is None


# === Configuration Integration Tests ===
class TestConfigurationIntegration:
    """Test manager integration with configuration system"""

    def test_manager_backup_path_integration(self, temp_dir: Path) -> None:
        """Test manager uses config backup path correctly"""
        config = AppConfig(base_folder=temp_dir)
        manager = WorkflowApi(config=config)

        expected_backup_path = temp_dir  # Now defaults to base folder instead of base_folder/backups
        assert manager.config.backups_path == expected_backup_path
