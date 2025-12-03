#!/usr/bin/env python3
"""
Workflow management commands for n8n-deploy CLI

Provides a consistent 'wf' command group for all wf operations including:
- Basic operations: add, list, delete, search, stats
- Server operations: pull, push, server
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ..config import get_config, AppConfig
from ..workflow import WorkflowApi
from .app import (
    cli_data_dir_help,
    HELP_DB_FILENAME,
    HELP_FLOW_DIR,
    HELP_JSON,
    HELP_NO_EMOJI,
    HELP_SERVER_URL,
    HELP_TABLE,
    CustomCommand,
    CustomGroup,
)
from .output import (
    cli_error,
    print_workflow_search_table,
    print_workflow_table,
)

console = Console()


def _read_workflow_file(
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


def _ensure_workflow_id(
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


def _resolve_server_for_linking(config: AppConfig, link_remote: str, output_json: bool, no_emoji: bool) -> Tuple[str, int]:
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


def _link_workflow_to_server(
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


def _output_add_success(workflow_id: str, workflow_name: str, output_json: bool, no_emoji: bool) -> None:
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


@click.group(cls=CustomGroup)
def wf() -> None:
    """🔄 Workflow management commands"""
    pass


# Basic wf operations
@wf.command(cls=CustomCommand)
@click.argument("workflow_file")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--link-remote", help="Link workflow to n8n server (server name or URL)")
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def add(
    workflow_file: str,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    link_remote: Optional[str],
    output_json: bool,
    no_emoji: bool,
) -> None:
    """➕ Register local workflow JSON file to database

    Adds a workflow from a local JSON file to the database. The workflow file
    should be in the flow directory. Optionally link to a remote n8n server.

    \b
    Examples:
      n8n-deploy wf add deAVBp391wvomsWY.json
      n8n-deploy wf add workflow.json --link-remote production
      n8n-deploy wf add workflow.json --link-remote https://n8n.example.com
    """
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        cli_error(str(e), no_emoji)
        raise click.Abort()

    from .db import check_database_exists

    check_database_exists(config.database_path, output_json=output_json, no_emoji=no_emoji)

    try:
        result = _read_workflow_file(config, workflow_file, output_json, no_emoji)
        if result is None:
            return  # JSON error already printed
        _, workflow_data = result

        workflow_id, workflow_name = _ensure_workflow_id(workflow_data, workflow_file, output_json, no_emoji)

        manager = WorkflowApi(config=config)
        manager.add_workflow(workflow_id, workflow_name, filename=workflow_file)

        _output_add_success(workflow_id, workflow_name, output_json, no_emoji)

        if link_remote:
            server_name, server_id = _resolve_server_for_linking(config, link_remote, output_json, no_emoji)
            _link_workflow_to_server(manager, workflow_id, server_id, server_name, output_json, no_emoji)

    except click.Abort:
        raise
    except Exception as e:
        if output_json:
            console.print(JSON.from_data({"success": False, "error": str(e)}))
        else:
            cli_error(f"Failed to add workflow: {e}", no_emoji)


@wf.command("list", cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list(
    data_dir: Optional[str],
    db_filename: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """📋 List all workflows

    Displays all workflows from database with their metadata.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)
        workflows = manager.list_workflows()

        # Backupable status is shown in workflow metadata (file_exists field)
        # No filtering - all workflows are displayed with their backupable status

        if output_json:
            console.print(JSON.from_data(workflows))
        else:
            print_workflow_table(workflows, no_emoji)

    except Exception as e:
        error_msg = f"Failed to list workflows: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command(cls=CustomCommand)
