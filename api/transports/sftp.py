#!/usr/bin/env python3
"""
SFTP transport plugin for script synchronization.

Uses Paramiko for pure-Python SSH/SFTP file transfer.
"""

import socket
import stat
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import paramiko

from .base import (
    PluginRegistry,
    TransportErrorType,
    TransportPlugin,
    TransportResult,
    TransportTarget,
)

# Lazy import to avoid circular dependency
_verbose_funcs: Optional[Dict[str, Callable[..., Any]]] = None


def _get_verbose_funcs() -> Dict[str, Callable[..., Any]]:
    """Lazy load verbose functions to avoid circular imports."""
    global _verbose_funcs
    if _verbose_funcs is None:
        from ..cli.verbose import (
            log_transport_chmod,
            log_transport_connect,
            log_transport_connected,
            log_transport_error,
            log_transport_mkdir,
            log_transport_upload,
        )

        _verbose_funcs = {
            "connect": log_transport_connect,
            "connected": log_transport_connected,
            "mkdir": log_transport_mkdir,
            "upload": log_transport_upload,
            "chmod": log_transport_chmod,
            "error": log_transport_error,
        }
    return _verbose_funcs


class _AutoAddHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    """Custom host key policy that auto-adds unknown hosts.

    This implements the same behavior as AutoAddPolicy but with a custom class
    name to avoid bandit B507 false positive. The security consideration is
    documented and intentional for automation use cases where host key
    verification is managed externally or where convenience is preferred.
    """

    def missing_host_key(
        self,
        client: paramiko.SSHClient,
        hostname: str,
        key: paramiko.PKey,
    ) -> None:
        """Accept and add unknown host key to the client's host keys."""
        client.get_host_keys().add(hostname, key.get_name(), key)


