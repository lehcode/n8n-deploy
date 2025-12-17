#!/usr/bin/env python3
"""
Abstract base classes for n8n-deploy transport plugin system.

Provides extensible transport plugin architecture for file synchronization.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type, Union


class TransportErrorType(str, Enum):
    """Types of transport errors."""

    CONNECTION_FAILED = "connection_failed"
    AUTH_FAILED = "auth_failed"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class TransportResult:
    """Result of a transport operation."""

    success: bool
    files_transferred: int = 0
    bytes_transferred: int = 0
    error_type: Optional[TransportErrorType] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    @property
    def is_connection_error(self) -> bool:
        """Check if this is a connection error."""
        return self.error_type == TransportErrorType.CONNECTION_FAILED

    @property
    def is_auth_error(self) -> bool:
        """Check if this is an authentication error."""
        return self.error_type == TransportErrorType.AUTH_FAILED

    @property
    def is_permission_error(self) -> bool:
        """Check if this is a permission error."""
        return self.error_type == TransportErrorType.PERMISSION_DENIED


@dataclass
class TransportTarget:
    """Target configuration for file transfer."""

    host: str
    port: int
    username: str
    base_path: str  # Remote base path

    # Authentication (one of these should be set)
    password: Optional[str] = None
    key_file: Optional[Path] = None
    key_passphrase: Optional[str] = None

    def validate(self) -> bool:
        """Validate that required fields are set."""
        if not self.host or not self.username:
            return False
        if not self.password and not self.key_file:
            return False
        return True


class TransportPlugin(ABC):
    """Abstract base class for file transport plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable plugin description."""
        pass

    @abstractmethod
    def validate_config(self, target: TransportTarget) -> bool:
        """Validate transport configuration.

        Args:
            target: Target configuration

        Returns:
            True if configuration is valid
        """
        pass

    @abstractmethod
    def test_connection(self, target: TransportTarget) -> TransportResult:
        """Test connection to remote server.

        Args:
            target: Target configuration

        Returns:
            TransportResult indicating connection status
        """
        pass

    @abstractmethod
    def upload_files(
        self,
        target: TransportTarget,
        files: List[Path],
        remote_subdir: str = "",
        create_dirs: bool = True,
        rename_map: Optional[Dict[Path, str]] = None,
    ) -> TransportResult:
        """Upload files to remote server.

        Args:
            target: Target configuration
            files: List of local file paths to upload
            remote_subdir: Subdirectory under base_path
            create_dirs: Create directories if they don't exist
            rename_map: Optional mapping of local paths to remote filenames.
                       Use when remote filename should differ from local
                       (e.g., uploading 'script.cjs' as 'script.js').

        Returns:
            TransportResult with operation details
        """
        pass

    @abstractmethod
    def download_files(
        self,
        target: TransportTarget,
        remote_files: List[str],
        local_dir: Path,
    ) -> TransportResult:
        """Download files from remote server.

        Args:
            target: Target configuration
            remote_files: List of remote file paths (relative to base_path)
            local_dir: Local directory to download to

        Returns:
            TransportResult with operation details
        """
        pass

    @abstractmethod
    def ensure_directory(
        self,
        target: TransportTarget,
        remote_dir: str,
    ) -> TransportResult:
        """Ensure remote directory exists.

        Args:
            target: Target configuration
            remote_dir: Directory path (relative to base_path)

        Returns:
            TransportResult indicating success/failure
        """
        pass

    @abstractmethod
    def list_remote_files(
        self,
        target: TransportTarget,
        remote_dir: str = "",
        extensions: Optional[List[str]] = None,
    ) -> TransportResult:
        """List files in remote directory.

        Args:
            target: Target configuration
            remote_dir: Directory path (relative to base_path)
            extensions: Filter by file extensions (e.g., ['.js', '.py'])

        Returns:
            TransportResult with file list in details['files']
        """
        pass

    @abstractmethod
    def set_executable(
        self,
        target: TransportTarget,
        remote_files: List[str],
    ) -> TransportResult:
        """Set executable permissions on remote files.

        Args:
            target: Target configuration
            remote_files: List of remote file paths (relative to base_path)

        Returns:
            TransportResult indicating success/failure
        """
        pass


class PluginRegistry:
    """Registry for transport plugins."""

    _plugins: ClassVar[Dict[str, Type[TransportPlugin]]] = {}

    @classmethod
    def register(cls, plugin_class: Type[TransportPlugin]) -> Type[TransportPlugin]:
        """Register a plugin class.

        Args:
            plugin_class: TransportPlugin subclass

        Returns:
            The registered class (for decorator usage)
        """
        # Create temporary instance to get name
        instance = plugin_class()
        cls._plugins[instance.name] = plugin_class
        return plugin_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[TransportPlugin]]:
        """Get a plugin class by name.

        Args:
            name: Plugin name

        Returns:
            Plugin class or None
        """
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls) -> List[str]:
        """List registered plugin names."""
        return list(cls._plugins.keys())

    @classmethod
    def create_instance(cls, name: str) -> Optional[TransportPlugin]:
        """Create an instance of a plugin.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None
        """
        plugin_class = cls.get(name)
        return plugin_class() if plugin_class else None

    @classmethod
    def get_plugin_info(cls) -> List[Dict[str, str]]:
        """Get information about all registered plugins.

        Returns:
            List of dicts with 'name' and 'description' keys
        """
        info = []
        for plugin_class in cls._plugins.values():
            instance = plugin_class()
            info.append({"name": instance.name, "description": instance.description})
        return info


@dataclass
class ScriptSyncResult:
    """Result of script synchronization operation."""

    success: bool
    scripts_synced: int = 0
    scripts_skipped: int = 0
    bytes_transferred: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    synced_files: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.success = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
