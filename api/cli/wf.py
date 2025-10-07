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
@click.argument("name")
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--link-remote", help="Link workflow to n8n server (server name, partial URL, or full URL with schema)")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def add(
    name: str,
    flow_dir: Optional[str],
    link_remote: Optional[str],
    skip_ssl_verify: bool,
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """➕ Add wf to database

    Pulls wf from remote n8n server and adds to database (requires API key and server URL).

    \b
    Example:
      n8n-deploy wf add MyWorkflow --link-remote my-server
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    # Validate wf name - allow UTF-8 characters, spaces, and common punctuation
    # Only reject control characters, null bytes, and path separators for security
    stripped_name = name.strip()
    if not stripped_name or any(c in stripped_name for c in "\x00/\\"):
        cli_error(
            f"Workflow name '{name}' is invalid. Name cannot be empty or contain null bytes or path separators (/ \\)",
            no_emoji,
        )

    try:
        config = get_config(flow_folder=flow_dir)
    except ValueError as e:
        cli_error(str(e), no_emoji)

    try:
        # Resolve server URL from --link-remote
        server_url = None
        if link_remote:
            from api.db.servers import ServerCrud

            server_crud = ServerCrud(config=config)

            # Check if it's a full URL (contains ://)
            if "://" in link_remote:
                # Full URL with schema - validate and use directly
                server_url = link_remote
            else:
                # Could be partial URL or server name
                # First, try to find by server name
                server = server_crud.get_server_by_name(link_remote)
                if server:
                    server_url = server["url"]
                else:
                    # Try to find by partial URL match in database
                    all_servers = server_crud.list_servers()
                    matching_servers = [s for s in all_servers if link_remote in s["url"]]
                    if len(matching_servers) == 1:
                        server_url = matching_servers[0]["url"]
                    elif len(matching_servers) > 1:
                        server_names = [s["name"] for s in matching_servers]
                        cli_error(
                            f"Partial URL '{link_remote}' matches multiple servers: {', '.join(server_names)}. "
                            f"Please be more specific or use full server name",
                            no_emoji,
                        )
                    else:
                        cli_error(
                            f"No server found matching '{link_remote}'. "
                            f"Check server name or URL in database with 'server list'",
                            no_emoji,
                        )
        elif not config.n8n_url:
            cli_error("Server URL not configured. Use --link-remote or set N8N_SERVER_URL environment variable", no_emoji)
        else:
            server_url = config.n8n_url

        # Update config with resolved server URL
        config.n8n_url = server_url

        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify)

        # Try to pull wf from server
        success = manager.pull_workflow(name)
        if not success:
            cli_error(f"Failed to pull wf '{name}' from server", no_emoji)

    except Exception as e:
        cli_error(f"Failed to add wf: {e}", no_emoji)


@wf.command("list", cls=CustomCommand)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list(
    flow_dir: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """📋 List all workflows

    Displays all workflows with backupable status in metadata.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        config = get_config(flow_folder=flow_dir)
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
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.argument("workflow_id", metavar="wf-id")
def remove(
    workflow_id: str,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
    yes: bool,
) -> None:
    """🗑️ Remove wf from database

    Removes a wf using its n8n wf ID (e.g., 'deAVBp391wvomsWY').
    This is the actual ID generated by n8n, not the user-friendly name.
    """
    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir)
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
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def search(
    query: str,
    data_dir: Optional[str],
    flow_dir: Optional[str],
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
        config = get_config(base_folder=data_dir, flow_folder=flow_dir)
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
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", required=False, metavar="wf-id")
def stats(
    workflow_id: Optional[str],
    data_dir: Optional[str],
    flow_dir: Optional[str],
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
        config = get_config(base_folder=data_dir, flow_folder=flow_dir)
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
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="wf-id")
def pull(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """📥 Download wf from n8n server

    Downloads a wf using its n8n wf ID (e.g., 'deAVBp391wvomsWY').
    This is the actual ID from the n8n server, not the user-friendly name.

    Use --remote to specify server by name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.
    """
    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

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
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="wf-id")
def push(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """📤 Upload wf to n8n server

    Uploads a wf using its n8n wf ID (e.g., 'deAVBp391wvomsWY').
    This is the actual ID stored in the wf JSON file.

    Use --remote to specify server by name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.
    """
    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir)
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
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list_server(
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """🌐 List workflows from n8n server"""
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, flow_folder=flow_dir)
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