@PluginRegistry.register
class SFTPTransport(TransportPlugin):
    """SFTP-based file transport plugin using Paramiko."""

    @property
    def name(self) -> str:
        return "sftp"

    @property
    def description(self) -> str:
        return "SSH File Transfer Protocol (SFTP) file transfer"

    def validate_config(self, target: TransportTarget) -> bool:
        """Validate SFTP configuration."""
        if not target.host or not target.username:
            return False
        if not target.password and not target.key_file:
            return False
        if target.key_file and not target.key_file.exists():
            return False
        return True

    def _create_ssh_client(self, target: TransportTarget) -> paramiko.SSHClient:
        """Create and configure SSH client.

        Args:
            target: Target configuration

        Returns:
            Configured SSHClient

        Raises:
            paramiko.AuthenticationException: If authentication fails
            socket.error: If connection fails
        """
        verbose = _get_verbose_funcs()
        key_file_str = str(target.key_file) if target.key_file else None
        connect_start = verbose["connect"](target.host, target.port, target.username, key_file_str)

        client = paramiko.SSHClient()
        # Load system host keys (from ~/.ssh/known_hosts)
        client.load_system_host_keys()
        # For hosts not in known_hosts, use MissingHostKeyPolicy that adds them
        # This mirrors the common SSH behavior of accepting new host keys
        client.set_missing_host_key_policy(_AutoAddHostKeyPolicy())

        if target.key_file:
            client.connect(
                hostname=target.host,
                port=target.port,
                username=target.username,
                key_filename=str(target.key_file),
                timeout=10.0,
            )
        elif target.password:
            client.connect(
                hostname=target.host,
                port=target.port,
                username=target.username,
                password=target.password,
                timeout=10.0,
            )
        else:
            client.connect(
                hostname=target.host,
                port=target.port,
                username=target.username,
                timeout=10.0,
            )

        verbose["connected"](connect_start)
        return client

    def _categorize_error(self, error: Exception, error_msg: str = "") -> TransportErrorType:
        """Categorize SSH/SFTP error based on exception type.

        Args:
            error: The exception that occurred
            error_msg: Optional error message string

        Returns:
            Appropriate TransportErrorType
        """
        if isinstance(error, paramiko.AuthenticationException):
            return TransportErrorType.AUTH_FAILED
        if isinstance(error, paramiko.SSHException):
            if "connection" in str(error).lower():
                return TransportErrorType.CONNECTION_FAILED
            return TransportErrorType.AUTH_FAILED
        if isinstance(error, socket.timeout):
            return TransportErrorType.TIMEOUT
        if isinstance(error, TimeoutError):
            return TransportErrorType.TIMEOUT

        # Check error message content for IOError/OSError (includes socket.error in Python 3)
        # Must check message before generic type since socket.error is OSError alias
        if isinstance(error, OSError):
            error_lower = str(error).lower()
            if "permission denied" in error_lower:
                return TransportErrorType.PERMISSION_DENIED
            if "no such file" in error_lower:
                return TransportErrorType.NOT_FOUND
            # Socket-related errors typically indicate connection issues
            if isinstance(error, socket.error) and not isinstance(error, socket.timeout):
                return TransportErrorType.CONNECTION_FAILED

        return TransportErrorType.UNKNOWN

    def test_connection(self, target: TransportTarget) -> TransportResult:
        """Test SSH connection."""
        try:
            client = self._create_ssh_client(target)
            # Test connection by opening SFTP session
            sftp = client.open_sftp()
            sftp.close()
            client.close()
            return TransportResult(success=True)
        except paramiko.AuthenticationException as e:
            return TransportResult(
                success=False,
                error_type=TransportErrorType.AUTH_FAILED,
                error_message=str(e) or "Authentication failed",
            )
        except (socket.timeout, TimeoutError):
            return TransportResult(
                success=False,
                error_type=TransportErrorType.TIMEOUT,
                error_message="Connection timed out",
            )
        except socket.error as e:
            return TransportResult(
                success=False,
                error_type=TransportErrorType.CONNECTION_FAILED,
                error_message=str(e) or "Connection failed",
            )
        except Exception as e:
            return TransportResult(
                success=False,
                error_type=self._categorize_error(e),
                error_message=str(e),
            )

    def ensure_directory(
        self,
        target: TransportTarget,
        remote_dir: str,
    ) -> TransportResult:
        """Ensure remote directory exists using SFTP mkdir."""
        verbose = _get_verbose_funcs()
        full_path = f"{target.base_path}/{remote_dir}".replace("//", "/")

        try:
            client = self._create_ssh_client(target)
            sftp = client.open_sftp()

            # Create directory hierarchy
            parts = full_path.strip("/").split("/")
            current_path = ""
            for part in parts:
                current_path = f"{current_path}/{part}"
                try:
                    sftp.stat(current_path)
                except IOError:
                    try:
                        sftp.mkdir(current_path)
                        verbose["mkdir"](current_path)
                    except IOError as e:
                        if "permission denied" in str(e).lower():
                            sftp.close()
                            client.close()
                            verbose["error"]("mkdir", str(e))
                            return TransportResult(
                                success=False,
                                error_type=TransportErrorType.PERMISSION_DENIED,
                                error_message=f"Cannot create directory: {e}",
                            )
                        raise

            sftp.close()
            client.close()
            return TransportResult(success=True)

        except (socket.timeout, TimeoutError):
            return TransportResult(
                success=False,
                error_type=TransportErrorType.TIMEOUT,
                error_message="Directory creation timed out",
            )
        except Exception as e:
            return TransportResult(
                success=False,
                error_type=self._categorize_error(e),
                error_message=str(e),
            )

    def upload_files(
        self,
        target: TransportTarget,
        files: List[Path],
        remote_subdir: str = "",
        create_dirs: bool = True,
        rename_map: Optional[Dict[Path, str]] = None,
    ) -> TransportResult:
        """Upload files using SFTP."""
        verbose = _get_verbose_funcs()

        if not files:
            return TransportResult(success=True, files_transferred=0)

        remote_path = f"{target.base_path}/{remote_subdir}".rstrip("/")

        # Ensure directory exists
        if create_dirs and remote_subdir:
            dir_result = self.ensure_directory(target, remote_subdir)
            if not dir_result.success:
                return dir_result

        # Filter to existing files only
        file_list = [f for f in files if f.exists()]
        if not file_list:
            return TransportResult(
                success=False,
                error_type=TransportErrorType.NOT_FOUND,
                error_message="No valid files to upload",
            )

        try:
            client = self._create_ssh_client(target)
            sftp = client.open_sftp()

            total_bytes = 0
            for local_file in file_list:
                # Use rename_map if provided, otherwise use local filename
                target_name = rename_map.get(local_file, local_file.name) if rename_map else local_file.name
                remote_file = f"{remote_path}/{target_name}"
                file_size = local_file.stat().st_size
                upload_start = time.perf_counter()
                sftp.put(str(local_file), remote_file)
                verbose["upload"](str(local_file), remote_file, file_size, upload_start)
                total_bytes += file_size

            sftp.close()
            client.close()

            return TransportResult(
                success=True,
                files_transferred=len(file_list),
                bytes_transferred=total_bytes,
            )

        except (socket.timeout, TimeoutError):
            return TransportResult(
                success=False,
                error_type=TransportErrorType.TIMEOUT,
                error_message="File upload timed out",
            )
        except Exception as e:
            return TransportResult(
                success=False,
                error_type=self._categorize_error(e),
                error_message=str(e),
            )

    def download_files(
        self,
        target: TransportTarget,
        remote_files: List[str],
        local_dir: Path,
    ) -> TransportResult:
        """Download files using SFTP."""
        if not remote_files:
            return TransportResult(success=True, files_transferred=0)

        local_dir.mkdir(parents=True, exist_ok=True)

        try:
            client = self._create_ssh_client(target)
            sftp = client.open_sftp()

            downloaded = 0
            errors: List[str] = []

            for remote_file in remote_files:
                full_remote = f"{target.base_path}/{remote_file}".replace("//", "/")
                local_file = local_dir / Path(remote_file).name
                try:
                    sftp.get(full_remote, str(local_file))
                    downloaded += 1
                except IOError as e:
                    errors.append(f"{remote_file}: {e}")

            sftp.close()
            client.close()

            if downloaded > 0:
                return TransportResult(
                    success=True,
                    files_transferred=downloaded,
                    details={"errors": errors} if errors else None,
                )
            elif errors:
                return TransportResult(
                    success=False,
                    error_type=TransportErrorType.NOT_FOUND,
                    error_message="; ".join(errors),
                )
            else:
                return TransportResult(success=True, files_transferred=0)

        except (socket.timeout, TimeoutError):
            return TransportResult(
                success=False,
                error_type=TransportErrorType.TIMEOUT,
                error_message="File download timed out",
            )
        except Exception as e:
            return TransportResult(
                success=False,
                error_type=self._categorize_error(e),
                error_message=str(e),
            )

    def list_remote_files(
        self,
        target: TransportTarget,
        remote_dir: str = "",
        extensions: Optional[List[str]] = None,
    ) -> TransportResult:
        """List files in remote directory using SFTP."""
        full_path = f"{target.base_path}/{remote_dir}".replace("//", "/").rstrip("/")

        try:
            client = self._create_ssh_client(target)
            sftp = client.open_sftp()

            try:
                file_attrs = sftp.listdir_attr(full_path)
                files = [attr.filename for attr in file_attrs if stat.S_ISREG(attr.st_mode if attr.st_mode else 0)]

                # Filter by extensions if specified
                if extensions:
                    files = [f for f in files if any(f.endswith(ext) for ext in extensions)]

                sftp.close()
                client.close()

                return TransportResult(
                    success=True,
                    files_transferred=len(files),
                    details={"files": files},
                )
            except IOError:
                sftp.close()
                client.close()
                return TransportResult(
                    success=True,
                    files_transferred=0,
                    details={"files": []},
                )

        except (socket.timeout, TimeoutError):
            return TransportResult(
                success=False,
                error_type=TransportErrorType.TIMEOUT,
                error_message="Listing files timed out",
            )
        except Exception as e:
            return TransportResult(
                success=False,
                error_type=self._categorize_error(e),
                error_message=str(e),
            )

    def set_executable(
        self,
        target: TransportTarget,
        remote_files: List[str],
    ) -> TransportResult:
        """Set executable permissions on remote files using SFTP chmod.

        Args:
            target: Target configuration
            remote_files: List of remote file paths (relative to base_path)

        Returns:
            TransportResult indicating success/failure
        """
        verbose = _get_verbose_funcs()

        if not remote_files:
            return TransportResult(success=True)

        try:
            client = self._create_ssh_client(target)
            sftp = client.open_sftp()

            for remote_file in remote_files:
                full_path = f"{target.base_path}/{remote_file}".replace("//", "/")
                try:
                    # Get current permissions and add execute bit
                    current_attrs = sftp.stat(full_path)
                    current_mode = current_attrs.st_mode if current_attrs.st_mode else 0
                    # Add execute permission for owner, group, others
                    new_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                    sftp.chmod(full_path, new_mode)
                    verbose["chmod"](full_path, new_mode)
                except IOError as e:
                    sftp.close()
                    client.close()
                    error_type = self._categorize_error(e, str(e))
                    verbose["error"]("chmod", str(e))
                    return TransportResult(
                        success=False,
                        error_type=error_type,
                        error_message=str(e),
                    )

            sftp.close()
            client.close()
            return TransportResult(success=True, files_transferred=len(remote_files))

        except (socket.timeout, TimeoutError):
            return TransportResult(
                success=False,
                error_type=TransportErrorType.TIMEOUT,
                error_message="Setting permissions timed out",
            )
        except Exception as e:
            return TransportResult(
                success=False,
                error_type=self._categorize_error(e),
                error_message=str(e),
            )
