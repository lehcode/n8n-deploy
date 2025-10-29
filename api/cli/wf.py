#!/usr/bin/env python3
"""
Workflow management commands for n8n-deploy CLI

Provides a consistent 'wf' command group for all wf operations including:
- Basic operations: add, list, remove, search, stats
- Server operations: pull, push, server
"""

from typing import Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ..config import get_config
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
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        cli_error(str(e), no_emoji)

    # Check if database exists and is initialized
    from .db import check_database_exists

    check_database_exists(config.database_path, output_json=output_json, no_emoji=no_emoji)

    try:
        import json
        from pathlib import Path

        # Determine the file path
        file_path = Path(config.workflows_path) / workflow_file

        if not file_path.exists():
            cli_error(f"Workflow file not found: {file_path}", no_emoji)

        # Read and parse the workflow JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            workflow_data = json.load(f)

        workflow_id = workflow_data.get("id")
        workflow_name = workflow_data.get("name", workflow_file.replace(".json", ""))

        if not workflow_id:
            cli_error(f"No 'id' field found in workflow file: {file_path}", no_emoji)

        # Add workflow to database
        manager = WorkflowApi(config=config)
        manager.add_workflow(workflow_id, workflow_name)

        result = {
            "success": True,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "message": f"Workflow '{workflow_name}' (ID: {workflow_id}) added to database",
        }

        if output_json:
            from rich.json import JSON

            console.print(JSON.from_data(result))
        elif no_emoji:
            console.print(f"Workflow '{workflow_name}' (ID: {workflow_id}) added to database")
        else:
            console.print(f"✅ Workflow '{workflow_name}' (ID: {workflow_id}) added to database")

        # Optionally link to remote server
        if link_remote:
            from api.db.servers import ServerCrud

            server_crud = ServerCrud(config=config)

            # Resolve server name or URL
            server_name: str
            if "://" in link_remote:
                # Full URL - ensure it exists in database or create it
                server = server_crud.get_server_by_url(link_remote)
                if not server:
                    if output_json:
                        from rich.json import JSON

                        console.print(
                            JSON.from_data({"success": False, "error": f"Server URL '{link_remote}' not found in database"})
                        )
                        raise click.Abort()
                    else:
                        cli_error(f"Server URL '{link_remote}' not found in database. Add it with 'server create'", no_emoji)
                # server is guaranteed to be not None here
                assert server is not None
                server_name = server["name"]
            else:
                # Server name
                server = server_crud.get_server_by_name(link_remote)
                if not server:
                    if output_json:
                        from rich.json import JSON

                        console.print(
                            JSON.from_data({"success": False, "error": f"Server '{link_remote}' not found in database"})
                        )
                        raise click.Abort()
                    else:
                        cli_error(f"Server '{link_remote}' not found in database. Add it with 'server create'", no_emoji)
                server_name = link_remote

            # Link workflow to server
            assert server is not None  # Type assertion for mypy
            server_id = server["id"]

            # Update workflow with server_id
            workflow_obj = manager.db.get_workflow(workflow_id)
            if workflow_obj:
                workflow_obj.server_id = server_id
                manager.db.update_workflow(workflow_obj)

            if not output_json:
                if no_emoji:
                    console.print(f"Workflow linked to server: {server_name}")
                else:
                    console.print(f"🔗 Workflow linked to server: {server_name}")

    except json.JSONDecodeError as e:
        if output_json:
            from rich.json import JSON

            console.print(JSON.from_data({"success": False, "error": f"Invalid JSON in workflow file: {e}"}))
        else:
            cli_error(f"Invalid JSON in workflow file: {e}", no_emoji)
    except Exception as e:
        if output_json:
            from rich.json import JSON

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
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.argument("workflow_id", metavar="wf-id")
def remove(
    workflow_id: str,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    yes: bool,
) -> None:
    """🗑️ Remove wf from database

    Removes a wf using its n8n wf ID (e.g., 'deAVBp391wvomsWY').
    This is the actual ID generated by n8n, not the user-friendly name.
    """
    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)

        # Get wf info for confirmation
        try:
            workflow_info = manager.get_workflow_info(workflow_id)
            workflow_name = workflow_info.get("name", workflow_id)
        except Exception:
            workflow_name = workflow_id

        # Ask for confirmation unless --yes flag is provided
        if not yes:
            if no_emoji:
                confirmation = click.confirm(f"Remove wf '{workflow_name}' ({workflow_id})?")
            else:
                confirmation = click.confirm(f"🗑️ Remove wf '{workflow_name}' ({workflow_id})?")

            if not confirmation:
                if no_emoji:
                    console.print("Operation cancelled")
                else:
                    console.print("[yellow]Operation cancelled[/yellow]")
                return

        manager.remove_workflow(workflow_id)

        success_msg = f"Removed wf '{workflow_id}'"
        if no_emoji:
            console.print(success_msg)
        else:
            console.print(f"[green]✓ {success_msg}[/green]")

    except Exception as e:
        error_msg = f"Failed to remove wf: {e}"
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
    Use exact n8n wf IDs for direct operations like pull/push/remove.
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
@click.option("--remote", help="n8n server (name or URL) - uses linked API key if name provided")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="wf-id")
def pull(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
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

    Examples:
      n8n-deploy wf pull workflow-name              # Uses linked server
      n8n-deploy wf pull workflow-name --remote staging  # Override to staging
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
        success = manager.pull_workflow(workflow_id)

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
@click.option("--remote", help="n8n server (name or URL) - uses linked API key if name provided")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="wf-id")
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
