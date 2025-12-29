"""Unit tests for N8nAPI _strip_readonly_fields method."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from api.workflow.n8n_api import N8nAPI


class TestStripReadonlyFields:
    """Tests for _strip_readonly_fields method"""

    def test_strip_readonly_fields_removes_all_readonly(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields removes all read-only fields"""
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

        # Verify only allowed fields are kept (whitelist approach)
        # Allowed: name, nodes, connections, settings, staticData
        assert_that(result).does_not_contain_key("id")
        assert_that(result).does_not_contain_key("active")
        assert_that(result).does_not_contain_key("triggerCount")
        assert_that(result).does_not_contain_key("updatedAt")
        assert_that(result).does_not_contain_key("createdAt")
        assert_that(result).does_not_contain_key("versionId")
        assert_that(result).does_not_contain_key("tags")
        assert_that(result).does_not_contain_key("meta")
        # staticData IS allowed by n8n API
        assert_that(result).contains_key("staticData")

    def test_strip_readonly_fields_preserves_other_fields(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields preserves non-readonly fields"""
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
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
        )

        result = api._strip_readonly_fields({})

        assert_that(result).is_empty()

    def test_strip_readonly_fields_removes_additional_readonly(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields removes additional readonly fields (isArchived, pinData, etc)"""
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

        workflow_data: Dict[str, Any] = {
            "name": "Test Workflow",
            "isArchived": False,
            "pinData": {"node1": [{"data": "test"}]},
            "versionCounter": 5,
            "shared": [{"id": "user1"}],
            "nodes": [],
            "connections": {},
        }

        result = api._strip_readonly_fields(workflow_data)

        # Verify additional readonly fields are removed
        assert_that(result).does_not_contain_key("isArchived")
        assert_that(result).does_not_contain_key("pinData")
        assert_that(result).does_not_contain_key("versionCounter")
        assert_that(result).does_not_contain_key("shared")
        # Verify valid fields are preserved
        assert_that(result).contains_key("name")
        assert_that(result).contains_key("nodes")
        assert_that(result).contains_key("connections")

    def test_strip_readonly_fields_filters_invalid_settings(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields filters invalid fields from settings object"""
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

        workflow_data: Dict[str, Any] = {
            "name": "Test Workflow",
            "nodes": [],
            "connections": {},
            "settings": {
                "executionOrder": "v1",
                "callerPolicy": "workflowsFromSameOwner",
                "availableInMCP": False,  # Invalid - should be filtered
                "customField": "value",  # Invalid - should be filtered
            },
        }

        result = api._strip_readonly_fields(workflow_data)

        # Verify settings are filtered
        assert_that(result).contains_key("settings")
        assert_that(result["settings"]).contains_key("executionOrder")
        assert_that(result["settings"]).contains_key("callerPolicy")
        assert_that(result["settings"]).does_not_contain_key("availableInMCP")
        assert_that(result["settings"]).does_not_contain_key("customField")

    def test_strip_readonly_fields_preserves_valid_settings(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields preserves all valid settings fields"""
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

        workflow_data: Dict[str, Any] = {
            "name": "Test Workflow",
            "nodes": [],
            "connections": {},
            "settings": {
                "executionOrder": "v1",
                "callerPolicy": "workflowsFromSameOwner",
                "saveDataErrorExecution": "all",
                "saveDataSuccessExecution": "all",
                "saveManualExecutions": True,
                "saveExecutionProgress": True,
                "executionTimeout": 3600,
                "errorWorkflow": "error-handler-wf-id",
                "timezone": "Europe/London",
            },
        }

        result = api._strip_readonly_fields(workflow_data)

        # All valid settings should be preserved
        assert_that(result["settings"]).is_length(9)
        assert_that(result["settings"]["executionOrder"]).is_equal_to("v1")
        assert_that(result["settings"]["timezone"]).is_equal_to("Europe/London")

    def test_strip_readonly_fields_handles_non_dict_settings(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields handles non-dict settings gracefully"""
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

        # Settings as None
        workflow_data: Dict[str, Any] = {
            "name": "Test Workflow",
            "settings": None,
        }

        result = api._strip_readonly_fields(workflow_data)

        # None settings should pass through unchanged
        assert_that(result["settings"]).is_none()

    def test_strip_readonly_fields_handles_empty_settings(self, temp_dir: Path) -> None:
        """Test _strip_readonly_fields handles empty settings dict"""
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

        workflow_data: Dict[str, Any] = {
            "name": "Test Workflow",
            "settings": {},
        }

        result = api._strip_readonly_fields(workflow_data)

        assert_that(result["settings"]).is_empty()


class TestStripFieldsIntegration:
    """Tests for stripping fields in create/update workflow methods"""

    def test_create_n8n_workflow_strips_fields(self, temp_dir: Path) -> None:
        """Test create_n8n_workflow strips readonly fields before POST"""
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
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
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
