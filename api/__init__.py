"""
n8n_deploy_ - a simple N8N Workflow Manager
Simple n8n wf deployment tool with SQLite metadata store
"""

from .models import Workflow
from .db import DBApi
from .workflow import WorkflowApi

__version__ = "2.2.3"
__author__ = "Lehcode"

__all__ = [
    "Workflow",
    "DBApi",
    "WorkflowApi",
]
