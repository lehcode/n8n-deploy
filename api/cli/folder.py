#!/usr/bin/env python3
"""
Folder synchronization CLI commands for n8n-deploy

Provides commands for managing folder mappings and synchronization
between local directories and n8n server folders.
"""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..config import AppConfig, get_config
from ..db.core import DBApi
from ..db.folders import FolderDB
from ..db.servers import ServerCrud
from ..models import SyncDirection
from ..workflow.folder_sync import FolderSyncManager
from .app import cli_data_dir_help, handle_verbose_flag, HELP_DB_FILENAME, CustomCommand, CustomGroup

console = Console()


def _get_server_id(
    config: "AppConfig",
    server_name: Optional[str] = None,
) -> Optional[int]:
    """Resolve server name to ID, or get active server

    Args:
        config: Application configuration
        server_name: Optional server name to look up

    Returns:
        Server ID or None
    """
    server_crud = ServerCrud(config=config)

    if server_name:
        server = server_crud.get_server_by_name(server_name)
        if server:
            server_id: int = server["id"]
            return server_id
        return None

    # Get first active server
    servers = server_crud.list_servers(active_only=True)
    if servers:
        first_id: int = servers[0]["id"]
        return first_id

    return None


@click.group(name="folder", cls=CustomGroup)
@click.option(
    "-v",
    "--verbose",
    count=True,
    expose_value=False,
    is_eager=True,
    callback=handle_verbose_flag,
    help="Verbosity level (-v, -vv)",
)
def folder() -> None:
    """📁 Manage folder synchronization with n8n server"""
    pass


@folder.command(name="auth", cls=CustomCommand)
@click.argument("server_name")
@click.option("--email", help="n8n account email")
@click.option("--password", help="n8n account password")
@click.option("--cookie", help="Session cookie from browser (alternative to email/password)")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification")
def auth_server(
    server_name: str,
    email: Optional[str],
    password: Optional[str],
    cookie: Optional[str],
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    skip_ssl_verify: bool,
) -> None:
    """Authenticate with n8n server for folder operations

    Uses internal n8n API (cookie-based authentication).

    Examples:

        n8n-deploy folder auth myserver --email user@example.com

        n8n-deploy folder auth myserver --cookie "n8n-auth=abc123..."
    """
    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        # Get server ID
        server_id = _get_server_id(config, server_name)
        if not server_id:
            msg = f"Server '{server_name}' not found"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

        db = DBApi(config=config)
        folder_db = FolderDB(config=config)

        sync_manager = FolderSyncManager(
            config=config,
            db=db,
            folder_db=folder_db,
            server_id=server_id,
            skip_ssl_verify=skip_ssl_verify,
        )

        # Try to connect
        if cookie:
            success = sync_manager.connect(cookie=cookie)
        elif email and password:
            success = sync_manager.connect(email=email, password=password)
        else:
            msg = "Either --email/--password or --cookie required"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

        if success:
            msg = f"Authenticated with server '{server_name}'"
            console.print(msg if no_emoji else f"[green]{msg}[/green]")
        else:
            msg = "Authentication failed"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        msg = f"Error: {e}"
        console.print(msg if no_emoji else f"[red]{msg}[/red]")
        raise click.Abort()