@click.option(
    "--remote",
    metavar="N8N_SERVER_NAME|N8N_SERVER_URL",
    help="n8n server (name or URL) - uses linked API key if name provided",
)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.argument("workflow_id", metavar="WF_ID|WF_NAME|FILENAME")
def delete(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    yes: bool,
) -> None:
    """🗑️ Delete workflow from n8n server and database

    Deletes a workflow using its n8n workflow ID (e.g., 'deAVBp391wvomsWY'),
    workflow name, or filename. The workflow is deleted from the remote server
    first, then removed from the local database. The JSON file is NOT deleted.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (set via 'wf add --link-remote')
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    \b
    Examples:
      n8n-deploy wf delete workflow-name              # Uses linked server
      n8n-deploy wf delete workflow-name --remote staging  # Override to staging
      n8n-deploy wf delete deAVBp391wvomsWY --yes    # Skip confirmation
      n8n-deploy wf delete my-workflow.json          # Delete by filename
    """
    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)

        # Get workflow info for confirmation (resolves ID/name/filename)
        try:
            workflow_info = manager.get_workflow_info(workflow_id)
            workflow_name = workflow_info.get("name", workflow_id)
            actual_id = workflow_info["wf"].id
        except Exception:
            workflow_name = workflow_id
            actual_id = workflow_id

        # Check if this is a draft workflow (local only, no server deletion needed)
        is_draft = actual_id.startswith("draft_")

        # Ask for confirmation unless --yes flag is provided
        if not yes:
            if is_draft:
                prompt_msg = f"Remove draft workflow '{workflow_name}' ({actual_id}) from database?"
            else:
                prompt_msg = f"Delete workflow '{workflow_name}' ({actual_id}) from server and database?"

            if no_emoji:
                confirmation = click.confirm(prompt_msg)
            else:
                confirmation = click.confirm(f"🗑️ {prompt_msg}")

            if not confirmation:
                if no_emoji:
                    console.print("Operation cancelled")
                else:
                    console.print("[yellow]Operation cancelled[/yellow]")
                return

        # Delete from server first (unless it's a draft)
        if not is_draft:
            success = manager.delete_n8n_workflow(actual_id)
            if not success:
                error_msg = f"Failed to delete workflow from server"
                if no_emoji:
                    console.print(error_msg)
                else:
                    console.print(f"[red]{error_msg}[/red]")
                raise click.Abort()

        # Remove from database
        manager.remove_workflow(actual_id)

        if is_draft:
            success_msg = f"Removed draft workflow '{workflow_name}' from database"
        else:
            success_msg = f"Deleted workflow '{workflow_name}' from server and database"

        if no_emoji:
            console.print(success_msg)
        else:
            console.print(f"[green]✓ {success_msg}[/green]")

    except click.Abort:
        raise
    except Exception as e:
        error_msg = f"Failed to delete workflow: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command(cls=CustomCommand)
@click.argument("query")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def search(
    query: str,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """🔍 Search workflows by name or wf ID

    Searches both:
    - User-friendly names assigned in n8n-deploy (e.g., 'signup-flow')
    - n8n wf IDs (e.g., 'deAVBp391wvomsWY' or partial matches)

    Results are ordered by relevance: exact matches first, then partial matches.
    Use exact n8n wf IDs for direct operations like pull/push/delete.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)
        workflows = manager.search_workflows(query)

        if output_json:
            console.print(JSON.from_data(workflows))
        else:
            print_workflow_search_table(workflows, no_emoji, query)

    except Exception as e:
        error_msg = f"Failed to search workflows: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", required=False, metavar="wf-id")
def stats(
    workflow_id: Optional[str],
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """📊 Show wf statistics

    Shows overall wf statistics if no wf-id is provided,
    or detailed statistics for a specific wf if wf-id is given.

    The wf-id should be the actual n8n wf ID (e.g., 'deAVBp391wvomsWY'),
    not the user-friendly name assigned in n8n-deploy.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)
        stats_data = manager.get_workflow_stats(workflow_id)

        if output_json:
            console.print(JSON.from_data(stats_data))
        else:
            if workflow_id:
                # Individual wf stats
                table = Table()
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="magenta")

                for key, value in stats_data.items():
                    table.add_row(key, str(value) if value is not None else "-")

                console.print(table)
            else:
                # Overall stats
                table = Table()
                table.add_column("Metric", style="cyan")
                table.add_column("Count", justify="right", style="magenta")

                table.add_row("Total Workflows", str(stats_data["total_workflows"]))
                table.add_row("Total Push Operations", str(stats_data["total_push_operations"]))
                table.add_row("Total Pull Operations", str(stats_data["total_pull_operations"]))

                console.print(table)

    except Exception as e:
        error_msg = f"Failed to get stats: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


