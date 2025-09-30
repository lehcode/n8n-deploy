#!/usr/bin/env python3
"""
Database module for n8n-deploy workflow management

This module provides modular database operations organized by functional areas:
- core: Main database operations and workflow CRUD
- backup: Backup-related database operations
- schema: Schema management and database initialization
"""

from .core import DBApi
from .backup import BackupApi
from .schema import SchemaApi

__all__ = [
    "DBApi",
    "BackupApi",
    "SchemaApi",
]
