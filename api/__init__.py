"""
n8n_deploy_ - a simple N8N Workflow Manager
Simple n8n wf deployment tool with SQLite metadata store
"""

from .models import Workflow
from .db import DBApi
from .workflow import WorkflowApi

# Dynamic version from package metadata (set by setuptools_scm from git tags)
try:
    from importlib.metadata import version as _get_version

    __version__ = _get_version("n8n-deploy")
except Exception:
    __version__ = "0.0.0"  # Fallback for development without install

__author__ = "Lehcode"

__all__ = [
    "Workflow",
    "DBApi",
    "WorkflowApi",
    "__version__",
]
