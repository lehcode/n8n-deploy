#!/usr/bin/env python3
"""
n8n_deploy_ Configuration Management
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union


class _NotProvided:
    """Sentinel to distinguish 'not provided' from None or explicit value.

    Used to detect when --flow-dir was not specified by user,
    allowing fallback to DB-stored workflow paths.
    """

    pass


NOT_PROVIDED: _NotProvided = _NotProvided()

# Import dotenv if available (ENVIRONMENT check happens at runtime in get_config)
try:
    from dotenv import load_dotenv

    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


def _resolve_base_path(base_folder: Optional[Union[str, Path]]) -> Path:
    """Resolve base folder path from parameter or environment.

    Priority:
    1. Explicit base_folder parameter
    2. N8N_DEPLOY_DATA_DIR environment variable
    3. Current working directory (default)
    """
    if base_folder is not None:
        return Path(base_folder).resolve()

    if "N8N_DEPLOY_DATA_DIR" in os.environ:
        base_path = Path(os.environ["N8N_DEPLOY_DATA_DIR"]).resolve()
        if base_path.exists() and base_path.is_dir():
            return base_path

    return Path.cwd()


def _resolve_flow_path(
    flow_folder: Optional[Union[str, Path, "_NotProvided"]],
) -> tuple[Optional[Path], bool]:
    """Resolve flow folder path from parameter or environment.

    Returns:
        Tuple of (resolved path or None, is_explicit flag)

    Priority:
    1. Explicit flow_folder parameter
    2. N8N_DEPLOY_FLOWS_DIR environment variable
    3. None (defer to DB-stored workflow file_folder)
    """
    if not isinstance(flow_folder, _NotProvided):
        if flow_folder is not None:
            return Path(flow_folder).resolve(), True
        return None, True

    if "N8N_DEPLOY_FLOWS_DIR" in os.environ:
        flow_path = Path(os.environ["N8N_DEPLOY_FLOWS_DIR"]).resolve()
        if flow_path.exists() and flow_path.is_dir():
            return flow_path, True

    return None, False


def _resolve_n8n_url(n8n_url: Optional[str]) -> Optional[str]:
    """Resolve n8n API URL from parameter or environment.

    Priority:
    1. Explicit n8n_url parameter
    2. N8N_SERVER_URL environment variable
    3. None
    """
    url = n8n_url if n8n_url is not None else os.environ.get("N8N_SERVER_URL")

    if url is None:
        return None

    url = url.rstrip("/")
    if not url.startswith("http"):
        url = f"http://{url}"
    return url


def _resolve_db_filename(db_filename: Optional[str]) -> str:
    """Resolve database filename from parameter or environment.

    Priority:
    1. Explicit db_filename parameter
    2. N8N_DEPLOY_DB_FILENAME environment variable
    3. n8n-deploy.db (default)
    """
    if db_filename is not None:
        return db_filename
    return os.environ.get("N8N_DEPLOY_DB_FILENAME", "n8n-deploy.db")


@dataclass
class AppConfig:
    """Configuration container for n8n_deploy_ paths and settings"""

    base_folder: Path
    flow_folder: Optional[Path] = None
    flow_folder_explicit: bool = False  # True if user provided --flow-dir or env var
    n8n_url: Optional[str] = None
    backup_dir: Optional[Path] = None
    db_filename: str = "n8n-deploy.db"

    @property
    def database_path(self) -> Path:
        return self.base_folder / self.db_filename

    @property
    def workflows_path(self) -> Path:
        if self.flow_folder:
            return self.flow_folder
        return self.base_folder

    @property
    def backups_path(self) -> Path:
        if self.backup_dir:
            return self.backup_dir
        return self.base_folder

    @property
    def n8n_api_url(self) -> str:
        if self.n8n_url:
            return self.n8n_url.rstrip("/")
        return os.environ.get("N8N_API_URL", "").rstrip("/")

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist"""
        self.base_folder.mkdir(parents=True, exist_ok=True)
        self.workflows_path.mkdir(parents=True, exist_ok=True)
        self.backups_path.mkdir(parents=True, exist_ok=True)

    def validate_paths(self) -> None:
        """Validate that paths are accessible and writable"""
        if not self.base_folder.exists():
            raise ValueError(f"Base folder does not exist: {self.base_folder}")
        if not self.base_folder.is_dir():
            raise ValueError(f"Base folder is not a directory: {self.base_folder}")
        if not os.access(self.base_folder, os.W_OK):
            raise ValueError(f"Base folder is not writable: {self.base_folder}")

        if self.flow_folder:
            if not self.flow_folder.exists():
                raise ValueError(f"Flow folder does not exist: {self.flow_folder}")
            if not self.flow_folder.is_dir():
                raise ValueError(f"Flow folder is not a directory: {self.flow_folder}")
            if not os.access(self.flow_folder, os.W_OK):
                raise ValueError(f"Flow folder is not writable: {self.flow_folder}")


def get_config(
    base_folder: Optional[Union[str, Path]] = None,
    flow_folder: Optional[Union[str, Path, _NotProvided]] = NOT_PROVIDED,
    n8n_url: Optional[str] = None,
    db_filename: Optional[str] = None,
) -> AppConfig:
    """
    Get n8n_deploy_ configuration with priority order:

    Base folder priority:
    1. Explicit --data-dir parameter (highest priority)
    2. N8N_DEPLOY_DATA_DIR environment variable
    3. Current working directory (default)

    Flow folder priority:
    1. Explicit --flow-dir parameter (highest priority)
    2. N8N_DEPLOY_FLOWS_DIR environment variable
    3. DB-stored workflow file_folder (when not explicit)
    4. Current working directory (fallback with warning)

    n8n URL priority:
    1. Explicit --remote parameter (highest priority)
    2. N8N_SERVER_URL environment variable
    3. (none - must be specified)

    Database filename priority:
    1. Explicit --db-filename parameter (highest priority)
    2. N8N_DEPLOY_DB_FILENAME environment variable
    3. n8n-deploy.db (default)
    """
    # Load .env file if available
    if HAS_DOTENV:
        load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)

    # Resolve all configuration values using helper functions
    base_path = _resolve_base_path(base_folder)
    flow_path, flow_explicit = _resolve_flow_path(flow_folder)
    api_url = _resolve_n8n_url(n8n_url)
    filename = _resolve_db_filename(db_filename)

    config = AppConfig(
        base_folder=base_path,
        flow_folder=flow_path,
        flow_folder_explicit=flow_explicit,
        n8n_url=api_url,
        db_filename=filename,
    )

    config.ensure_directories()
    config.validate_paths()

    return config