@folder.command(name="list", cls=CustomCommand)
@click.option("--remote", help="Server name to list folders from")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification")
def list_folders(
    remote: Optional[str],
    output_json: bool,
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    skip_ssl_verify: bool,
) -> None:
    """List folders on n8n server

    Discovers and displays all folders from the connected n8n server.
    """
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_id = _get_server_id(config, remote)
        if not server_id:
            msg = "No server specified and no active server found"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

        db = DBApi(config=config)
        folder_db = FolderDB(config=config)

        sync_manager = FolderSyncManager(
            config=config,
            db=db,
            folder_db=folder_db,
            server_id=server_id,
            skip_ssl_verify=skip_ssl_verify,
        )

        # Try to connect using stored credentials
        if not sync_manager.connect():
            msg = "Not authenticated. Run 'n8n-deploy folder auth' first."
            console.print(msg if no_emoji else f"[yellow]{msg}[/yellow]")
            raise click.Abort()

        # Discover folders
        folders = sync_manager.discover_folders()

        if output_json:
            data = [
                {
                    "id": f.id,
                    "n8n_folder_id": f.n8n_folder_id,
                    "path": f.folder_path,
                    "project_id": f.n8n_project_id,
                }
                for f in folders
            ]
            print(json.dumps(data, indent=2))
            return

        if not folders:
            msg = "No folders found on server"
            console.print(msg if no_emoji else f"[yellow]{msg}[/yellow]")
            return

        # Display table
        table = Table(title=f"Folders on {sync_manager.server_name}" if not no_emoji else None)
        table.add_column("Path", style="cyan")
        table.add_column("Folder ID")
        table.add_column("Project ID")

        for f in folders:
            table.add_row(f.folder_path, f.n8n_folder_id[:12] + "...", f.n8n_project_id[:12] + "...")

        console.print(table)
        console.print(f"\nTotal: {len(folders)} folder(s)")

    except click.Abort:
        raise
    except Exception as e:
        msg = f"Error: {e}"
        console.print(msg if no_emoji else f"[red]{msg}[/red]")
        raise click.Abort()


@folder.command(name="map", cls=CustomCommand)
@click.argument("local_path", type=click.Path())
@click.argument("n8n_folder")
@click.option(
    "--direction",
    type=click.Choice(["push", "pull", "bidirectional"]),
    default="bidirectional",
    help="Sync direction",
)
@click.option("--remote", help="Server name")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification")
def map_folder(
    local_path: str,
    n8n_folder: str,
    direction: str,
    remote: Optional[str],
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    skip_ssl_verify: bool,
) -> None:
    """Create a folder mapping between local and n8n folders

    Maps a local directory to an n8n folder for synchronization.

    Examples:

        n8n-deploy folder map ./workflows openminded/test

        n8n-deploy folder map ./prod production --direction push
    """
    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_id = _get_server_id(config, remote)
        if not server_id:
            msg = "No server specified and no active server found"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

        db = DBApi(config=config)
        folder_db = FolderDB(config=config)

        sync_manager = FolderSyncManager(
            config=config,
            db=db,
            folder_db=folder_db,
            server_id=server_id,
            skip_ssl_verify=skip_ssl_verify,
        )

        if not sync_manager.connect():
            msg = "Not authenticated. Run 'n8n-deploy folder auth' first."
            console.print(msg if no_emoji else f"[yellow]{msg}[/yellow]")
            raise click.Abort()

        # Convert direction to enum
        sync_dir = SyncDirection(direction)

        # Create mapping
        abs_path = str(Path(local_path).resolve())
        mapping = sync_manager.create_mapping(abs_path, n8n_folder, sync_dir)

        if mapping:
            msg = f"Created mapping: {local_path} <-> {n8n_folder} ({direction})"
            console.print(msg if no_emoji else f"[green]{msg}[/green]")
        else:
            msg = f"Failed to create mapping. Folder '{n8n_folder}' may not exist."
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        msg = f"Error: {e}"
        console.print(msg if no_emoji else f"[red]{msg}[/red]")
        raise click.Abort()


