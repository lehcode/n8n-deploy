#!/usr/bin/env python3
"""
Script synchronization orchestration for n8n-deploy.

Coordinates workflow parsing, git change detection, and file transport
to sync scripts referenced by Execute Command nodes.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..transports.base import (
    PluginRegistry,
    ScriptSyncResult,
    TransportPlugin,
    TransportTarget,
)
from .script_git import GitScriptDetector, is_git_repository
from .script_parser import WorkflowScriptParser


@dataclass
class ScriptSyncConfig:
    """Configuration for script synchronization."""

    scripts_dir: Path
    remote_base_path: str
    workflow_name: str  # Sanitized workflow name for remote subdir

    # Transport configuration
    transport: str = "scp"
    host: str = ""
    port: int = 22
    username: str = ""
    password: Optional[str] = None
    key_file: Optional[Path] = None

    # Sync options
    changed_only: bool = True
    dry_run: bool = False

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: List[str] = []

        if not self.scripts_dir.exists():
            errors.append(f"Scripts directory does not exist: {self.scripts_dir}")
        elif not self.scripts_dir.is_dir():
            errors.append(f"Scripts path is not a directory: {self.scripts_dir}")

        if not self.host:
            errors.append("Remote host is required")
        if not self.username:
            errors.append("Remote username is required")
        if not self.password and not self.key_file:
            errors.append("Either password or SSH key file is required")
        if self.key_file and not self.key_file.exists():
            errors.append(f"SSH key file does not exist: {self.key_file}")

        return errors


class ScriptSyncManager:
    """Manages script synchronization for workflows."""

    # Characters allowed in sanitized workflow names
    SAFE_CHARS: Set[str] = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

    def __init__(
        self,
        config: ScriptSyncConfig,
        transport_plugin: Optional[TransportPlugin] = None,
    ) -> None:
        """Initialize script sync manager.

        Args:
            config: Synchronization configuration
            transport_plugin: Optional pre-configured transport plugin

        Raises:
            ValueError: If configuration is invalid or transport plugin not found
        """
        self.config = config

        # Validate configuration
        validation_errors = config.validate()
        if validation_errors:
            raise ValueError("Invalid configuration: " + "; ".join(validation_errors))

        # Initialize transport plugin
        if transport_plugin:
            self._transport = transport_plugin
        else:
            plugin = PluginRegistry.create_instance(config.transport)
            if not plugin:
                available = ", ".join(PluginRegistry.list_plugins())
                raise ValueError(f"Unknown transport plugin: {config.transport}. " f"Available: {available}")
            self._transport = plugin

        # Initialize git detector if using change detection
        self._git_detector: Optional[GitScriptDetector] = None
        if config.changed_only and is_git_repository(config.scripts_dir):
            try:
                self._git_detector = GitScriptDetector(config.scripts_dir)
            except ValueError:
                # Not a git repo - will sync all files
                pass

    def _build_transport_target(self) -> TransportTarget:
        """Build transport target from config."""
        return TransportTarget(
            host=self.config.host,
            port=self.config.port,
            username=self.config.username,
            base_path=self.config.remote_base_path,
            password=self.config.password,
            key_file=self.config.key_file,
        )

    @staticmethod
    def sanitize_workflow_name(name: str) -> str:
        """Sanitize workflow name for use as directory name.

        Args:
            name: Original workflow name

        Returns:
            Sanitized name safe for use as directory name
        """
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        # Replace spaces with underscores, remove other unsafe chars
        sanitized = name.replace(" ", "_")
        sanitized = "".join(c if c in safe_chars else "_" for c in sanitized)
        # Collapse multiple underscores
        sanitized = re.sub(r"_+", "_", sanitized)
        return sanitized.strip("_") or "unnamed_workflow"

    def find_local_scripts(
        self,
        workflow_scripts: Set[str],
    ) -> List[Path]:
        """Find local script files matching workflow references.

        Args:
            workflow_scripts: Set of script filenames from workflow

        Returns:
            List of paths to existing local scripts
        """
        found: List[Path] = []

        for script_name in workflow_scripts:
            # Search in scripts directory (flat and recursive)
            script_path = self.config.scripts_dir / script_name
            if script_path.exists():
                found.append(script_path)
            else:
                # Try recursive search
                matches = list(self.config.scripts_dir.rglob(script_name))
                if matches:
                    found.append(matches[0])

        return found

    def get_scripts_to_sync(
        self,
        workflow_scripts: Set[str],
    ) -> List[Path]:
        """Get list of scripts that need syncing.

        Args:
            workflow_scripts: Set of script filenames from workflow

        Returns:
            List of script paths to sync
        """
        local_scripts = self.find_local_scripts(workflow_scripts)

        if not self.config.changed_only or not self._git_detector:
            return local_scripts

        # Filter to changed scripts only
        changes = self._git_detector.get_modified_scripts()
        changed_filenames = {c.filename for c in changes if c.needs_upload}

        return [s for s in local_scripts if s.name in changed_filenames]

    def sync_scripts(
        self,
        workflow_data: Dict[str, Any],
    ) -> ScriptSyncResult:
        """Synchronize scripts for a workflow.

        Args:
            workflow_data: Parsed workflow JSON data

        Returns:
            ScriptSyncResult with operation details
        """
        result = ScriptSyncResult(success=True)

        # Parse workflow for script references
        parser = WorkflowScriptParser(workflow_data)
        script_refs = parser.parse_scripts()

        if not script_refs:
            result.add_warning("No Execute Command nodes with scripts found")
            return result

        workflow_scripts = parser.get_script_filenames()
        scripts_to_sync = self.get_scripts_to_sync(workflow_scripts)

        if not scripts_to_sync:
            if self.config.changed_only and self._git_detector:
                result.add_warning("No scripts need syncing (all unchanged in git)")
            else:
                result.add_warning(f"No matching scripts found in {self.config.scripts_dir}")
            result.scripts_skipped = len(workflow_scripts)
            return result

        # Build remote subdirectory from workflow name
        workflow_name = self.sanitize_workflow_name(str(workflow_data.get("name", "unknown")))
        remote_subdir = workflow_name

        if self.config.dry_run:
            for script in scripts_to_sync:
                result.synced_files.append(f"[DRY RUN] {script.name}")
            result.scripts_synced = len(scripts_to_sync)
            result.scripts_skipped = len(workflow_scripts) - len(scripts_to_sync)
            return result

        # Perform upload
        target = self._build_transport_target()
        upload_result = self._transport.upload_files(
            target=target,
            files=scripts_to_sync,
            remote_subdir=remote_subdir,
            create_dirs=True,
        )

        if upload_result.success:
            # Set executable permissions on uploaded scripts
            remote_files = [f"{remote_subdir}/{s.name}" for s in scripts_to_sync]
            chmod_result = self._transport.set_executable(target, remote_files)
            if not chmod_result.success:
                result.add_warning(f"Failed to set executable permissions: {chmod_result.error_message}")

            result.scripts_synced = upload_result.files_transferred
            result.bytes_transferred = upload_result.bytes_transferred
            result.synced_files = [s.name for s in scripts_to_sync]
            result.scripts_skipped = len(workflow_scripts) - len(scripts_to_sync)
        else:
            result.add_error(f"Upload failed: {upload_result.error_message}")

        return result

    def test_connection(self) -> ScriptSyncResult:
        """Test connection to remote server.

        Returns:
            ScriptSyncResult indicating connection status
        """
        result = ScriptSyncResult(success=True)
        target = self._build_transport_target()

        conn_result = self._transport.test_connection(target)
        if not conn_result.success:
            result.add_error(f"Connection failed: {conn_result.error_message}")

        return result


def create_sync_manager_from_cli(
    scripts_dir: str,
    remote_base_path: str,
    workflow_name: str,
    host: str,
    username: str,
    port: int = 22,
    key_file: Optional[str] = None,
    password: Optional[str] = None,
    transport: str = "scp",
    changed_only: bool = True,
    dry_run: bool = False,
) -> ScriptSyncManager:
    """Factory function to create ScriptSyncManager from CLI arguments.

    Args:
        scripts_dir: Local scripts directory path
        remote_base_path: Remote base path for scripts
        workflow_name: Workflow name (for subdirectory)
        host: Remote host
        username: Remote username
        port: SSH port
        key_file: Optional SSH key file path
        password: Optional password
        transport: Transport plugin name
        changed_only: Only sync changed files
        dry_run: Don't actually transfer files

    Returns:
        Configured ScriptSyncManager
    """
    config = ScriptSyncConfig(
        scripts_dir=Path(scripts_dir).resolve(),
        remote_base_path=remote_base_path,
        workflow_name=ScriptSyncManager.sanitize_workflow_name(workflow_name),
        transport=transport,
        host=host,
        port=port,
        username=username,
        password=password,
        key_file=Path(key_file).expanduser() if key_file else None,
        changed_only=changed_only,
        dry_run=dry_run,
    )

    return ScriptSyncManager(config)
