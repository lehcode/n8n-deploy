"""Unit tests for api/workflow/n8n_api.py module

Tests for N8nAPI class methods.
"""

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
from assertpy import assert_that

from api.workflow.n8n_api import N8nAPI


class TestN8nAPI:
    """Tests for N8nAPI class methods"""

    def test_init(self, temp_dir: Path) -> None:
        """Test N8nAPI.__init__ method initializes attributes correctly"""
        # Create mocks
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        # Test basic initialization
        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        assert_that(api.db).is_equal_to(mock_db)
        assert_that(api.config).is_equal_to(mock_config)
        assert_that(api.api_manager).is_equal_to(mock_api_manager)
        assert_that(api.skip_ssl_verify).is_false()
        assert_that(api.remote).is_none()
        assert_that(api.base_path).is_equal_to(temp_dir / "workflows")
        assert_that(api._server_url).is_none()
        assert_that(api._server_api_key).is_none()

    def test_init_with_ssl_skip(self, temp_dir: Path) -> None:
        """Test N8nAPI initialization with skip_ssl_verify=True"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
            skip_ssl_verify=True,
        )

        assert_that(api.skip_ssl_verify).is_true()

    def test_init_with_remote(self, temp_dir: Path) -> None:
        """Test N8nAPI initialization with remote parameter"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
            remote="http://test-server.com:5678",
        )

        assert_that(api.remote).is_equal_to("http://test-server.com:5678")

    def test_pull_workflow(self, temp_dir: Path) -> None:
        """Test pull_workflow method retrieves and saves workflow"""
        # Setup
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.workflows_path = workflows_path
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
        mock_config.workflows_path = temp_dir / "workflows"
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

    def test_push_workflow(self, temp_dir: Path) -> None:
        """Test push_workflow method pushes workflow to server"""
        # Setup
        mock_db = MagicMock()
        mock_config = MagicMock()
        workflows_path = temp_dir / "workflows"
        workflows_path.mkdir(parents=True, exist_ok=True)
        mock_config.workflows_path = workflows_path
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
            # Mock get_n8n_workflow to return existing (update case)
            with patch.object(api, "get_n8n_workflow", return_value=workflow_data):
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
        mock_config.workflows_path = workflows_path
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

    def test_get_n8n_version(self, temp_dir: Path) -> None:
        """Test get_n8n_version retrieves version from settings endpoint"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # Mock _make_n8n_request to return settings with version
        with patch.object(
            api,
            "_make_n8n_request",
            return_value={"data": {"version": "1.45.0", "publicApi": True}},
        ):
            version = api.get_n8n_version()

        assert_that(version).is_equal_to("1.45.0")

    def test_get_n8n_version_n8n_version_field(self, temp_dir: Path) -> None:
        """Test get_n8n_version with n8nVersion field"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # Mock _make_n8n_request with n8nVersion field
        with patch.object(
            api,
            "_make_n8n_request",
            return_value={"data": {"n8nVersion": "1.46.0"}},
        ):
            version = api.get_n8n_version()

        assert_that(version).is_equal_to("1.46.0")

    def test_get_n8n_version_healthz_fallback(self, temp_dir: Path) -> None:
        """Test get_n8n_version falls back to healthz endpoint"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # First call returns settings without version, second returns healthz
        def mock_request(method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
            if endpoint == "api/v1/settings":
                return {"data": {"publicApi": True}}  # No version field
            elif endpoint == "healthz":
                return {"status": "ok"}
            return {}

        with patch.object(api, "_make_n8n_request", side_effect=mock_request):
            version = api.get_n8n_version()

        assert_that(version).starts_with("healthy-")

    def test_get_n8n_version_exception_returns_none(self, temp_dir: Path) -> None:
        """Test get_n8n_version returns None on exception"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # Mock _make_n8n_request to raise exception
        with patch.object(api, "_make_n8n_request", side_effect=Exception("Network error")):
            version = api.get_n8n_version()

        assert_that(version).is_none()


