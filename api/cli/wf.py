#!/usr/bin/env python3
"""
Workflow management commands for n8n-deploy CLI

Provides a consistent 'wf' command group for all workflow operations including:
- Basic operations: add, list, remove, search, stats, sync
- Server operations: pull, push, server
- Backup operations: backup, restore, backups, verify
"""

import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ..config import get_config
from ..workflow import WorkflowApi
from .app import CustomGroup, HELP_APP_DIR, HELP_FLOW_DIR, HELP_SERVER_URL, HELP_NO_EMOJI, HELP_FORMAT
from .output import (
    output_json_or_table,
    print_backup_files_table,
    print_workflow_search_table,
    print_workflow_table,
    print_error,
    print_success,
    cli_error,
)

console = Console()


@click.group(cls=CustomGroup)
def wf() -> None:
    """🔄 Workflow management commands"""
    pass


# Basic workflow operations
@wf.command()
@click.argument("name")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--server-url", help=HELP_SERVER_URL)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help=HELP_FORMAT,
)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def add(
    name: str,
    app_dir: Optional[str],
    flow_dir: Optional[str],
    server_url: Optional[str],
    skip_ssl_verify: bool,
    format: str,
    no_emoji: bool,
) -> None:
    """➕ Add workflow to database

    Pulls workflow from remote n8n server and adds to database (requires API key and server URL).

    \b
    Example:
      n8n-deploy wf add MyWorkflow  # Pulls from server
    """
    # Validate workflow name - allow UTF-8 characters, spaces, and common punctuation
    # Only reject control characters, null bytes, and path separators for security
    stripped_name = name.strip()
    if not stripped_name or any(c in stripped_name for c in "\x00/\\"):
        cli_error(
            f"Workflow name '{name}' is invalid. Name cannot be empty or contain null bytes or path separators (/ \\)",
            no_emoji,
        )

    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir, n8n_url=server_url)
    except ValueError as e:
        cli_error(str(e), no_emoji)

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify)

        # Pull workflow from server
        # Check if API key and server URL are configured
        if not config.n8n_url:
            cli_error(
                "Server URL not configured. Use --server-url or set N8N_DEPLOY_SERVER_URL environment variable", no_emoji
            )

        # Try to pull workflow from server
        success = manager.pull_workflow(name)
        if not success:
            cli_error(f"Failed to pull workflow '{name}' from server", no_emoji)

    except Exception as e:
        cli_error(f"Failed to add workflow: {e}", no_emoji)


@wf.command("list")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help=HELP_FORMAT,
)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.option("--only", is_flag=True, help="Show only workflows with existing JSON files (backupable)")
def list(
    app_dir: Optional[str],
    flow_dir: Optional[str],
    format: str,
    no_emoji: bool,
    only: bool,
) -> None:
    """📋 List all workflows"""
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)
        workflows = manager.list_workflows()

        # Filter to only backupable workflows if --only flag is set
        if only:
            from pathlib import Path

            backupable_workflows = []
            for wf in workflows:
                # Construct the workflow file path using workflow ID
                workflow_path = Path(config.workflows_path) / f"{wf['id']}.json"
                if workflow_path.exists():
                    backupable_workflows.append(wf)
            workflows = backupable_workflows

        if format == "json":
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


@wf.command()
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.argument("workflow_id", metavar="workflow-id")
def remove(
    workflow_id: str,
    app_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
    yes: bool,
) -> None:
    """🗑️ Remove workflow from database

    Removes a workflow using its n8n workflow ID (e.g., 'deAVBp391wvomsWY').
    This is the actual ID generated by n8n, not the user-friendly name.
    """
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)

        # Get workflow info for confirmation
        try:
            workflow_info = manager.get_workflow_info(workflow_id)
            workflow_name = workflow_info.get("name", workflow_id)
        except Exception:
            workflow_name = workflow_id

        # Ask for confirmation unless --yes flag is provided
        if not yes:
            if no_emoji:
                confirmation = click.confirm(f"Remove workflow '{workflow_name}' ({workflow_id})?")
            else:
                confirmation = click.confirm(f"🗑️ Remove workflow '{workflow_name}' ({workflow_id})?")

            if not confirmation:
                if no_emoji:
                    console.print("Operation cancelled")
                else:
                    console.print("[yellow]Operation cancelled[/yellow]")
                return

        manager.remove_workflow(workflow_id)

        success_msg = f"Removed workflow '{workflow_id}'"
        if no_emoji:
            console.print(success_msg)
        else:
            console.print(f"[green]✓ {success_msg}[/green]")

    except Exception as e:
        error_msg = f"Failed to remove workflow: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command()
