#!/usr/bin/env python3
"""
n8n_deploy_ Configuration Management
"""

import os
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class n8n_deploy_Config:
    """Configuration container for n8n_deploy_ paths and settings"""

    base_folder: Path
    flow_folder: Optional[Path] = None

    @property
    def database_path(self) -> Path:
        """Path to the SQLite database (in app base folder)"""
        return self.base_folder / "n8n-deploy.db"

    @property
    def workflows_path(self) -> Path:
        """Path to workflow files directory (in flow folder)"""
        if self.flow_folder:
            return self.flow_folder
        return self.base_folder / "workflows"

    @property
    def backups_path(self) -> Path:
        """Path to backup files directory (in app base folder)"""
        return self.base_folder / "backups"

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.base_folder.mkdir(parents=True, exist_ok=True)
        self.workflows_path.mkdir(parents=True, exist_ok=True)
        self.backups_path.mkdir(parents=True, exist_ok=True)

    def validate_paths(self) -> None:
        """Validate that paths are accessible and writable"""
        # Validate base folder
        if not self.base_folder.exists():
            raise ValueError(f"Base folder does not exist: {self.base_folder}")
        if not self.base_folder.is_dir():
            raise ValueError(f"Base folder is not a directory: {self.base_folder}")
        if not os.access(self.base_folder, os.W_OK):
            raise ValueError(f"Base folder is not writable: {self.base_folder}")

        # Validate flow folder if specified
        if self.flow_folder:
            if not self.flow_folder.exists():
                raise ValueError(f"Flow folder does not exist: {self.flow_folder}")
            if not self.flow_folder.is_dir():
                raise ValueError(f"Flow folder is not a directory: {self.flow_folder}")
            if not os.access(self.flow_folder, os.W_OK):
                raise ValueError(f"Flow folder is not writable: {self.flow_folder}")


def get_config(
    base_folder: Optional[Union[str, Path]] = None,
    flow_folder: Optional[Union[str, Path]] = None,
) -> n8n_deploy_Config:
    """
    Get n8n_deploy_ configuration with priority order:

    Base folder priority:
    1. Explicit --app-dir parameter (highest priority)
    2. Current working directory (default)

    Flow folder priority:
    1. Explicit --flow-dir parameter (highest priority)
    2. N8N_FLOW_DIR environment variable (if specified)
    3. Same as base folder (default)
    """

    # Base folder resolution
    if base_folder is not None:
        # Explicit parameter has highest priority
        base_path = Path(base_folder).resolve()
    else:
        # Use working directory as default
        base_path = Path.cwd()

    # Flow folder resolution
    if flow_folder is not None:
        # Explicit parameter has highest priority
        flow_path = Path(flow_folder).resolve()
    elif "N8N_FLOW_DIR" in os.environ:
        # Environment variable if specified
        flow_path = Path(os.environ["N8N_FLOW_DIR"]).resolve()
    else:
        # Default: same as base folder
        flow_path = None

    config = n8n_deploy_Config(base_folder=base_path, flow_folder=flow_path)

    # First ensure directories exist, then validate access
    config.ensure_directories()
    config.validate_paths()

    return config


def get_legacy_config() -> n8n_deploy_Config:
    """
    Get legacy configuration (project-relative paths)
    Used for backward compatibility during migration
    """
    # Calculate project root from this file's location
    project_root = Path(__file__).parent.parent

    return n8n_deploy_Config(base_folder=project_root)