class TestStripReadonlyFields:
    """Tests for _strip_readonly_fields method"""

    def test_strip_readonly_fields_removes_all_readonly(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields removes all read-only fields"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        workflow_data: Dict[str, Any] = {
            "id": "test_123",
            "name": "Test Workflow",
            "active": True,
            "triggerCount": 5,
            "updatedAt": "2025-01-01T00:00:00Z",
            "createdAt": "2025-01-01T00:00:00Z",
            "versionId": "abc123",
            "staticData": {"key": "value"},
            "tags": [{"id": "1", "name": "test"}],
            "meta": {"instanceId": "xyz"},
            "nodes": [{"id": "node1"}],
            "connections": {},
        }

        result = api._strip_readonly_fields(workflow_data)

        # Verify readonly fields are removed
        assert_that(result).does_not_contain_key("id")
        assert_that(result).does_not_contain_key("active")
        assert_that(result).does_not_contain_key("triggerCount")
        assert_that(result).does_not_contain_key("updatedAt")
        assert_that(result).does_not_contain_key("createdAt")
        assert_that(result).does_not_contain_key("versionId")
        assert_that(result).does_not_contain_key("staticData")
        assert_that(result).does_not_contain_key("tags")
        assert_that(result).does_not_contain_key("meta")

    def test_strip_readonly_fields_preserves_other_fields(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields preserves non-readonly fields"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        workflow_data: Dict[str, Any] = {
            "id": "test_123",
            "name": "Test Workflow",
            "nodes": [{"id": "node1", "type": "start"}],
            "connections": {"node1": []},
            "settings": {"executionOrder": "v1"},
        }

        result = api._strip_readonly_fields(workflow_data)

        # Verify non-readonly fields are preserved
        assert_that(result).contains_key("name")
        assert_that(result).contains_key("nodes")
        assert_that(result).contains_key("connections")
        assert_that(result).contains_key("settings")
        assert_that(result["name"]).is_equal_to("Test Workflow")
        assert_that(result["nodes"]).is_length(1)

    def test_strip_readonly_fields_empty_input(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields handles empty input"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        result = api._strip_readonly_fields({})

        assert_that(result).is_empty()

    def test_create_n8n_workflow_strips_fields(self, temp_dir: Path) -> None:
        """Test create_n8n_workflow strips readonly fields before POST"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        workflow_data: Dict[str, Any] = {
            "id": "should_be_stripped",
            "name": "New Workflow",
            "triggerCount": 0,
            "nodes": [],
            "connections": {},
        }

        with patch.object(api, "_make_n8n_request") as mock_request:
            mock_request.return_value = {"id": "server_assigned_id", "name": "New Workflow"}
            api.create_n8n_workflow(workflow_data)

            # Verify _make_n8n_request was called with stripped data
            call_args = mock_request.call_args
            sent_data = call_args[0][2]  # Third positional argument is data
            assert_that(sent_data).does_not_contain_key("id")
            assert_that(sent_data).does_not_contain_key("triggerCount")
            assert_that(sent_data).contains_key("name")

    def test_update_n8n_workflow_strips_fields(self, temp_dir: Path) -> None:
        """Test update_n8n_workflow strips readonly fields before PUT"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        workflow_data: Dict[str, Any] = {
            "id": "existing_id",
            "name": "Updated Workflow",
            "updatedAt": "2025-01-01T00:00:00Z",
            "versionId": "old_version",
            "nodes": [{"id": "node1"}],
            "connections": {},
        }

        with patch.object(api, "_make_n8n_request") as mock_request:
            mock_request.return_value = {"id": "existing_id", "name": "Updated Workflow"}
            api.update_n8n_workflow("existing_id", workflow_data)

            # Verify _make_n8n_request was called with stripped data
            call_args = mock_request.call_args
            sent_data = call_args[0][2]  # Third positional argument is data
            assert_that(sent_data).does_not_contain_key("id")
            assert_that(sent_data).does_not_contain_key("updatedAt")
            assert_that(sent_data).does_not_contain_key("versionId")
            assert_that(sent_data).contains_key("name")
            assert_that(sent_data).contains_key("nodes")