@click.argument("query")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help=HELP_FORMAT,
)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def search(
    query: str,
    app_dir: Optional[str],
    flow_dir: Optional[str],
    format: str,
    no_emoji: bool,
) -> None:
    """🔍 Search workflows by name or workflow ID

    Searches both:
    - User-friendly names assigned in n8n-deploy (e.g., 'signup-flow')
    - n8n workflow IDs (e.g., 'deAVBp391wvomsWY' or partial matches)

    Results are ordered by relevance: exact matches first, then partial matches.
    Use exact n8n workflow IDs for direct operations like pull/push/remove.
    """
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)
        workflows = manager.search_workflows(query)
        output_json_or_table(workflows, format, no_emoji, print_workflow_search_table, query)

    except Exception as e:
        error_msg = f"Failed to search workflows: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command()
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help=HELP_FORMAT,
)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", required=False, metavar="workflow-id")
def stats(
    workflow_id: Optional[str],
    app_dir: Optional[str],
    flow_dir: Optional[str],
    format: str,
    no_emoji: bool,
) -> None:
    """📊 Show workflow statistics

    Shows overall workflow statistics if no workflow-id is provided,
    or detailed statistics for a specific workflow if workflow-id is given.

    The workflow-id should be the actual n8n workflow ID (e.g., 'deAVBp391wvomsWY'),
    not the user-friendly name assigned in n8n-deploy.
    """
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)
        stats_data = manager.get_workflow_stats(workflow_id)

        if format == "json":
            console.print(JSON.from_data(stats_data))
        else:
            if workflow_id:
                # Individual workflow stats
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
@wf.command()
@click.option("--server-url", help=HELP_SERVER_URL)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="workflow-id")
def pull(
    workflow_id: str,
    server_url: Optional[str],
    skip_ssl_verify: bool,
    app_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """📥 Download workflow from n8n server

    Downloads a workflow using its n8n workflow ID (e.g., 'deAVBp391wvomsWY').
    This is the actual ID from the n8n server, not the user-friendly name.
    """
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify)
        # Override server URL if provided
        if server_url:
            # Set temporary environment variable for this operation
            original_url = os.environ.get("N8N_DEPLOY_SERVER_URL")
            os.environ["N8N_DEPLOY_SERVER_URL"] = server_url

        success = manager.pull_workflow(workflow_id)

        # Restore original environment
        if server_url:
            if original_url:
                os.environ["N8N_DEPLOY_SERVER_URL"] = original_url
            else:
                os.environ.pop("N8N_DEPLOY_SERVER_URL", None)

        if success:
            success_msg = f"Pulled workflow '{workflow_id}' from server"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]✓ {success_msg}[/green]")
        else:
            error_msg = f"Failed to pull workflow '{workflow_id}'"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except Exception as e:
        error_msg = f"Failed to pull workflow: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command()
@click.option("--server-url", help=HELP_SERVER_URL)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="workflow-id")
def push(
    workflow_id: str,
    server_url: Optional[str],
    skip_ssl_verify: bool,
    app_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """📤 Upload workflow to n8n server

    Uploads a workflow using its n8n workflow ID (e.g., 'deAVBp391wvomsWY').
    This is the actual ID stored in the workflow JSON file.
    """
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify)
        # Override server URL if provided
        if server_url:
            original_url = os.environ.get("N8N_DEPLOY_SERVER_URL")
            os.environ["N8N_DEPLOY_SERVER_URL"] = server_url

        success = manager.push_workflow(workflow_id)

        # Restore original environment
        if server_url:
            if original_url:
                os.environ["N8N_DEPLOY_SERVER_URL"] = original_url
            else:
                os.environ.pop("N8N_DEPLOY_SERVER_URL", None)

        if success:
            success_msg = f"Pushed workflow '{workflow_id}' to server"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]✓ {success_msg}[/green]")
        else:
            error_msg = f"Failed to push workflow '{workflow_id}'"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except Exception as e:
        error_msg = f"Failed to push workflow: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command("server")
@click.option("--server-url", help=HELP_SERVER_URL)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help=HELP_FORMAT,
)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list_server(
    server_url: Optional[str],
    skip_ssl_verify: bool,
    app_dir: Optional[str],
    flow_dir: Optional[str],
    format: str,
    no_emoji: bool,
) -> None:
    """🌐 List workflows from n8n server"""
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify)
        # Override server URL if provided
        if server_url:
            original_url = os.environ.get("N8N_DEPLOY_SERVER_URL")
            os.environ["N8N_DEPLOY_SERVER_URL"] = server_url

        workflows = manager.list_n8n_workflows()

        # Restore original environment
        if server_url:
            if original_url:
                os.environ["N8N_DEPLOY_SERVER_URL"] = original_url
            else:
                os.environ.pop("N8N_DEPLOY_SERVER_URL", None)

        if format == "json":
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