# Server operations
@wf.command(cls=CustomCommand)
@click.option(
    "--remote",
    metavar="N8N_SERVER_NAME|N8N_SERVER_URL",
    help="n8n server (name or URL) - uses linked API key if name provided",
)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--filename", metavar="FILENAME", help="Custom filename for new workflows (e.g., 'my-workflow.json')")
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="WORKFLOW_ID|WORKFLOW_NAME")
def pull(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    filename: Optional[str],
    no_emoji: bool,
) -> None:
    """📥 Download wf from n8n server

    Downloads a wf using its n8n wf ID (e.g., 'deAVBp391wvomsWY') or workflow name.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (if workflow exists in database)
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    Use --remote to override with server name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.

    For new workflows (not in database), use --filename to specify the local filename.
    If not provided, you will be prompted to enter one.

    Examples:
      n8n-deploy wf pull workflow-name              # Uses linked server
      n8n-deploy wf pull workflow-name --remote staging  # Override to staging
      n8n-deploy wf pull abc123 --filename my-workflow.json  # Custom filename
    """
    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    # Check if database exists and is initialized
    from .db import check_database_exists

    check_database_exists(config.database_path, output_json=False, no_emoji=no_emoji)

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)

        # Check if workflow exists in database
        # If not, and no filename provided, prompt user
        target_filename = filename
        try:
            manager.get_workflow_info(workflow_id)
            # Workflow exists - filename will be retrieved from database
        except ValueError:
            # Workflow not in database - this is a new pull
            if not target_filename:
                # Prompt user for filename
                default_filename = f"{workflow_id}.json"
                if no_emoji:
                    console.print(f"New workflow detected. Enter filename (default: {default_filename}):")
                else:
                    console.print(f"📄 New workflow detected. Enter filename (default: [cyan]{default_filename}[/cyan]):")

                target_filename = click.prompt("Filename", default=default_filename, show_default=False)

                # Ensure .json extension
                if target_filename and not target_filename.endswith(".json"):
                    target_filename = f"{target_filename}.json"

        success = manager.pull_workflow(workflow_id, filename=target_filename)

        if success:
            success_msg = f"Pulled wf '{workflow_id}' from server"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]✓ {success_msg}[/green]")
        else:
            error_msg = f"Failed to pull wf '{workflow_id}'"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except click.Abort:
        # Re-raise Abort without additional message
        raise
    except Exception as e:
        error_msg = f"Failed to pull wf: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command(cls=CustomCommand)
@click.option(
    "--remote",
    metavar="N8N_SERVER_NAME|N8N_SERVER_URL",
    help="n8n server (name or URL) - uses linked API key if name provided",
)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="WORKFLOW_ID|WORKFLOW_NAME")
def push(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
) -> None:
    """📤 Upload wf to n8n server

    Uploads a wf using its n8n wf ID (e.g., 'deAVBp391wvomsWY') or workflow name.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (set via 'wf add --link-remote')
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    Use --remote to override with server name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.

    Examples:
      n8n-deploy wf push workflow-name              # Uses linked server
      n8n-deploy wf push workflow-name --remote staging  # Override to staging
    """
    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)
        success = manager.push_workflow(workflow_id)

        if success:
            success_msg = f"Pushed wf '{workflow_id}' to server"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]✓ {success_msg}[/green]")
        else:
            error_msg = f"Failed to push wf '{workflow_id}'"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except click.Abort:
        raise  # Re-raise without additional message
    except Exception as e:
        error_msg = f"Failed to push wf: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command("server", cls=CustomCommand)
@click.option("--remote", help=HELP_SERVER_URL)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list_server(
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """🌐 List workflows from n8n server"""
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)
        workflows = manager.list_n8n_workflows()

        if output_json:
            console.print(JSON.from_data(workflows))
        else:
            if not workflows:
                msg = "No workflows found on server"
                if no_emoji:
                    console.print(msg)
                else:
                    console.print(f"[yellow]{msg}[/yellow]")
                return

            table = Table()
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Active", justify="center")
            table.add_column("Updated", justify="center")

            for wf in workflows:
                table.add_row(
                    wf.get("id", ""),
                    wf.get("name", ""),
                    "✓" if wf.get("active") else "✗",
                    str(wf.get("updatedAt", ""))[:10] if wf.get("updatedAt") else "-",
                )

            console.print(table)

    except Exception as e:
        error_msg = f"Failed to list server workflows: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
