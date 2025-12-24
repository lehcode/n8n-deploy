#!/usr/bin/env python3
"""
Integration tests for transport layer (plugin system).

Tests transport plugin registration, discovery, and basic functionality.
"""

import tempfile
from pathlib import Path
from typing import Iterator

import pytest


class TestTransportPluginRegistry:
    """Integration tests for transport plugin registry"""

    def test_sftp_transport_is_registered(self) -> None:
        """Test SFTP transport is properly registered in plugin registry"""
        from api.transports.base import PluginRegistry

        plugins = PluginRegistry.list_plugins()
        assert "sftp" in plugins, f"SFTP transport not registered. Available: {plugins}"

    def test_sftp_transport_can_be_created(self) -> None:
        """Test SFTP transport can be instantiated via registry"""
        from api.transports.base import PluginRegistry

        plugin = PluginRegistry.create_instance("sftp")
        assert plugin is not None, "Failed to create SFTP transport instance"
        assert plugin.name == "sftp"

    def test_unknown_transport_returns_none(self) -> None:
        """Test unknown transport name returns None"""
        from api.transports.base import PluginRegistry

        plugin = PluginRegistry.create_instance("nonexistent_transport")
        assert plugin is None

    def test_sftp_transport_has_description(self) -> None:
        """Test SFTP transport has a description"""
        from api.transports.base import PluginRegistry

        plugin = PluginRegistry.create_instance("sftp")
        assert plugin is not None
        assert plugin.description, "SFTP transport should have a description"
        assert "SFTP" in plugin.description


class TestTransportTarget:
    """Integration tests for TransportTarget configuration"""

    def test_transport_target_with_password(self) -> None:
        """Test TransportTarget creation with password authentication"""
        from api.transports.base import TransportTarget

        target = TransportTarget(
            host="localhost",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            password="testpass",
        )

        assert target.host == "localhost"
        assert target.port == 22
        assert target.username == "testuser"
        assert target.base_path == "/opt/scripts"
        assert target.password == "testpass"
        assert target.key_file is None

    def test_transport_target_with_key_file(self) -> None:
        """Test TransportTarget creation with SSH key authentication"""
        from api.transports.base import TransportTarget

        key_path = Path("/home/user/.ssh/id_rsa")
        target = TransportTarget(
            host="example.com",
            port=2222,
            username="deploy",
            base_path="/var/scripts",
            key_file=key_path,
        )

        assert target.host == "example.com"
        assert target.port == 2222
        assert target.key_file == key_path
        assert target.password is None

    def test_transport_target_standard_port(self) -> None:
        """Test TransportTarget with standard SSH port"""
        from api.transports.base import TransportTarget

        target = TransportTarget(
            host="localhost",
            port=22,
            username="test",
            base_path="/scripts",
            password="pass",
        )

        assert target.port == 22, "Port should be 22"


class TestTransportResult:
    """Integration tests for TransportResult dataclass"""

    def test_result_success(self) -> None:
        """Test successful TransportResult"""
        from api.transports.base import TransportResult

        result = TransportResult(success=True, files_transferred=5)

        assert result.success is True
        assert result.files_transferred == 5
        assert result.error_type is None
        assert result.error_message is None

    def test_result_failure(self) -> None:
        """Test failed TransportResult"""
        from api.transports.base import TransportErrorType, TransportResult

        result = TransportResult(
            success=False,
            error_type=TransportErrorType.CONNECTION_FAILED,
            error_message="Connection refused",
        )

        assert result.success is False
        assert result.error_type == TransportErrorType.CONNECTION_FAILED
        assert "Connection refused" in result.error_message

    def test_result_with_details(self) -> None:
        """Test TransportResult with extra details"""
        from api.transports.base import TransportResult

        result = TransportResult(
            success=True,
            files_transferred=3,
            bytes_transferred=1024,
            details={"files": ["a.py", "b.js", "c.cjs"]},
        )

        assert result.files_transferred == 3
        assert result.bytes_transferred == 1024
        assert result.details is not None
        assert "files" in result.details
        assert len(result.details["files"]) == 3


class TestTransportErrorTypes:
    """Integration tests for transport error type enumeration"""

    def test_all_error_types_exist(self) -> None:
        """Test all expected error types are defined"""
        from api.transports.base import TransportErrorType

        expected_types = [
            "AUTH_FAILED",
            "CONNECTION_FAILED",
            "TIMEOUT",
            "PERMISSION_DENIED",
            "NOT_FOUND",
            "UNKNOWN",
        ]

        for error_type in expected_types:
            assert hasattr(TransportErrorType, error_type), f"Missing error type: {error_type}"

    def test_error_types_are_unique(self) -> None:
        """Test error type values are unique"""
        from api.transports.base import TransportErrorType

        values = [e.value for e in TransportErrorType]
        assert len(values) == len(set(values)), "Error type values should be unique"


