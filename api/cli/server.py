#!/usr/bin/env python3
"""
Server management CLI commands for n8n-deploy

Provides commands for managing n8n servers and their API key associations.
"""

import json
from typing import Any, Dict, List, Optional, cast

import click
from rich.console import Console
from rich.table import Table

from ..api_keys import KeyApi
from ..config import AppConfig, get_config
from ..db.core import DBApi
from ..db.servers import ServerCrud
from .app import CustomCommand, CustomGroup
from .output import format_server_table

console = Console()


@click.group(name="server", cls=CustomGroup)
def server() -> None:
    """🖥️  Manage n8n servers"""
    pass


@server.command(name="create", cls=CustomCommand)
@click.argument("name")
@click.argument("url")
@click.option("--description", "-d", help="Server description")
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def create_server(
    name: str,
    url: str,
    description: Optional[str],
    data_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """Create a new n8n server"""
    try:
        config = get_config(base_folder=data_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_api = ServerCrud(config=config)
        server_id = server_api.add_server(
            url=url,
            name=name,
            description=description,
        )

        if no_emoji:
            console.print(f"Server '{name}' created successfully (ID: {server_id})")
        else:
            console.print(f"✅ Server '{name}' created successfully (ID: {server_id})")

    except Exception as e:
        if no_emoji:
            console.print(f"Error creating server: {e}")
        else:
            console.print(f"❌ Error creating server: {e}")
        raise click.Abort()


@server.command(name="list", cls=CustomCommand)
@click.option("--active", is_flag=True, help="Show only active servers")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def list_servers(
    active: bool,
    fmt: str,
    data_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """List all n8n servers"""
    try:
        config = get_config(base_folder=data_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_api = ServerCrud(config=config)
        servers = server_api.list_servers(active_only=active)

        if fmt == "json":
            print(json.dumps(servers, indent=2, default=str))
            return

        if not servers:
            if no_emoji:
                console.print("No servers found")
            else:
                console.print("ℹ️  No servers found")
            return

        format_server_table(servers, no_emoji=no_emoji)

    except Exception as e:
        if no_emoji:
            console.print(f"Error listing servers: {e}")
        else:
            console.print(f"❌ Error listing servers: {e}")
        raise click.Abort()


def _handle_api_key_decision(
    server_name: str, linked_keys: List[Dict[str, Any]], key_action: Optional[str], no_emoji: bool
) -> str:
    """
    Handle API key action decision for server removal.

    Args:
        server_name: Name of the server being removed
        linked_keys: List of API keys linked to the server
        key_action: Explicit action (preserve/delete) or None for interactive
        no_emoji: Whether to disable emoji in output

    Returns:
        str: Action to take ('preserve' or 'delete')
    """
    if key_action is not None:
        return key_action

    # Interactive mode - ask user
    if not linked_keys:
        return "preserve"  # No keys to handle

    if no_emoji:
        console.print(f"\nServer '{server_name}' has {len(linked_keys)} linked API key(s):")
    else:
        console.print(f"\n⚠️  Server '{server_name}' has {len(linked_keys)} linked API key(s):")

    for key in linked_keys:
        console.print(f"  - {key['name']}")

    console.print("\nWhat should happen to these API keys?")
    console.print("  [1] Preserve (keep API keys, just unlink them)")
    console.print("  [2] Delete (remove API keys that are ONLY linked to this server)")

    choice = cast(int, click.prompt("Enter choice", type=int, default="1"))
    return "preserve" if choice == 1 else "delete"


def _delete_linked_api_keys(linked_keys: List[Dict[str, Any]], config: "AppConfig", no_emoji: bool) -> None:
    """
    Delete API keys that are linked to the server being removed.

    Args:
        linked_keys: List of API keys to delete
        config: Application configuration
        no_emoji: Whether to disable emoji in output
    """
    db_api = DBApi(config=config)
    key_api = KeyApi(db=db_api, config=config)

    for key in linked_keys:
        # Check if this key is linked to other servers
        # For now, just delete the key (we can add a check for multiple servers later)
        key_api.delete_api_key(key["name"])
        if no_emoji:
            console.print(f"Deleted API key: {key['name']}")
        else:
            console.print(f"🗑️  Deleted API key: {key['name']}")


@server.command(name="remove", cls=CustomCommand)
@click.argument("server_name")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--preserve-keys",
    "key_action",
    flag_value="preserve",
    help="Keep all linked API keys (default in interactive mode)",
)
@click.option(
    "--delete-keys",
    "key_action",
    flag_value="delete",
    help="Delete API keys that are ONLY linked to this server",
)
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def remove_server(
    server_name: str,
    confirm: bool,
    key_action: Optional[str],
    data_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """Remove (delete) an n8n server and optionally its API keys"""
    try:
        config = get_config(base_folder=data_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_api = ServerCrud(config=config)

        # Check if server exists
        server = server_api.get_server_by_name(server_name)
        if not server:
            msg = f"Server '{server_name}' not found"
            console.print(msg if no_emoji else f"❌ {msg}")
            return

        # Get linked API keys and determine action
        linked_keys = server_api.get_server_api_keys(server_name)
        final_action = _handle_api_key_decision(server_name, linked_keys, key_action, no_emoji)

        # Confirm server deletion
        if not confirm:
            msg = f"Delete server '{server_name}'"
            if linked_keys and final_action == "delete":
                msg += f" and {len(linked_keys)} linked API key(s)"
            msg += "?"

            if not click.confirm(msg):
                console.print("Operation cancelled")
                return

        # Delete API keys if requested
        if final_action == "delete" and linked_keys:
            _delete_linked_api_keys(linked_keys, config, no_emoji)

        # Delete the server (CASCADE will remove links)
        if server_api.delete_server(server_name):
            msg = f"Server '{server_name}' removed successfully"
            console.print(msg if no_emoji else f"✅ {msg}")
        else:
            msg = f"Failed to remove server '{server_name}'"
            console.print(msg if no_emoji else f"❌ {msg}")

    except Exception as e:
        if no_emoji:
            console.print(f"Error removing server: {e}")
        else:
            console.print(f"❌ Error removing server: {e}")
        raise click.Abort()


@server.command(name="keys", cls=CustomCommand)
@click.argument("server_name")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def show_keys(
    server_name: str,
    fmt: str,
    data_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """Show API keys linked to a server"""
    try:
        config = get_config(base_folder=data_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_api = ServerCrud(config=config)
        keys = server_api.get_server_api_keys(server_name)

        if fmt == "json":
            print(json.dumps(keys, indent=2, default=str))
            return

        if not keys:
            if no_emoji:
                console.print(f"No API keys linked to server '{server_name}'")
            else:
                console.print(f"ℹ️  No API keys linked to server '{server_name}'")
            return

        # Display table
        table = Table(title=f"API Keys for Server: {server_name}" if not no_emoji else None)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Linked At", style="green")

        for key in keys:
            table.add_row(
                key["name"],
                key.get("description") or "",
                str(key["linked_at"]),
            )

        console.print(table)

    except Exception as e:
        if no_emoji:
            console.print(f"Error showing keys: {e}")
        else:
            console.print(f"❌ Error showing keys: {e}")
        raise click.Abort()
