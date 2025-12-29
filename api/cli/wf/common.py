#!/usr/bin/env python3
"""
Common utilities for workflow CLI commands.

Shared helper functions for reading workflow files, resolving servers,
and outputting success/error messages.
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import click
from rich.console import Console
from rich.json import JSON

from ...config import AppConfig
from ...workflow import WorkflowApi
from ..output import cli_error

console = Console()


def read_workflow_file(
    config: AppConfig, workflow_file: str, output_json: bool, no_emoji: bool
) -> Optional[Tuple[Path, Dict[str, Any]]]:
    """Read and parse workflow JSON file.

    Returns:
        Tuple of (file_path, workflow_data) on success, None on error (with JSON output)

    Raises:
        click.Abort: If file not found or invalid JSON (non-JSON mode only)
    """
    file_path = Path(config.workflows_path) / workflow_file

    if not file_path.exists():
        if output_json:
            console.print(JSON.from_data({"success": False, "error": f"Workflow file not found: {file_path}"}))
            return None
        cli_error(f"Workflow file not found: {file_path}", no_emoji)
        raise click.Abort()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            workflow_data: Dict[str, Any] = json.load(f)
        return file_path, workflow_data
    except json.JSONDecodeError as e:
        if output_json:
            console.print(JSON.from_data({"success": False, "error": f"Invalid JSON in workflow file: {e}"}))
            return None
        cli_error(f"Invalid JSON in workflow file: {e}", no_emoji)
        raise click.Abort()


def ensure_workflow_id(
    workflow_data: Dict[str, Any], workflow_file: str, output_json: bool, no_emoji: bool
) -> Tuple[str, str]:
    """Ensure workflow has an ID, generating draft if needed.

    Returns:
        Tuple of (workflow_id, workflow_name)
    """
    workflow_id = workflow_data.get("id")
    workflow_name = workflow_data.get("name", workflow_file.replace(".json", ""))

    if not workflow_id:
        workflow_id = f"draft_{uuid.uuid4()}"
        if not output_json and not no_emoji:
            console.print(f"[yellow]⚠️  No ID found in workflow file. Generated draft ID: {workflow_id}[/yellow]")
            console.print("[yellow]    This will be replaced with server-assigned ID after first push.[/yellow]")
        elif not output_json:
            console.print(f"WARNING: No ID found in workflow file. Generated draft ID: {workflow_id}")
            console.print("         This will be replaced with server-assigned ID after first push.")

    return workflow_id, workflow_name


def resolve_server_for_linking(config: AppConfig, link_remote: str, output_json: bool, no_emoji: bool) -> Tuple[str, int]:
    """Resolve server name or URL for workflow linking.

    Returns:
        Tuple of (server_name, server_id)

    Raises:
        click.Abort: If server not found
    """
    from api.db.servers import ServerCrud

    server_crud = ServerCrud(config=config)

    if "://" in link_remote:
        server = server_crud.get_server_by_url(link_remote)
        error_msg = f"Server URL '{link_remote}' not found in database"
        suggestion = ". Add it with 'server create'"
    else:
        server = server_crud.get_server_by_name(link_remote)
        error_msg = f"Server '{link_remote}' not found in database"
        suggestion = ". Add it with 'server create'"

    if not server:
        if output_json:
            console.print(JSON.from_data({"success": False, "error": error_msg}))
        else:
            cli_error(error_msg + suggestion, no_emoji)
        raise click.Abort()

    server_name = server["name"] if "://" in link_remote else link_remote
    return server_name, server["id"]


def link_workflow_to_server(
    manager: WorkflowApi, workflow_id: str, server_id: int, server_name: str, output_json: bool, no_emoji: bool
) -> None:
    """Link workflow to server in database."""
    workflow_obj = manager.db.get_workflow(workflow_id)
    if workflow_obj:
        workflow_obj.server_id = server_id
        manager.db.update_workflow(workflow_obj)

    if not output_json:
        if no_emoji:
            console.print(f"Workflow linked to server: {server_name}")
        else:
            console.print(f"🔗 Workflow linked to server: {server_name}")


def output_add_success(workflow_id: str, workflow_name: str, output_json: bool, no_emoji: bool) -> None:
    """Output success message for workflow add."""
    result = {
        "success": True,
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "message": f"Workflow '{workflow_name}' (ID: {workflow_id}) added to database",
    }

    if output_json:
        console.print(JSON.from_data(result))
    elif no_emoji:
        console.print(f"Workflow '{workflow_name}' (ID: {workflow_id}) added to database")
    else:
        console.print(f"✅ Workflow '{workflow_name}' (ID: {workflow_id}) added to database")