class TestDeleteN8nWorkflow:
    """Tests for delete_n8n_workflow method"""

    def test_delete_n8n_workflow_success(self, temp_dir: Path) -> None:
        """Test successful workflow deletion"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

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
            # Mock requests.delete to return successful response
            mock_response = Mock()
            mock_response.raise_for_status = Mock()

            with patch("api.workflow.n8n_api.requests.delete", return_value=mock_response) as mock_delete:
                result = api.delete_n8n_workflow("test_wf_123")

                assert_that(result).is_true()
                mock_delete.assert_called_once_with(
                    "http://test.com/api/v1/workflows/test_wf_123",
                    headers={"X-N8N-API-KEY": "test_key"},
                    verify=True,
                    timeout=10,
                )

    def test_delete_n8n_workflow_no_credentials(self, temp_dir: Path) -> None:
        """Test deletion fails without credentials"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        # Mock _get_n8n_credentials to return None
        with patch.object(api, "_get_n8n_credentials", return_value=None):
            result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_false()

    def test_delete_n8n_workflow_404_treated_as_success(self, temp_dir: Path) -> None:
        """Test 404 response is treated as success (workflow already deleted)"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        import requests

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
            # Mock requests.delete to raise 404 HTTPError
            mock_response = Mock()
            mock_response.status_code = 404
            http_error = requests.exceptions.HTTPError(response=mock_response)

            with patch("api.workflow.n8n_api.requests.delete") as mock_delete:
                mock_delete.return_value.raise_for_status.side_effect = http_error
                mock_delete.return_value = mock_response
                mock_response.raise_for_status = Mock(side_effect=http_error)

                result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_true()

    def test_delete_n8n_workflow_server_error(self, temp_dir: Path) -> None:
        """Test deletion handles server errors (non-404)"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        import requests

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
            # Mock requests.delete to raise 500 HTTPError
            mock_response = Mock()
            mock_response.status_code = 500
            http_error = requests.exceptions.HTTPError(response=mock_response)

            with patch("api.workflow.n8n_api.requests.delete") as mock_delete:
                mock_response.raise_for_status = Mock(side_effect=http_error)
                mock_delete.return_value = mock_response

                result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_false()

    def test_delete_n8n_workflow_network_error(self, temp_dir: Path) -> None:
        """Test deletion handles network errors"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        import requests

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
            # Mock requests.delete to raise ConnectionError
            with patch("api.workflow.n8n_api.requests.delete") as mock_delete:
                mock_delete.side_effect = requests.exceptions.ConnectionError("Network unreachable")

                result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_false()

    def test_delete_n8n_workflow_skip_ssl_verify(self, temp_dir: Path) -> None:
        """Test deletion with skip_ssl_verify option"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.workflows_path = temp_dir / "workflows"
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
            skip_ssl_verify=True,
        )

        # Mock _get_n8n_credentials
        with patch.object(
            api,
            "_get_n8n_credentials",
            return_value={
                "api_key": "test_key",
                "server_url": "https://test.com",
                "headers": {"X-N8N-API-KEY": "test_key"},
            },
        ):
            mock_response = Mock()
            mock_response.raise_for_status = Mock()

            with patch("api.workflow.n8n_api.requests.delete", return_value=mock_response) as mock_delete:
                result = api.delete_n8n_workflow("test_wf_123")

                assert_that(result).is_true()
                # Verify verify=False when skip_ssl_verify=True
                mock_delete.assert_called_once_with(
                    "https://test.com/api/v1/workflows/test_wf_123",
                    headers={"X-N8N-API-KEY": "test_key"},
                    verify=False,
                    timeout=10,
                )
