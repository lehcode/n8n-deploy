#!/usr/bin/env python3
"""
API key management commands for n8n-deploy CLI

Handles API key lifecycle management including creation, listing, retrieval,
deactivation, deletion, and testing.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ..api_keys import KeyApi
from ..config import get_config
from ..db import DBApi
from .app import HELP_APP_DIR, HELP_JSON, HELP_NO_EMOJI, HELP_TABLE, CustomCommand, CustomGroup
from .output import cli_error

console = Console()


@click.group(cls=CustomGroup)
def apikey() -> None:
    """🔐 API key management commands

    Store and manage API keys for n8n server authentication.
    Keys are stored in plain text in the local database.
    Use 'n8n-deploy apikey COMMAND --help' for specific command options.
    """
    pass


@apikey.command("add", cls=CustomCommand)
@click.argument("key", required=False)
@click.option("--name", required=True, help="API key name (UTF-8 supported, no path separators)")
@click.option("--server", help="Server name to link this API key to (uses N8N_SERVER_URL if not specified)")
@click.option("--description", help="Description of the API key")
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def add_apikey(
    key: Optional[str],
    name: str,
    server: Optional[str],
    description: Optional[str],
    no_emoji: bool,
) -> None:
    """🔑 Add new API key

    Store an API key with a name for later use with n8n server operations.
    The API key should be a valid n8n JWT token.

    If --server is specified, the API key will be automatically linked to that server.
    If --server is not specified but N8N_SERVER_URL is set, a server will be created
    from that URL and the key will be linked to it.

    \b
    Examples:
      n8n-deploy apikey add eyJhbGci... --name my_key --server production
      echo "eyJhbGci..." | n8n-deploy apikey add - --name my_key --server staging
      N8N_SERVER_URL=http://n8n.local n8n-deploy apikey add - --name my_key
    """
    # Read key from stdin if no key argument provided or if key argument is "-"
    if key is None or key == "-":
        key = sys.stdin.read().strip()
        if not key:
            cli_error("No API key provided via stdin", no_emoji)

    # Validate API key name format - handle edge cases gracefully
    stripped_name = name.strip()

    if len(stripped_name) == 0:
        cli_error("API key name cannot be empty", no_emoji)

    if len(name) > 100:  # Reasonable limit for name length
        cli_error("API key name too long (maximum 100 characters)", no_emoji)

    # Allow UTF-8 characters and spaces, only block security risks (null bytes, path separators)
    if any(c in stripped_name for c in "\x00/\\"):
        cli_error("API key name cannot contain null bytes or path separators (/ \\)", no_emoji)

    # Validate API key format - handle edge cases gracefully
    key = key.strip()  # Remove whitespace

    if len(key) == 0:
        cli_error("API key cannot be empty", no_emoji)

    if len(key) > 2000:  # Reasonable limit for JWT tokens
        cli_error("API key too long (maximum 2000 characters)", no_emoji)

    # Check for basic JWT pattern but be more lenient for testing
    # JWT tokens should have 3 parts separated by dots
    jwt_parts = key.split(".")
    if len(jwt_parts) != 3:
        cli_error("API key must be a valid JWT token (format: header.payload.signature)", no_emoji)

    # Validate each part contains only valid JWT characters
    jwt_char_pattern = r"^[A-Za-z0-9_-]*$"  # Allow empty parts for edge case testing
    for i, part in enumerate(jwt_parts):
        if not re.match(jwt_char_pattern, part):
            cli_error(f"Invalid characters in JWT token part {i + 1}", no_emoji)

    try:
        import os
        from ..db.servers import ServerCrud

        # Use default config from environment variables
        config = get_config()
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        key_id = key_api.add_api_key(
            name=name,
            api_key=key,
            description=description,
        )

        if no_emoji:
            console.print(f"API key '{name}' added successfully")
            console.print(f"ID: {key_id}")
        else:
            console.print(f"✅ API key '{name}' added successfully")
            console.print(f"   ID: {key_id}")

        # Link to server if --server specified or N8N_SERVER_URL is set
        server_name = server
        server_url = os.getenv("N8N_SERVER_URL")

        if server_name or server_url:
            server_api = ServerCrud(config=config)

            # If --server specified, link to that server
            if server_name:
                try:
                    server_api.link_api_key(server_name, name)
                    if no_emoji:
                        console.print(f"API key '{name}' linked to server '{server_name}'")
                    else:
                        console.print(f"🔗 API key '{name}' linked to server '{server_name}'")
                except ValueError as e:
                    if no_emoji:
                        console.print(f"Warning: {e}")
                        console.print(f"Server '{server_name}' not found. Create it with:")
                        console.print(f"  n8n-deploy server create {server_name} <url>")
                    else:
                        console.print(f"⚠️  {e}")
                        console.print(f"   Server '{server_name}' not found. Create it with:")
                        console.print(f"   n8n-deploy server create {server_name} <url>")

            # If N8N_SERVER_URL is set but --server not specified, create/use server from URL
            elif server_url:
                # Check if server with this URL already exists
                existing_server = server_api.get_server_by_url(server_url)
                if existing_server:
                    existing_server_name = str(existing_server["name"])
                    try:
                        server_api.link_api_key(existing_server_name, name)
                        if no_emoji:
                            console.print(
                                f"API key '{name}' linked to existing server '{existing_server_name}' ({server_url})"
                            )
                        else:
                            console.print(
                                f"🔗 API key '{name}' linked to existing server '{existing_server_name}' ({server_url})"
                            )
                    except ValueError as e:
                        if no_emoji:
                            console.print(f"Warning: Failed to link to server: {e}")
                        else:
                            console.print(f"⚠️  Failed to link to server: {e}")
                else:
                    # Create new server from URL
                    auto_server_name = f"Auto server {key_id}"
                    try:
                        server_api.add_server(url=server_url, name=auto_server_name)
                        server_api.link_api_key(auto_server_name, name)
                        if no_emoji:
                            console.print(f"Server '{auto_server_name}' created from N8N_SERVER_URL ({server_url})")
                            console.print(f"API key '{name}' linked to server '{auto_server_name}'")
                        else:
                            console.print(f"✨ Server '{auto_server_name}' created from N8N_SERVER_URL ({server_url})")
                            console.print(f"🔗 API key '{name}' linked to server '{auto_server_name}'")
                    except Exception as e:
                        if no_emoji:
                            console.print(f"Warning: Failed to create/link server: {e}")
                        else:
                            console.print(f"⚠️  Failed to create/link server: {e}")

    except Exception as e:
        if no_emoji:
            console.print(f"Error: Failed to add API key: {e}")
        else:
            console.print(f"❌ Error: Failed to add API key: {e}")
        raise click.Abort()


@apikey.command("list", cls=CustomCommand)
@click.option("--unmask", is_flag=True, help="Display actual credentials (SECURITY WARNING: use with extreme caution)")
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list_apikeys(unmask: bool, output_json: bool, output_table: bool, no_emoji: bool) -> None:
    """📋 List all stored API keys

    Display all stored API keys with metadata (credentials are masked by default).
    Use --json for machine-readable output.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    try:
        # Use default config from environment variables
        config = get_config()
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        keys = key_api.list_api_keys()

        if output_json:
            console.print(JSON(json.dumps(keys, indent=2, default=str)))
        else:
            if not keys:
                if no_emoji:
                    console.print("No API keys found")
                else:
                    console.print("🔐 No API keys found")
                return

            if no_emoji:
                table = Table(title="API Keys")
            else:
                table = Table(title="🔐 API Keys")
            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Created", style="blue")
            table.add_column("Status", style="magenta")
            table.add_column("Description", style="dim")
            if unmask:
                table.add_column("API Key", style="red")

            for key in keys:
                created = key["created_at"]
                if isinstance(created, str):
                    created = created[:16]  # Truncate datetime

                # Determine status based on is_active
                status = "Active" if key.get("is_active", True) else "Inactive"

                row_data = [
                    key["name"],
                    str(key["id"]),
                    str(created),
                    status,
                    key["description"] or "",
                ]
                if unmask:
                    row_data.append(key.get("api_key", "***"))
                else:
                    # Mask credentials by default
                    pass  # Don't add API key column at all
                table.add_row(*row_data)

            console.print(table)
    except Exception as e:
        raise click.ClickException(f"Failed to list API keys: {e}")


