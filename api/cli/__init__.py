#!/usr/bin/env python3
"""
CLI module for n8n-deploy workflow management

This module provides modular CLI commands organized by functional areas:
- main: Base CLI application with version/help handling
- workflow: Workflow operations (add, remove, list, sync, search, stats)
- db: Database management (init, status, backup, compact)
- backup: Backup/restore operations for workflows
- apikey: API key lifecycle management
"""

from .app import get_cli_app, cli


def main() -> None:
    """Main entry point for the CLI application"""
    cli()


__all__ = [
    "get_cli_app",
    "cli",
    "main",
]
