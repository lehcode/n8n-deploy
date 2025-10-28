#!/usr/bin/env python3
"""
n8n_deploy_ Configuration Management
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

# Import dotenv if available (ENVIRONMENT check happens at runtime in get_config)
try:
    from dotenv import load_dotenv

    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


@dataclass
class AppConfig:
    """Configuration container for n8n_deploy_ paths and settings"""

    base_folder: Path
    flow_folder: Optional[Path] = None
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
    flow_folder: Optional[Union[str, Path]] = None,
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
    3. Current working directory (default)

    n8n URL priority:
    1. Explicit --remote parameter (highest priority)
    2. N8N_SERVER_URL environment variable
    3. (none - must be specified)

    Database filename priority:
    1. Explicit --db-filename parameter (highest priority)
    2. N8N_DEPLOY_DB_FILENAME environment variable
    3. n8n-deploy.db (default)
    """
    # Load .env file if available, then check ENVIRONMENT variable
    if HAS_DOTENV:
        load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
        # Only use .env values if ENVIRONMENT=development
        if os.getenv("ENVIRONMENT", "").lower() != "development":
            # Clear .env-loaded vars in production mode (keep system env vars)
            pass  # For now, just load but document that ENVIRONMENT should be set

    if base_folder is not None:
        base_path = Path(base_folder).resolve()
    elif "N8N_DEPLOY_DATA_DIR" in os.environ:
        base_path = Path(os.environ["N8N_DEPLOY_DATA_DIR"]).resolve()
        # Default to cwd if path doesn't exist or isn't a directory
        if not base_path.exists() or not base_path.is_dir():
            base_path = Path.cwd()
    else:
        base_path = Path.cwd()

    if flow_folder is not None:
        flow_path = Path(flow_folder).resolve()
    elif "N8N_DEPLOY_FLOWS_DIR" in os.environ:
        flow_path = Path(os.environ["N8N_DEPLOY_FLOWS_DIR"]).resolve()
        # Default to cwd if path doesn't exist or isn't a directory
        if not flow_path.exists() or not flow_path.is_dir():
            flow_path = Path.cwd()
    else:
        flow_path = Path.cwd()

    if n8n_url is not None:
        api_url = n8n_url.rstrip("/")
        if not api_url.startswith("http"):
            api_url = f"http://{api_url}"
    elif "N8N_SERVER_URL" in os.environ:
        api_url = os.environ["N8N_SERVER_URL"].rstrip("/")
        if not api_url.startswith("http"):
            api_url = f"http://{api_url}"
    else:
        api_url = None

    # Database filename resolution
    if db_filename is not None:
        filename = db_filename
    elif "N8N_DEPLOY_DB_FILENAME" in os.environ:
        filename = os.environ["N8N_DEPLOY_DB_FILENAME"]
    else:
        filename = "n8n-deploy.db"

    config = AppConfig(base_folder=base_path, flow_folder=flow_path, n8n_url=api_url, db_filename=filename)

    config.ensure_directories()
    config.validate_paths()

    return config
