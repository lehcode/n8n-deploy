"""Unit tests for N8nAPI delete_n8n_workflow method."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import requests
from assertpy import assert_that

from api.workflow.n8n_api import N8nAPI


class TestDeleteN8nWorkflow:
    """Tests for delete_n8n_workflow method"""

    def test_delete_n8n_workflow_success(self, temp_dir: Path) -> None:
        """Test successful workflow deletion"""
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
            mock_response.status_code = 200
            mock_response.headers = {}  # Required for verbose logging

            with patch("api.workflow.http_client.requests.delete", return_value=mock_response) as mock_delete:
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
            result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_false()

    def test_delete_n8n_workflow_404_treated_as_success(self, temp_dir: Path) -> None:
        """Test 404 response is treated as success (workflow already deleted)"""
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
            mock_response.headers = {}  # Required for verbose logging
            http_error = requests.exceptions.HTTPError(response=mock_response)

            with patch("api.workflow.http_client.requests.delete") as mock_delete:
                mock_delete.return_value.raise_for_status.side_effect = http_error
                mock_delete.return_value = mock_response
                mock_response.raise_for_status = Mock(side_effect=http_error)

                result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_true()

    def test_delete_n8n_workflow_server_error(self, temp_dir: Path) -> None:
        """Test deletion handles server errors (non-404)"""
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
            mock_response.headers = {}  # Required for verbose logging
            http_error = requests.exceptions.HTTPError(response=mock_response)

            with patch("api.workflow.http_client.requests.delete") as mock_delete:
                mock_response.raise_for_status = Mock(side_effect=http_error)
                mock_delete.return_value = mock_response

                result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_false()

    def test_delete_n8n_workflow_network_error(self, temp_dir: Path) -> None:
        """Test deletion handles network errors"""
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
            with patch("api.workflow.http_client.requests.delete") as mock_delete:
                mock_delete.side_effect = requests.exceptions.ConnectionError("Network unreachable")

                result = api.delete_n8n_workflow("test_wf_123")

        assert_that(result).is_false()

    def test_delete_n8n_workflow_skip_ssl_verify(self, temp_dir: Path) -> None:
        """Test deletion with skip_ssl_verify option"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
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
            mock_response.status_code = 200
            mock_response.headers = {}  # Required for verbose logging

            with patch("api.workflow.http_client.requests.delete", return_value=mock_response) as mock_delete:
                result = api.delete_n8n_workflow("test_wf_123")

                assert_that(result).is_true()
                # Verify verify=False when skip_ssl_verify=True
                mock_delete.assert_called_once_with(
                    "https://test.com/api/v1/workflows/test_wf_123",
                    headers={"X-N8N-API-KEY": "test_key"},
                    verify=False,
                    timeout=10,
                )
