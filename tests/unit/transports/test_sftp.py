"""Unit tests for api/transports/sftp.py module

Tests for SFTPTransport class methods using Paramiko mocks.
"""

import socket
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import paramiko
import pytest
from assertpy import assert_that

from api.transports.base import TransportTarget, TransportErrorType
from api.transports.sftp import SFTPTransport


class TestSFTPTransport:
    """Tests for SFTPTransport class"""

    def test_name_property(self) -> None:
        """Test transport name property"""
        transport = SFTPTransport()
        assert_that(transport.name).is_equal_to("sftp")

    def test_upload_files_success(self, temp_dir: Path) -> None:
        """Test successful file upload via SFTP"""
        # Create test files
        file1 = temp_dir / "test1.py"
        file2 = temp_dir / "test2.js"
        file1.write_text("# python")
        file2.write_text("// javascript")

        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock stat to make directory appear to exist
            mock_sftp.stat.return_value = MagicMock()

            result = transport.upload_files(
                target=target,
                files=[file1, file2],
                remote_subdir="workflow_test",
            )

        assert_that(result.success).is_true()
        assert_that(result.files_transferred).is_equal_to(2)
        # Verify put was called for each file
        assert_that(mock_sftp.put.call_count).is_equal_to(2)

    def test_upload_files_connection_error(self, temp_dir: Path) -> None:
        """Test upload handles connection errors"""
        file1 = temp_dir / "test.py"
        file1.write_text("# test")

        target = TransportTarget(
            host="unreachable.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_create.side_effect = socket.error("Connection refused")

            result = transport.upload_files(
                target=target,
                files=[file1],
                remote_subdir="test",
            )

        assert_that(result.success).is_false()
        assert_that(result.error_type).is_equal_to(TransportErrorType.CONNECTION_FAILED)

    def test_upload_files_permission_denied(self, temp_dir: Path) -> None:
        """Test upload handles permission denied errors"""
        file1 = temp_dir / "test.py"
        file1.write_text("# test")

        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/root/scripts",  # no permission
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock mkdir to raise permission denied
            mock_sftp.stat.side_effect = IOError("No such file")
            mock_sftp.mkdir.side_effect = IOError("Permission denied")

            result = transport.upload_files(
                target=target,
                files=[file1],
                remote_subdir="test",
            )

        assert_that(result.success).is_false()
        assert_that(result.error_type).is_equal_to(TransportErrorType.PERMISSION_DENIED)

    def test_upload_files_auth_failure(self, temp_dir: Path) -> None:
        """Test upload handles authentication failures"""
        file1 = temp_dir / "test.py"
        file1.write_text("# test")

        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="wrong_user",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/wrong_key"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_create.side_effect = paramiko.AuthenticationException("Authentication failed")

            result = transport.upload_files(
                target=target,
                files=[file1],
                remote_subdir="test",
            )

        assert_that(result.success).is_false()
        assert_that(result.error_type).is_equal_to(TransportErrorType.AUTH_FAILED)

    def test_upload_files_empty_list(self, temp_dir: Path) -> None:
        """Test upload with empty file list"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        result = transport.upload_files(
            target=target,
            files=[],
            remote_subdir="test",
        )

        assert_that(result.success).is_true()
        assert_that(result.files_transferred).is_equal_to(0)

    def test_upload_files_filters_nonexistent(self, temp_dir: Path) -> None:
        """Test upload filters out non-existent files"""
        existing = temp_dir / "exists.py"
        existing.write_text("# exists")
        nonexistent = temp_dir / "missing.py"  # don't create this

        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock stat to make directory appear to exist
            mock_sftp.stat.return_value = MagicMock()

            result = transport.upload_files(
                target=target,
                files=[existing, nonexistent],
                remote_subdir="test",
            )

        assert_that(result.success).is_true()
        assert_that(result.files_transferred).is_equal_to(1)

    def test_ensure_directory_success(self) -> None:
        """Test ensuring remote directory exists"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock stat to raise IOError (directory doesn't exist)
            mock_sftp.stat.side_effect = IOError("No such file")

            result = transport.ensure_directory(target, "new_workflow")

        assert_that(result.success).is_true()
        # Verify mkdir was called
        assert_that(mock_sftp.mkdir.call_count).is_greater_than(0)

    def test_ensure_directory_permission_denied(self) -> None:
        """Test ensure_directory handles permission denied"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/root/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock stat to raise IOError (directory doesn't exist)
            mock_sftp.stat.side_effect = IOError("No such file")
            # Mock mkdir to raise permission denied
            mock_sftp.mkdir.side_effect = IOError("Permission denied")

            result = transport.ensure_directory(target, "test")

        assert_that(result.success).is_false()
        assert_that(result.error_type).is_equal_to(TransportErrorType.PERMISSION_DENIED)

    def test_test_connection_success(self) -> None:
        """Test connection test success"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            result = transport.test_connection(target)

        assert_that(result.success).is_true()

    def test_test_connection_failure(self) -> None:
        """Test connection test failure"""
        target = TransportTarget(
            host="unreachable.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_create.side_effect = socket.error("Connection refused")

            result = transport.test_connection(target)

        assert_that(result.success).is_false()
        assert_that(result.error_type).is_equal_to(TransportErrorType.CONNECTION_FAILED)

    def test_custom_port(self, temp_dir: Path) -> None:
        """Test upload with custom SSH port"""
        file1 = temp_dir / "test.py"
        file1.write_text("# test")

        target = TransportTarget(
            host="remote.example.com",
            port=2222,  # custom port
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch("paramiko.SSHClient") as MockSSHClient:
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            MockSSHClient.return_value = mock_client

            # Mock stat to make directory appear to exist
            mock_sftp.stat.return_value = MagicMock()

            transport.upload_files(target=target, files=[file1], remote_subdir="test")

        # Verify connect was called with custom port (may be called twice: ensure_directory + upload)
        assert_that(mock_client.connect.call_count).is_greater_than_or_equal_to(1)
        call_kwargs = mock_client.connect.call_args[1]
        assert_that(call_kwargs["port"]).is_equal_to(2222)


class TestTransportTarget:
    """Tests for TransportTarget dataclass"""

    def test_target_creation_with_key(self) -> None:
        """Test TransportTarget creation with key file"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )
        assert_that(target.host).is_equal_to("remote.example.com")
        assert_that(target.port).is_equal_to(22)
        assert_that(target.username).is_equal_to("testuser")
        assert_that(target.key_file).is_not_none()
        assert_that(target.password).is_none()

    def test_target_creation_with_password(self) -> None:
        """Test TransportTarget creation with password"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            password="testpass",  # nosec B105 - test fixture
        )
        assert_that(target.password).is_equal_to("testpass")
        assert_that(target.key_file).is_none()


class TestSetExecutable:
    """Tests for SFTPTransport.set_executable method"""

    def test_set_executable_success(self) -> None:
        """Test setting executable permissions on remote files"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock stat to return file attributes
            mock_attrs = MagicMock()
            mock_attrs.st_mode = 0o644
            mock_sftp.stat.return_value = mock_attrs

            result = transport.set_executable(
                target=target,
                remote_files=["workflow_test/script1.py", "workflow_test/script2.js"],
            )

        assert_that(result.success).is_true()
        assert_that(result.files_transferred).is_equal_to(2)
        # Verify chmod was called
        assert_that(mock_sftp.chmod.call_count).is_equal_to(2)

    def test_set_executable_empty_list(self) -> None:
        """Test set_executable with empty file list returns success"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        # No SSH call should be made for empty list
        result = transport.set_executable(target=target, remote_files=[])

        assert_that(result.success).is_true()

    def test_set_executable_permission_denied(self) -> None:
        """Test set_executable handles permission denied errors on stat"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock stat to return attrs, but chmod raises permission denied
            mock_attrs = MagicMock()
            mock_attrs.st_mode = 0o644
            mock_sftp.stat.return_value = mock_attrs
            mock_sftp.chmod.side_effect = IOError("Permission denied")

            result = transport.set_executable(
                target=target,
                remote_files=["script.py"],
            )

        assert_that(result.success).is_false()
        assert_that(result.error_type).is_equal_to(TransportErrorType.PERMISSION_DENIED)

    def test_set_executable_timeout(self) -> None:
        """Test set_executable handles timeout"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_create.side_effect = socket.timeout("Connection timed out")

            result = transport.set_executable(
                target=target,
                remote_files=["script.py"],
            )

        assert_that(result.success).is_false()
        assert_that(result.error_type).is_equal_to(TransportErrorType.TIMEOUT)
        assert_that(result.error_message).contains("timed out")

    def test_set_executable_custom_port(self) -> None:
        """Test set_executable uses correct port for SSH"""
        target = TransportTarget(
            host="remote.example.com",
            port=2222,  # custom port
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch("paramiko.SSHClient") as MockSSHClient:
            mock_client = MagicMock()
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            MockSSHClient.return_value = mock_client

            # Mock stat to return file attributes
            mock_attrs = MagicMock()
            mock_attrs.st_mode = 0o644
            mock_sftp.stat.return_value = mock_attrs

            transport.set_executable(target=target, remote_files=["script.py"])

        # Verify connect was called with custom port
        mock_client.connect.assert_called_once()
        call_kwargs = mock_client.connect.call_args[1]
        assert_that(call_kwargs["port"]).is_equal_to(2222)

    def test_set_executable_builds_full_paths(self) -> None:
        """Test set_executable builds correct full paths from base_path"""
        target = TransportTarget(
            host="remote.example.com",
            port=22,
            username="testuser",
            base_path="/opt/scripts",
            key_file=Path("/home/user/.ssh/id_rsa"),
        )

        transport = SFTPTransport()

        with patch.object(transport, "_create_ssh_client") as mock_create:
            mock_client = MagicMock(spec=paramiko.SSHClient)
            mock_sftp = MagicMock()
            mock_client.open_sftp.return_value = mock_sftp
            mock_create.return_value = mock_client

            # Mock stat to return file attributes
            mock_attrs = MagicMock()
            mock_attrs.st_mode = 0o644
            mock_sftp.stat.return_value = mock_attrs

            transport.set_executable(
                target=target,
                remote_files=["workflow/script.py"],
            )

        # Should have full path /opt/scripts/workflow/script.py
        mock_sftp.stat.assert_called_with("/opt/scripts/workflow/script.py")


class TestTransportErrorType:
    """Tests for TransportErrorType enum"""

    def test_error_types_exist(self) -> None:
        """Test all error types are defined"""
        assert_that(TransportErrorType.CONNECTION_FAILED.value).is_equal_to("connection_failed")
        assert_that(TransportErrorType.AUTH_FAILED.value).is_equal_to("auth_failed")
        assert_that(TransportErrorType.PERMISSION_DENIED.value).is_equal_to("permission_denied")
        assert_that(TransportErrorType.NOT_FOUND.value).is_equal_to("not_found")
        assert_that(TransportErrorType.TIMEOUT.value).is_equal_to("timeout")
        assert_that(TransportErrorType.UNKNOWN.value).is_equal_to("unknown")
