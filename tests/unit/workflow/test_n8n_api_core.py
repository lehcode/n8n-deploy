"""Unit tests for N8nAPI initialization and version methods.

Tests for N8nAPI class __init__ and get_n8n_version methods.
"""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from api.workflow.n8n_api import N8nAPI


class TestN8nAPIInit:
    """Tests for N8nAPI class initialization"""

    def test_init(self, temp_dir: Path) -> None:
        """Test N8nAPI.__init__ method initializes attributes correctly"""
        # Create mocks
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = False
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
        assert_that(api.base_path_explicit).is_false()
        # Server URL and API key are now cached in ServerResolver
        assert_that(api._server_resolver._cached_url).is_none()
        assert_that(api._server_resolver._cached_api_key).is_none()

    def test_init_with_ssl_skip(self, temp_dir: Path) -> None:
        """Test N8nAPI initialization with skip_ssl_verify=True"""
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

        assert_that(api.skip_ssl_verify).is_true()
        assert_that(api.base_path_explicit).is_true()

    def test_init_with_remote(self, temp_dir: Path) -> None:
        """Test N8nAPI initialization with remote parameter"""
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
        mock_api_manager = MagicMock()

        api = N8nAPI(
            db=mock_db,
            config=mock_config,
            api_manager=mock_api_manager,
            remote="http://test-server.com:5678",
        )

        assert_that(api.remote).is_equal_to("http://test-server.com:5678")


class TestN8nAPIVersion:
    """Tests for N8nAPI get_n8n_version method"""

    def test_get_n8n_version(self, temp_dir: Path) -> None:
        """Test get_n8n_version retrieves version from settings endpoint"""
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
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
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
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
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
        mock_config.flow_folder = temp_dir / "workflows"
        mock_config.flow_folder_explicit = True
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
