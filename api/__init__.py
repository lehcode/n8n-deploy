"""
n8n_deploy_ - a simple N8N Workflow Manager
Simple n8n workflow deployment tool with SQLite metadata store
"""

__version__ = "2.0.0"
__author__ = "Itzam System"

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import Workflow, WorkflowVersion
from api.n8n_deploy_db import n8n_deploy_DB
from api.manager import WorkflowManager

__all__ = [
    "Workflow",
    "WorkflowVersion",
    "n8n_deploy_DB",
    "WorkflowManager",
]