@apikey.command("deactivate", cls=CustomCommand)
@click.argument("key_name")
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def deactivate_apikey(key_name: str, no_emoji: bool) -> None:
    """🚫 Deactivate API key (soft delete)"""
    try:
        # Use default config from environment variables
        config = get_config()
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.deactivate_api_key(key_name)
        if not success:
            raise click.ClickException("Failed to deactivate API key")
    except Exception as e:
        if no_emoji:
            console.print(f"Error: Failed to deactivate API key: {e}")
        else:
            console.print(f"❌ Error: Failed to deactivate API key: {e}")
        raise click.Abort()


@apikey.command("delete", cls=CustomCommand)
@click.argument("key_name")
@click.option("--confirm", is_flag=True, help="Confirm permanent deletion")
def delete_apikey(key_name: str, confirm: bool) -> None:
    """🗑️ Permanently delete an API key"""
    try:
        # Use default config from environment variables
        config = get_config()
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.delete_api_key(key_name, confirm=confirm)
        if not success:
            raise click.ClickException("Failed to delete API key")
    except Exception as e:
        raise click.ClickException(f"Failed to delete API key: {e}")


@apikey.command("test", cls=CustomCommand)
@click.argument("key_name")
def test_apikey(key_name: str) -> None:
    """🧪 Test API key validity"""
    try:
        # Use default config from environment variables
        config = get_config()
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.test_api_key(key_name)
        if not success:
            raise click.ClickException("API key test failed")
    except Exception as e:
        raise click.ClickException(f"Failed to test API key: {e}")