class TestSFTPTransportValidation:
    """Integration tests for SFTP transport config validation"""

    def test_validate_config_requires_host(self) -> None:
        """Test config validation requires host"""
        from api.transports.base import PluginRegistry, TransportTarget

        transport = PluginRegistry.create_instance("sftp")
        assert transport is not None

        target = TransportTarget(
            host="",  # Empty host
            port=22,
            username="test",
            base_path="/scripts",
            password="pass",
        )

        assert transport.validate_config(target) is False

    def test_validate_config_requires_username(self) -> None:
        """Test config validation requires username"""
        from api.transports.base import PluginRegistry, TransportTarget

        transport = PluginRegistry.create_instance("sftp")
        assert transport is not None

        target = TransportTarget(
            host="localhost",
            port=22,
            username="",  # Empty username
            base_path="/scripts",
            password="pass",
        )

        assert transport.validate_config(target) is False

    def test_validate_config_requires_auth(self) -> None:
        """Test config validation requires password or key"""
        from api.transports.base import PluginRegistry, TransportTarget

        transport = PluginRegistry.create_instance("sftp")
        assert transport is not None

        target = TransportTarget(
            host="localhost",
            port=22,
            username="test",
            base_path="/scripts",
            # No password or key_file
        )

        assert transport.validate_config(target) is False

    def test_validate_config_accepts_password_auth(self) -> None:
        """Test config validation accepts password authentication"""
        from api.transports.base import PluginRegistry, TransportTarget

        transport = PluginRegistry.create_instance("sftp")
        assert transport is not None

        target = TransportTarget(
            host="localhost",
            port=22,
            username="test",
            base_path="/scripts",
            password="testpass",
        )

        assert transport.validate_config(target) is True

    @pytest.fixture
    def temp_key_file(self) -> Iterator[Path]:
        """Create a temporary SSH key file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("-----BEGIN RSA PRIVATE KEY-----\n")  # gitleaks:allow
            f.write("FAKE KEY FOR TESTING\n")
            f.write("-----END RSA PRIVATE KEY-----\n")  # gitleaks:allow
            key_path = Path(f.name)

        yield key_path

        # Cleanup
        key_path.unlink(missing_ok=True)

    def test_validate_config_accepts_key_file_auth(self, temp_key_file: Path) -> None:
        """Test config validation accepts SSH key authentication"""
        from api.transports.base import PluginRegistry, TransportTarget

        transport = PluginRegistry.create_instance("sftp")
        assert transport is not None

        target = TransportTarget(
            host="localhost",
            port=22,
            username="test",
            base_path="/scripts",
            key_file=temp_key_file,
        )

        assert transport.validate_config(target) is True

    def test_validate_config_rejects_nonexistent_key(self) -> None:
        """Test config validation rejects non-existent key file"""
        from api.transports.base import PluginRegistry, TransportTarget

        transport = PluginRegistry.create_instance("sftp")
        assert transport is not None

        target = TransportTarget(
            host="localhost",
            port=22,
            username="test",
            base_path="/scripts",
            key_file=Path("/nonexistent/key/file"),
        )

        assert transport.validate_config(target) is False


class TestScriptSyncResult:
    """Integration tests for ScriptSyncResult dataclass"""

    def test_script_sync_result_creation(self) -> None:
        """Test ScriptSyncResult can be created"""
        from api.transports.base import ScriptSyncResult

        result = ScriptSyncResult(success=True, scripts_synced=3)

        assert result.success is True
        assert result.scripts_synced == 3
        assert result.warnings == []

    def test_script_sync_result_with_warnings(self) -> None:
        """Test ScriptSyncResult with warnings"""
        from api.transports.base import ScriptSyncResult

        result = ScriptSyncResult(success=True, scripts_synced=2)
        result.add_warning("Some files were skipped")
        result.add_warning("Permissions warning")

        assert result.success is True
        assert len(result.warnings) == 2
        assert "skipped" in result.warnings[0]

    def test_script_sync_result_failure(self) -> None:
        """Test ScriptSyncResult failure case"""
        from api.transports.base import ScriptSyncResult

        result = ScriptSyncResult(
            success=False,
            scripts_synced=0,
            errors=["Connection failed"],
        )

        assert result.success is False
        assert result.scripts_synced == 0
        assert result.errors == ["Connection failed"]
