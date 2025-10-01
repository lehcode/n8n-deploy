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

from .app import (
    get_cli_app,
    cli,
    PROG_NAME,
    HELP_APP_DIR,
    HELP_FLOW_DIR,
    HELP_SERVER_URL,
    HELP_NO_EMOJI,
    HELP_FORMAT,
)


def main() -> None:
    """Main entry point for the CLI application"""
    cli(prog_name=PROG_NAME)


__all__ = [
    "get_cli_app",
    "cli",
    "main",
    "PROG_NAME",
    "HELP_APP_DIR",
    "HELP_FLOW_DIR",
    "HELP_SERVER_URL",
    "HELP_NO_EMOJI",
    "HELP_FORMAT",
]