@folder.command(name="mappings", cls=CustomCommand)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def list_mappings(
    output_json: bool,
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
) -> None:
    """List all folder mappings"""
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        folder_db = FolderDB(config=config)
        mappings = folder_db.list_folder_mappings()

        if output_json:
            data = []
            for m in mappings:
                n8n_folder = folder_db.get_n8n_folder(m.n8n_folder_id)
                data.append(
                    {
                        "id": m.id,
                        "local_path": m.local_path,
                        "n8n_folder_path": n8n_folder.folder_path if n8n_folder else "Unknown",
                        "direction": m.sync_direction,
                    }
                )
            print(json.dumps(data, indent=2))
            return

        if not mappings:
            msg = "No folder mappings configured"
            console.print(msg if no_emoji else f"[yellow]{msg}[/yellow]")
            return

        table = Table(title="Folder Mappings" if not no_emoji else None)
        table.add_column("ID", style="dim")
        table.add_column("Local Path", style="cyan")
        table.add_column("n8n Folder", style="green")
        table.add_column("Direction")

        for m in mappings:
            n8n_folder = folder_db.get_n8n_folder(m.n8n_folder_id)
            folder_path = n8n_folder.folder_path if n8n_folder else "Unknown"

            dir_icon = {
                "push": "->",
                "pull": "<-",
                "bidirectional": "<->",
            }.get(m.sync_direction, "?")

            table.add_row(
                str(m.id),
                m.local_path,
                folder_path,
                f"{dir_icon} ({m.sync_direction})",
            )

        console.print(table)

    except click.Abort:
        raise
    except Exception as e:
        msg = f"Error: {e}"
        console.print(msg if no_emoji else f"[red]{msg}[/red]")
        raise click.Abort()


@folder.command(name="pull", cls=CustomCommand)
@click.argument("n8n_folder")
@click.argument("local_path", type=click.Path())
@click.option("--remote", help="Server name")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification")
def pull_folder(
    n8n_folder: str,
    local_path: str,
    remote: Optional[str],
    dry_run: bool,
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    skip_ssl_verify: bool,
) -> None:
    """Pull workflows from n8n folder to local directory

    Downloads all workflows from the specified n8n folder.

    Examples:

        n8n-deploy folder pull openminded/test ./local-workflows

        n8n-deploy folder pull production ./prod --dry-run
    """
    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_id = _get_server_id(config, remote)
        if not server_id:
            msg = "No server specified and no active server found"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

        db = DBApi(config=config)
        folder_db = FolderDB(config=config)

        sync_manager = FolderSyncManager(
            config=config,
            db=db,
            folder_db=folder_db,
            server_id=server_id,
            skip_ssl_verify=skip_ssl_verify,
        )

        if not sync_manager.connect():
            msg = "Not authenticated. Run 'n8n-deploy folder auth' first."
            console.print(msg if no_emoji else f"[yellow]{msg}[/yellow]")
            raise click.Abort()

        if dry_run:
            console.print("[yellow]Dry run mode - no changes will be made[/yellow]" if not no_emoji else "Dry run mode")

        result = sync_manager.sync_pull_folder(
            n8n_path=n8n_folder,
            local_path=Path(local_path),
            dry_run=dry_run,
        )

        # Print summary
        if result.success:
            msg = f"Pull complete: {result.pulled} workflow(s)"
            console.print(msg if no_emoji else f"[green]{msg}[/green]")
        else:
            msg = "Pull failed"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")

        for err in result.errors:
            console.print(f"  Error: {err}" if no_emoji else f"  [red]Error: {err}[/red]")

        for warn in result.warnings:
            console.print(f"  Warning: {warn}" if no_emoji else f"  [yellow]Warning: {warn}[/yellow]")

        if not result.success:
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        msg = f"Error: {e}"
        console.print(msg if no_emoji else f"[red]{msg}[/red]")
        raise click.Abort()


