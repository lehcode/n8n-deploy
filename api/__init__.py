"""
n8n_deploy_ - a simple N8N Workflow Manager
Simple n8n workflow deployment tool with SQLite metadata store
"""

from .models import Workflow
from .db import DBApi
from .workflow import WorkflowApi
from . import cli  # Make api.cli accessible for patching in tests
from . import config  # Make api.config accessible for patching in tests
from . import workflow  # Make api.workflow accessible for patching in tests

# Dynamic version from package metadata (set by setuptools_scm from git tags)
try:
    from importlib.metadata import version as _get_version

    __version__ = _get_version("n8n-deploy")
except Exception:
    __version__ = "0.1.5"  # Fallback for development without install

__author__ = "Lehcode"

__all__ = [
    "Workflow",
    "DBApi",
    "WorkflowApi",
    "__version__",
]
