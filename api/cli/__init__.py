#!/usr/bin/env python3
"""
CLI module for n8n-deploy workflow management

This module provides modular CLI commands organized by functional areas:
- main: Base CLI application with version/help handling
- wf: Workflow operations (add, delete, list, sync, search, stats)
- db: Database management (init, status, backup, compact)
- backup: Backup/restore operations for workflows
- apikey: API key lifecycle management
"""

from .app import (
    cli_data_dir_help,
    HELP_FLOW_DIR,
    HELP_FORMAT,
    HELP_NO_EMOJI,
    HELP_SERVER_URL,
    PROG_NAME,
    cli,
    get_cli_app,
)


def main() -> None:
    """Main entry point for the CLI application"""
    cli(prog_name=PROG_NAME)


__all__ = [
    "get_cli_app",
    "cli",
    "main",
    "PROG_NAME",
    "cli_data_dir_help",
    "HELP_FLOW_DIR",
    "HELP_SERVER_URL",
    "HELP_NO_EMOJI",
    "HELP_FORMAT",
]