# Backup operations
def get_backup_dir(backup_dir_param: Optional[str]) -> Path:
    """Get backup directory with priority: parameter > environment > cwd"""
    if backup_dir_param:
        return Path(backup_dir_param).resolve()

    env_backup_dir = os.environ.get("N8N_BACKUP_DIR")
    if env_backup_dir:
        return Path(env_backup_dir).resolve()

    return Path.cwd()


@wf.command("createbackup")
@click.option("--backup-dir", type=click.Path(), help="Backup directory (overrides N8N_BACKUP_DIR, default: cwd)")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def backup(
    backup_dir: Optional[str],
    app_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """📦 Create workflow backup

    Creates a tar.gz backup of all workflows in the specified directory.
    Uses current directory by default, N8N_BACKUP_DIR environment variable,
    or --backup-dir parameter (highest priority).
    """
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        backup_path = get_backup_dir(backup_dir)
        manager = WorkflowApi(config=config)

        result = manager.backup_all_workflows(backup_path)

        if result:
            success_msg = f"Created backup: {result}"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]✓ {success_msg}[/green]")
        else:
            error_msg = "Failed to create backup"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except Exception as e:
        error_msg = f"Failed to create backup: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command()
@click.argument("backup_file")
@click.option("--backup-dir", type=click.Path(), help="Backup directory (overrides N8N_BACKUP_DIR, default: cwd)")
@click.option("--app-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def restore(
    backup_file: str,
    backup_dir: Optional[str],
    app_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """📥 Restore workflows from backup

    Restores workflows from a tar.gz backup file.
    Looks for backup file in current directory by default,
    N8N_BACKUP_DIR environment variable, or --backup-dir parameter.
    """
    try:
        config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        backup_path = get_backup_dir(backup_dir)
        full_backup_path = backup_path / backup_file

        manager = WorkflowApi(config=config)
        result = manager.restore_workflows_backup(full_backup_path)

        if result:
            success_msg = f"Restored workflows from: {full_backup_path}"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]✓ {success_msg}[/green]")
        else:
            error_msg = f"Failed to restore from: {full_backup_path}"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except Exception as e:
        error_msg = f"Failed to restore backup: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command("backups")
@click.option("--backup-dir", type=click.Path(), help="Backup directory (overrides N8N_BACKUP_DIR, default: cwd)")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help=HELP_FORMAT,
)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list_backups(
    backup_dir: Optional[str],
    format: str,
    no_emoji: bool,
) -> None:
    """📋 List available workflow backups

    Lists tar.gz backup files in the specified directory.
    Looks in current directory by default, N8N_DEPLOY_FLOW_DIR environment variable,
    or --backup-dir parameter.
    """
    try:
        backup_path = get_backup_dir(backup_dir)
        # Use list() builtin explicitly to avoid conflict with Click's list command
        import builtins

        backup_files = builtins.list(backup_path.glob("*.tar.gz"))

        if format == "json":
            import json as json_module

            backup_data = []
            for backup_file in sorted(backup_files):
                stat = backup_file.stat()
                backup_data.append(
                    {
                        "name": backup_file.name,
                        "path": str(backup_file),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )
            # Always output JSON, even if empty list
            click.echo(json_module.dumps(backup_data, indent=2))
        else:
            print_backup_files_table(backup_files, no_emoji, str(backup_path))

    except Exception as e:
        error_msg = f"Failed to list backups: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()


@wf.command("verify")
@click.argument("backup_file")
@click.option("--backup-dir", type=click.Path(), help="Backup directory (overrides N8N_BACKUP_DIR, default: cwd)")
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def verify_backup(
    backup_file: str,
    backup_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """🔍 Verify backup file integrity

    Verifies the integrity of a tar.gz backup file.
    Looks for backup file in current directory by default,
    N8N_BACKUP_DIR environment variable, or --backup-dir parameter.
    """
    try:
        backup_path = get_backup_dir(backup_dir)
        full_backup_path = backup_path / backup_file

        if not full_backup_path.exists():
            error_msg = f"Backup file not found: {full_backup_path}"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

        # Basic verification - try to open and list contents
        import tarfile

        try:
            with tarfile.open(full_backup_path, "r:gz") as tar:
                members = tar.getnames()

            success_msg = f"Backup file is valid: {backup_file} ({len(members)} files)"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]✓ {success_msg}[/green]")

        except tarfile.TarError as e:
            error_msg = f"Backup file is corrupted: {e}"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except Exception as e:
        error_msg = f"Failed to verify backup: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
