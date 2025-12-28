#!/usr/bin/env python3
"""
Workflow module for n8n-deploy

This module provides modular workflow operations:
- crud: Core workflow CRUD operations and metadata management
- n8n_api: n8n server API integration for push/pull operations
"""

from .crud import WorkflowCRUD
from .n8n_api import N8nAPI
from .main import WorkflowApi
from .types import N8nApiErrorType, N8nApiResult

__all__ = [
    "WorkflowCRUD",
    "N8nAPI",
    "WorkflowApi",
    "N8nApiErrorType",
    "N8nApiResult",
]
