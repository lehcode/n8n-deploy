#!/usr/bin/env python3
"""
Server management CLI commands for n8n-deploy

Provides commands for managing n8n servers and their API key associations.
"""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..config import get_config
from ..db.servers import ServerApi
from .app import CustomGroup
from .output import format_server_table

console = Console()


@click.group(name="server", cls=CustomGroup)
def server_group() -> None:
    """🖥️  Manage n8n servers"""
    pass


@server_group.command(name="create")
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
        server_api = ServerApi(config=config)
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


@server_group.command(name="list")
@click.option("--active", is_flag=True, help="Show only active servers")
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def list_servers(
    active: bool,
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
        server_api = ServerApi(config=config)
        servers = server_api.list_servers(active_only=active)

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


@server_group.command(name="delete")
@click.argument("name")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def delete_server(
    name: str,
    confirm: bool,
    data_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """Delete an n8n server"""
    try:
        config = get_config(base_folder=data_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    if not confirm:
        if not click.confirm(f"Delete server '{name}' and all its API key associations?"):
            console.print("Operation cancelled")
            return

    try:
        server_api = ServerApi(config=config)
        if server_api.delete_server(name):
            if no_emoji:
                console.print(f"Server '{name}' deleted successfully")
            else:
                console.print(f"✅ Server '{name}' deleted successfully")
        else:
            if no_emoji:
                console.print(f"Server '{name}' not found")
            else:
                console.print(f"❌ Server '{name}' not found")

    except Exception as e:
        if no_emoji:
            console.print(f"Error deleting server: {e}")
        else:
            console.print(f"❌ Error deleting server: {e}")
        raise click.Abort()


@server_group.command(name="remove")
@click.argument("server_name")
@click.argument("api_key_name")
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def remove_apikey(
    server_name: str,
    api_key_name: str,
    data_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """Remove (unlink) an API key from a server"""
    try:
        config = get_config(base_folder=data_dir)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        server_api = ServerApi(config=config)
        if server_api.unlink_api_key(server_name, api_key_name):
            if no_emoji:
                console.print(f"API key '{api_key_name}' removed from server '{server_name}'")
            else:
                console.print(f"✅ API key '{api_key_name}' removed from server '{server_name}'")
        else:
            if no_emoji:
                console.print(f"API key '{api_key_name}' not linked to server '{server_name}'")
            else:
                console.print(f"❌ API key '{api_key_name}' not linked to server '{server_name}'")

    except Exception as e:
        if no_emoji:
            console.print(f"Error removing API key: {e}")
        else:
            console.print(f"❌ Error removing API key: {e}")
        raise click.Abort()


@server_group.command(name="keys")
@click.argument("server_name")
@click.option("--data-dir", help="Application directory (overrides N8N_DEPLOY_DATA)")
@click.option("--no-emoji", is_flag=True, help="Disable emoji in output")
def show_keys(
    server_name: str,
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
        server_api = ServerApi(config=config)
        keys = server_api.get_server_api_keys(server_name)

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
