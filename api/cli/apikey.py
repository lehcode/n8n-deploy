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
from ..config import AppConfig
from ..db import DBApi
from .app import CustomGroup
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


@apikey.command("add")
@click.argument("key", required=False)
@click.option("--name", required=True, help="API key name (alphanumeric, underscore, dash only)")
@click.option("--description", help="Description of the API key")
@click.option("--expires-in", type=int, help="Number of days until expiration")
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
@click.option("--no-emoji", is_flag=True, help="Disable emoji output for automation/scripting")
def add_apikey(
    key: Optional[str],
    name: str,
    description: Optional[str],
    expires_in: Optional[int],
    app_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """🔑 Add new API key

    Store an API key with a name for later use with n8n server operations.
    The API key should be a valid n8n JWT token.

    \b
    Examples:
      n8n-deploy apikey add eyJhbGci... --name my_server --description "Production n8n"
      echo "eyJhbGci..." | n8n-deploy apikey add - --name my_server
    """
    # Read key from stdin if no key argument provided or if key argument is "-"
    if key is None or key == "-":
        key = sys.stdin.read().strip()
        if not key:
            cli_error("No API key provided via stdin", no_emoji)

    # Validate API key name format - handle edge cases gracefully
    if len(name.strip()) == 0:
        cli_error("API key name cannot be empty", no_emoji)

    if len(name) > 100:  # Reasonable limit for name length
        cli_error("API key name too long (maximum 100 characters)", no_emoji)

    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        cli_error("API key name must contain only letters, numbers, underscores, and dashes", no_emoji)

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
        # API key operations only need base folder, not workflow directories
        base_path = Path(app_dir) if app_dir else Path.cwd()
        config = AppConfig(base_folder=base_path)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        key_id = key_api.add_api_key(
            name=name,
            api_key=key,
            description=description,
            expires_days=expires_in,
        )

        if no_emoji:
            console.print(f"API key '{name}' added successfully")
            console.print(f"ID: {key_id}")
            if expires_in:
                console.print(f"Expires in: {expires_in} days")
        else:
            console.print(f"✅ API key '{name}' added successfully")
            console.print(f"   ID: {key_id}")
            if expires_in:
                console.print(f"   Expires in: {expires_in} days")
    except Exception as e:
        if no_emoji:
            console.print(f"Error: Failed to add API key: {e}")
        else:
            console.print(f"❌ Error: Failed to add API key: {e}")
        raise click.Abort()


@apikey.command("list")
@click.option("--show-keys", is_flag=True, help="Show actual API keys (use with caution)")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
@click.option("--no-emoji", is_flag=True, help="Disable emoji output for automation/scripting")
def list_apikeys(show_keys: bool, format: str, app_dir: Optional[str], no_emoji: bool) -> None:
    """📋 List all stored API keys

    Display all stored API keys with metadata (keys are hidden by default).
    Use --format json for machine-readable output.
    """
    try:
        # API key operations only need base folder, not workflow directories
        base_path = Path(app_dir) if app_dir else Path.cwd()
        config = AppConfig(base_folder=base_path)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        keys = key_api.list_api_keys()

        if format == "json":
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
            table.add_column("Last Used", style="yellow")
            table.add_column("Status", style="magenta")
            table.add_column("Description", style="dim")
            if show_keys:
                table.add_column("API Key", style="red")

            for key in keys:
                created = key["created_at"]
                if isinstance(created, str):
                    created = created[:16]  # Truncate datetime

                last_used = key["last_used"]
                if last_used:
                    last_used = str(last_used)[:16] if isinstance(last_used, str) else str(last_used)[:16]
                else:
                    last_used = "Never"

                # Use text-only status for consistency
                status_icons = {
                    "active": "Active",
                    "inactive": "Inactive",
                    "expired": "Expired",
                    "expiring_soon": "Expiring Soon",
                }
                status = status_icons.get(key["status"], key["status"])

                row_data = [
                    key["name"],
                    str(key["id"]),
                    str(created),
                    last_used,
                    status,
                    key["description"] or "",
                ]
                if show_keys:
                    row_data.append(key.get("api_key", "***"))
                table.add_row(*row_data)

            console.print(table)
    except Exception as e:
        raise click.ClickException(f"Failed to list API keys: {e}")


@apikey.command("get")
@click.argument("key_name_or_id")
@click.option("--show-key", is_flag=True, help="Show the actual API key (use with caution)")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
@click.option("--no-emoji", is_flag=True, help="Disable emoji output for automation/scripting")
def get_apikey(key_name_or_id: str, show_key: bool, format: str, app_dir: Optional[str], no_emoji: bool) -> None:
    """🔍 Get API key details"""
    # API key operations only need base folder, not workflow directories
    try:
        base_path = Path(app_dir) if app_dir else Path.cwd()
        config = AppConfig(base_folder=base_path)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
    except Exception as e:
        if no_emoji:
            console.print(f"Error: Failed to retrieve API key: {e}")
        else:
            console.print(f"❌ Error: Failed to retrieve API key: {e}")
        raise click.Abort()

    if show_key:
        api_key = key_api.get_api_key(key_name_or_id)
        if api_key:
            if no_emoji:
                console.print(f"API key retrieved: {key_name_or_id}")
                console.print(f"Key: {api_key}")
            else:
                console.print(f"✅ API key retrieved: {key_name_or_id}")
                console.print(f"   Key: {api_key}")
        else:
            if no_emoji:
                console.print(f"API key not found: {key_name_or_id}")
            else:
                console.print(f"❌ API key not found: {key_name_or_id}")
            raise click.Abort()
    else:
        # Just test if key exists and is valid
        success = key_api.test_api_key(key_name_or_id)
        if success:
            if no_emoji:
                console.print(f"API key is valid and accessible: {key_name_or_id}")
            else:
                console.print(f"✅ API key is valid and accessible: {key_name_or_id}")
        else:
            if no_emoji:
                console.print(f"API key not found or invalid: {key_name_or_id}")
            else:
                console.print(f"❌ API key not found or invalid: {key_name_or_id}")
            raise click.Abort()


@apikey.command("deactivate")
@click.argument("key_name")
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
def deactivate_apikey(key_name: str, app_dir: Optional[str]) -> None:
    """🚫 Deactivate API key (soft delete)"""
    try:
        # API key operations only need base folder, not workflow directories
        base_path = Path(app_dir) if app_dir else Path.cwd()
        config = AppConfig(base_folder=base_path)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.deactivate_api_key(key_name)
        if not success:
            raise click.ClickException("Failed to deactivate API key")
    except Exception as e:
        raise click.ClickException(f"Failed to deactivate API key: {e}")


@apikey.command("delete")
@click.argument("key_name")
@click.option("--confirm", is_flag=True, help="Confirm permanent deletion")
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
def delete_apikey(key_name: str, confirm: bool, app_dir: Optional[str]) -> None:
    """🗑️ Permanently delete an API key"""
    try:
        # API key operations only need base folder, not workflow directories
        base_path = Path(app_dir) if app_dir else Path.cwd()
        config = AppConfig(base_folder=base_path)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.delete_api_key(key_name, confirm=confirm)
        if not success:
            raise click.ClickException("Failed to delete API key")
    except Exception as e:
        raise click.ClickException(f"Failed to delete API key: {e}")


@apikey.command("test")
@click.argument("key_name")
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
def test_apikey(key_name: str, app_dir: Optional[str]) -> None:
    """🧪 Test API key validity"""
    try:
        # API key operations only need base folder, not workflow directories
        base_path = Path(app_dir) if app_dir else Path.cwd()
        config = AppConfig(base_folder=base_path)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.test_api_key(key_name)
        if not success:
            raise click.ClickException("API key test failed")
    except Exception as e:
        raise click.ClickException(f"Failed to test API key: {e}")
