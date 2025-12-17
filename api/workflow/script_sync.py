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
from .script_parser import ScriptReference, WorkflowScriptParser


@dataclass
class ScriptMapping:
    """Maps local script file to remote path."""

    local_path: Path
    remote_dir: str  # Directory from workflow (e.g., /files/testing/)
    filename: str


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

    # Valid script extensions for n8n Execute Command nodes
    JS_EXTENSIONS = (".js", ".cjs", ".mjs")
    PY_EXTENSIONS = (".py", ".pyw")
    SCRIPT_EXTENSIONS = JS_EXTENSIONS + PY_EXTENSIONS

    def find_local_script(self, filename: str) -> Optional[Path]:
        """Find a single local script file by filename.

        Supports extension fallback: if workflow references 'script.js' but
        local file is 'script.cjs', it will match by stem.

        Args:
            filename: Script filename to find

        Returns:
            Path to existing local script or None
        """
        # Search in scripts directory (exact match first)
        script_path = self.config.scripts_dir / filename
        if script_path.exists():
            return script_path

        # Try recursive search for exact match
        matches = list(self.config.scripts_dir.rglob(filename))
        if matches:
            return matches[0]

        # Try extension fallback - match by stem with alternative extensions
        stem = Path(filename).stem
        original_ext = Path(filename).suffix.lower()

        # Determine which extensions to try based on original
        alt_extensions: tuple[str, ...]
        if original_ext in self.JS_EXTENSIONS:
            alt_extensions = self.JS_EXTENSIONS
        elif original_ext in self.PY_EXTENSIONS:
            alt_extensions = self.PY_EXTENSIONS
        else:
            alt_extensions = self.SCRIPT_EXTENSIONS

        for ext in alt_extensions:
            if ext == original_ext:
                continue  # Already tried exact match
            alt_filename = stem + ext
            # Flat search
            alt_path = self.config.scripts_dir / alt_filename
            if alt_path.exists():
                return alt_path
            # Recursive search
            alt_matches = list(self.config.scripts_dir.rglob(alt_filename))
            if alt_matches:
                return alt_matches[0]

        return None

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
            local = self.find_local_script(script_name)
            if local:
                found.append(local)
        return found

    def get_remote_dir(self, script_path: str) -> str:
        """Determine remote directory for a script.

        - Absolute paths: Use directory from workflow directly
        - Relative paths: Prefix with base_path

        Args:
            script_path: Script path from workflow command

        Returns:
            Remote directory path
        """
        if script_path.startswith("/"):
            return str(Path(script_path).parent)
        else:
            return self.config.remote_base_path

    def build_script_mappings(
        self,
        script_refs: List[ScriptReference],
    ) -> List[ScriptMapping]:
        """Build mappings from local files to remote paths.

        Args:
            script_refs: Script references from workflow parser

        Returns:
            List of ScriptMapping for files that exist locally
        """
        mappings: List[ScriptMapping] = []
        seen_filenames: Set[str] = set()

        for ref in script_refs:
            # Skip duplicates (same script referenced multiple times)
            if ref.filename in seen_filenames:
                continue
            seen_filenames.add(ref.filename)

            # Find local file
            local_path = self.find_local_script(ref.filename)
            if local_path:
                remote_dir = self.get_remote_dir(ref.script_path)
                mappings.append(
                    ScriptMapping(
                        local_path=local_path,
                        remote_dir=remote_dir,
                        filename=ref.filename,
                    )
                )

        return mappings

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

    def _filter_mappings_by_changes(
        self,
        mappings: List[ScriptMapping],
    ) -> List[ScriptMapping]:
        """Filter mappings to only include changed scripts.

        Args:
            mappings: All script mappings

        Returns:
            Filtered mappings (only changed scripts if git detection enabled)
        """
        if not self.config.changed_only or not self._git_detector:
            return mappings

        changes = self._git_detector.get_modified_scripts()
        changed_filenames = {c.filename for c in changes if c.needs_upload}

        return [m for m in mappings if m.filename in changed_filenames]

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

        # Build mappings from local files to remote paths
        all_mappings = self.build_script_mappings(script_refs)

        if not all_mappings:
            result.add_warning(f"No matching scripts found in {self.config.scripts_dir}")
            result.scripts_skipped = len(script_refs)
            return result

        # Filter to changed scripts only (if git detection enabled)
        mappings_to_sync = self._filter_mappings_by_changes(all_mappings)

        if not mappings_to_sync:
            result.add_warning("No scripts need syncing (all unchanged in git)")
            result.scripts_skipped = len(all_mappings)
            return result

        # Dry run: show what would be uploaded
        if self.config.dry_run:
            for mapping in mappings_to_sync:
                remote_path = f"{mapping.remote_dir}/{mapping.filename}"
                result.synced_files.append(f"[DRY RUN] {mapping.filename} -> {remote_path}")
            result.scripts_synced = len(mappings_to_sync)
            result.scripts_skipped = len(all_mappings) - len(mappings_to_sync)
            return result

        # Perform uploads grouped by remote directory
        target = self._build_transport_target()
        total_transferred = 0
        total_bytes = 0

        # Group mappings by remote directory for batch upload
        dir_groups: Dict[str, List[ScriptMapping]] = {}
        for mapping in mappings_to_sync:
            if mapping.remote_dir not in dir_groups:
                dir_groups[mapping.remote_dir] = []
            dir_groups[mapping.remote_dir].append(mapping)

        # Upload each group to its directory
        for remote_dir, group in dir_groups.items():
            files = [m.local_path for m in group]
            # Build rename_map for files that need extension conversion
            # (e.g., local 'script.cjs' -> remote 'script.js' as workflow expects)
            rename_map = {m.local_path: m.filename for m in group if m.local_path.name != m.filename}
            upload_result = self._transport.upload_files(
                target=target,
                files=files,
                remote_subdir=remote_dir,
                create_dirs=True,
                rename_map=rename_map or None,
            )

            if upload_result.success:
                total_transferred += upload_result.files_transferred
                total_bytes += upload_result.bytes_transferred

                # Set executable permissions
                remote_files = [f"{remote_dir}/{m.filename}" for m in group]
                chmod_result = self._transport.set_executable(target, remote_files)
                if not chmod_result.success:
                    result.add_warning(
                        f"Failed to set executable permissions in {remote_dir}: " f"{chmod_result.error_message}"
                    )
            else:
                result.add_error(f"Upload to {remote_dir} failed: {upload_result.error_message}")

        if result.errors:
            return result

        result.scripts_synced = total_transferred
        result.bytes_transferred = total_bytes
        result.synced_files = [m.filename for m in mappings_to_sync]
        result.scripts_skipped = len(all_mappings) - len(mappings_to_sync)

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