@folder.command(name="push", cls=CustomCommand)
@click.argument("local_path", type=click.Path(exists=True))
@click.argument("n8n_folder")
@click.option("--create", "create_folder", is_flag=True, help="Create folder if it doesn't exist")
@click.option("--remote", help="Server name")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification")
def push_folder(
    local_path: str,
    n8n_folder: str,
    create_folder: bool,
    remote: Optional[str],
    dry_run: bool,
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    skip_ssl_verify: bool,
) -> None:
    """Push workflows from local directory to n8n folder

    Uploads all JSON workflow files from local directory to n8n folder.

    Examples:

        n8n-deploy folder push ./workflows openminded/test

        n8n-deploy folder push ./new-workflows new-folder --create
    """
    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_id = _get_server_id(config, remote)
        if not server_id:
            msg = "No server specified and no active server found"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

        db = DBApi(config=config)
        folder_db = FolderDB(config=config)

        sync_manager = FolderSyncManager(
            config=config,
            db=db,
            folder_db=folder_db,
            server_id=server_id,
            skip_ssl_verify=skip_ssl_verify,
        )

        if not sync_manager.connect():
            msg = "Not authenticated. Run 'n8n-deploy folder auth' first."
            console.print(msg if no_emoji else f"[yellow]{msg}[/yellow]")
            raise click.Abort()

        if dry_run:
            console.print("[yellow]Dry run mode - no changes will be made[/yellow]" if not no_emoji else "Dry run mode")

        result = sync_manager.sync_push_folder(
            local_path=Path(local_path),
            n8n_path=n8n_folder,
            create_folder=create_folder,
            dry_run=dry_run,
        )

        # Print summary
        if result.success:
            msg = f"Push complete: {result.pushed} workflow(s)"
            console.print(msg if no_emoji else f"[green]{msg}[/green]")
        else:
            msg = "Push failed"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")

        for err in result.errors:
            console.print(f"  Error: {err}" if no_emoji else f"  [red]Error: {err}[/red]")

        for warn in result.warnings:
            console.print(f"  Warning: {warn}" if no_emoji else f"  [yellow]Warning: {warn}[/yellow]")

        if not result.success:
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        msg = f"Error: {e}"
        console.print(msg if no_emoji else f"[red]{msg}[/red]")
        raise click.Abort()


@folder.command(name="sync", cls=CustomCommand)
@click.option("--mapping", "mapping_id", type=int, help="Specific mapping ID to sync")
@click.option("--remote", help="Server name")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification")
def sync_folders(
    mapping_id: Optional[int],
    remote: Optional[str],
    dry_run: bool,
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    skip_ssl_verify: bool,
) -> None:
    """Synchronize folders based on configured mappings

    Runs sync for all configured mappings or a specific one.

    Examples:

        n8n-deploy folder sync

        n8n-deploy folder sync --mapping 1 --dry-run
    """
    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_id = _get_server_id(config, remote)
        if not server_id:
            msg = "No server specified and no active server found"
            console.print(msg if no_emoji else f"[red]{msg}[/red]")
            raise click.Abort()

        db = DBApi(config=config)
        folder_db = FolderDB(config=config)

        sync_manager = FolderSyncManager(
            config=config,
            db=db,
            folder_db=folder_db,
            server_id=server_id,
            skip_ssl_verify=skip_ssl_verify,
        )

        if not sync_manager.connect():
            msg = "Not authenticated. Run 'n8n-deploy folder auth' first."
            console.print(msg if no_emoji else f"[yellow]{msg}[/yellow]")
            raise click.Abort()

        if dry_run:
            console.print("[yellow]Dry run mode - no changes will be made[/yellow]" if not no_emoji else "Dry run mode")

        if mapping_id:
            # Sync specific mapping
            mapping = folder_db.get_folder_mapping(mapping_id)
            if not mapping:
                msg = f"Mapping {mapping_id} not found"
                console.print(msg if no_emoji else f"[red]{msg}[/red]")
                raise click.Abort()

            result = sync_manager.sync_bidirectional(mapping, dry_run)
        else:
            # Sync all mappings
            result = sync_manager.sync_all_mappings(dry_run)

        # Print summary
        console.print("\n--- Sync Summary ---")
        console.print(f"  Pushed: {result.pushed}")
        console.print(f"  Pulled: {result.pulled}")
        if result.conflicts:
            console.print(f"  Conflicts: {result.conflicts}")

        if result.success:
            msg = "Sync completed successfully"
            console.print(msg if no_emoji else f"\n[green]{msg}[/green]")
        else:
            msg = "Sync completed with errors"
            console.print(msg if no_emoji else f"\n[yellow]{msg}[/yellow]")

        for err in result.errors:
            console.print(f"  Error: {err}" if no_emoji else f"  [red]Error: {err}[/red]")

        if not result.success:
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        msg = f"Error: {e}"
        console.print(msg if no_emoji else f"[red]{msg}[/red]")
        raise click.Abort()
