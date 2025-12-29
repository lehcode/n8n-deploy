#!/usr/bin/env python3
"""
API key management commands for n8n-deploy CLI

Handles API key lifecycle management including creation, listing, retrieval,
deactivation, deletion, and testing.
"""

import json
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ..api_keys import KeyApi
from ..config import get_config
from ..db import DBApi
from ..jwt_utils import check_jwt_expiration, format_expiration_date, get_jwt_issued_at
from .app import cli_data_dir_help, handle_verbose_flag, HELP_DB_FILENAME, HELP_JSON, HELP_NO_EMOJI, CustomCommand, CustomGroup
from .output import cli_error

console = Console()


def _validate_apikey_name(name: str, no_emoji: bool) -> str:
    """Validate and return stripped API key name.

    Raises click.Abort on validation failure.
    """
    stripped_name = name.strip()

    if len(stripped_name) == 0:
        cli_error("API key name cannot be empty", no_emoji)
        raise click.Abort()

    if len(name) > 100:
        cli_error("API key name too long (maximum 100 characters)", no_emoji)
        raise click.Abort()

    # Allow UTF-8 characters and spaces, only block security risks
    if any(c in stripped_name for c in "\x00/\\"):
        cli_error("API key name cannot contain null bytes or path separators (/ \\)", no_emoji)
        raise click.Abort()

    return stripped_name


def _validate_apikey_value(key: Optional[str], no_emoji: bool) -> str:
    """Validate and return the API key value.

    Reads from stdin if key is None or "-".
    Raises click.Abort on validation failure.
    """
    # Read from stdin if needed
    if key is None or key == "-":
        key = sys.stdin.read().strip()
        if not key:
            cli_error("No API key provided via stdin", no_emoji)
            raise click.Abort()

    key = key.strip()

    if len(key) == 0:
        cli_error("API key cannot be empty", no_emoji)
        raise click.Abort()

    if len(key) > 2000:
        cli_error("API key too long (maximum 2000 characters)", no_emoji)
        raise click.Abort()

    # Check for basic JWT pattern
    jwt_parts = key.split(".")
    if len(jwt_parts) != 3:
        cli_error("API key must be a valid JWT token (format: header.payload.signature)", no_emoji)
        raise click.Abort()

    # Validate each part contains only valid JWT characters
    jwt_char_pattern = r"^[A-Za-z0-9_-]*$"
    for i, part in enumerate(jwt_parts):
        if not re.match(jwt_char_pattern, part):
            cli_error(f"Invalid characters in JWT token part {i + 1}", no_emoji)
            raise click.Abort()

    return key


def _link_apikey_to_server(config: Any, key_name: str, server: str, no_emoji: bool) -> None:
    """Link API key to a server, with helpful error message if server not found."""
    from ..db.servers import ServerCrud

    server_api = ServerCrud(config=config)
    try:
        server_api.link_api_key(server, key_name)
        if no_emoji:
            console.print(f"API key '{key_name}' linked to server '{server}'")
        else:
            console.print(f"🔗 API key '{key_name}' linked to server '{server}'")
    except ValueError as e:
        if no_emoji:
            console.print(f"Warning: {e}")
            console.print(f"Server '{server}' not found. Create it with:")
            console.print(f"  n8n-deploy server create {server} <url>")
        else:
            console.print(f"⚠️  {e}")
            console.print(f"   Server '{server}' not found. Create it with:")
            console.print(f"   n8n-deploy server create {server} <url>")


def _output_apikey_success(key_name: str, key_id: int, no_emoji: bool) -> None:
    """Output success message after adding API key."""
    if no_emoji:
        console.print(f"API key '{key_name}' added successfully")
        console.print(f"ID: {key_id}")
    else:
        console.print(f"✅ API key '{key_name}' added successfully")
        console.print(f"   ID: {key_id}")


def _get_key_created_date(key: Dict[str, Any]) -> str:
    """Extract created date from JWT or fallback to database timestamp."""
    api_key_value = key.get("api_key")
    if api_key_value:
        iat_datetime = get_jwt_issued_at(api_key_value)
        if iat_datetime:
            return iat_datetime.strftime("%Y-%m-%d %H:%M")

    created = key["created_at"]
    if isinstance(created, str):
        return created[:16]
    return str(created)


def _get_key_status(key: Dict[str, Any], no_emoji: bool) -> Tuple[str, bool]:
    """Determine key status display.

    Returns:
        Tuple of (status_display, is_expired)
    """
    is_active = key.get("is_active", True)
    api_key_value = key.get("api_key")

    # Check if expired
    is_expired = False
    if api_key_value:
        is_expired, _, _ = check_jwt_expiration(api_key_value)

    if is_expired:
        return ("Expired" if no_emoji else "❌ Expired"), True
    if not is_active:
        return ("Inactive" if no_emoji else "❌"), False
    return ("Active" if no_emoji else "✅"), False


def _get_key_expiry_display(key: Dict[str, Any]) -> str:
    """Get expiry display string with formatting."""
    api_key_value = key.get("api_key")
    if not api_key_value:
        return "N/A"

    is_expired, exp_datetime, warning = check_jwt_expiration(api_key_value)
    if not exp_datetime:
        return "N/A"

    expiry_display = format_expiration_date(exp_datetime)
    if is_expired:
        return f"[red]{expiry_display}[/red]"
    if warning:
        return f"[yellow]{expiry_display}[/yellow]"
    return expiry_display


def _build_apikey_table_row(key: Dict[str, Any], unmask: bool, no_emoji: bool) -> List[str]:
    """Build a single table row for an API key."""
    created = _get_key_created_date(key)

    added = key["created_at"]
    if isinstance(added, str):
        added = added[:16]

    status, _ = _get_key_status(key, no_emoji)
    expiry_display = _get_key_expiry_display(key)
    key_display = key.get("api_key", "***") if unmask else "***"
    server_display = key.get("server_url") or "N/A"

    return [
        key["name"],
        str(key["id"]),
        server_display,
        str(created),
        str(added),
        status,
        expiry_display,
        key_display,
    ]


def _output_apikey_table(keys: List[Dict[str, Any]], unmask: bool, no_emoji: bool) -> None:
    """Build and output the API keys table."""
    title = "API Keys" if no_emoji else "🔐 API Keys"
    table = Table(title=title)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("ID", style="dim")
    table.add_column("Server", style="blue", overflow="fold")
    table.add_column("Created", style="blue")
    table.add_column("Added", style="green")
    table.add_column("Status", style="magenta", justify="center")
    table.add_column("Expires", style="yellow")
    table.add_column("Key", style="dim" if not unmask else "red")

    for key in keys:
        row_data = _build_apikey_table_row(key, unmask, no_emoji)
        table.add_row(*row_data)

    console.print(table)


@click.group(cls=CustomGroup)
@click.option(
    "-v",
    "--verbose",
    count=True,
    expose_value=False,
    is_eager=True,
    callback=handle_verbose_flag,
    help="Verbosity level (-v, -vv)",
)
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
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def add_apikey(
    key: Optional[str],
    name: str,
    server: Optional[str],
    description: Optional[str],
    data_dir: Optional[str],
    db_filename: Optional[str],
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
    # Validate inputs using helper functions
    _validate_apikey_name(name, no_emoji)
    validated_key = _validate_apikey_value(key, no_emoji)

    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        key_id = key_api.add_api_key(
            name=name,
            api_key=validated_key,
            description=description,
        )

        _output_apikey_success(name, key_id, no_emoji)

        if server:
            _link_apikey_to_server(config, name, server, no_emoji)

    except click.Abort:
        raise
    except Exception as e:
        if no_emoji:
            console.print(f"Error: Failed to add API key: {e}")
        else:
            console.print(f"❌ Error: Failed to add API key: {e}")
        raise click.Abort()


@apikey.command("list", cls=CustomCommand)
@click.option("--unmask", is_flag=True, help="Display actual credentials (SECURITY WARNING: use with extreme caution)")
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def list_apikeys(unmask: bool, output_json: bool, data_dir: Optional[str], db_filename: Optional[str], no_emoji: bool) -> None:
    """📋 List all stored API keys

    Display all stored API keys with metadata (credentials are masked by default).
    Use --json for machine-readable output.
    """
    if output_json:
        no_emoji = True

    try:
        config = get_config(base_folder=data_dir, db_filename=db_filename)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        keys = key_api.list_api_keys(unmask=unmask)

        if output_json:
            print(json.dumps(keys, indent=2, default=str))
            return

        if not keys:
            console.print("No API keys found" if no_emoji else "🔐 No API keys found")
            return

        _output_apikey_table(keys, unmask, no_emoji)

    except Exception as e:
        raise click.ClickException(f"Failed to list API keys: {e}")


@apikey.command("activate", cls=CustomCommand)
@click.argument("key_name")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def activate_apikey(key_name: str, data_dir: Optional[str], db_filename: Optional[str], no_emoji: bool) -> None:
    """✅ Activate API key (restore from deactivation)"""
    try:
        # Use default config from environment variables
        config = get_config(base_folder=data_dir, db_filename=db_filename)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.activate_api_key(key_name)
        if not success:
            raise click.ClickException("Failed to activate API key")
    except Exception as e:
        if no_emoji:
            console.print(f"Error: Failed to activate API key: {e}")
        else:
            console.print(f"❌ Error: Failed to activate API key: {e}")
        raise click.Abort()


@apikey.command("deactivate", cls=CustomCommand)
@click.argument("key_name")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def deactivate_apikey(key_name: str, data_dir: Optional[str], db_filename: Optional[str], no_emoji: bool) -> None:
    """🚫 Deactivate API key (soft delete)"""
    try:
        # Use default config from environment variables
        config = get_config(base_folder=data_dir, db_filename=db_filename)
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
@click.option("--force", is_flag=True, help="Force permanent deletion without confirmation")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def delete_apikey(key_name: str, force: bool, data_dir: Optional[str], db_filename: Optional[str], no_emoji: bool) -> None:
    """🗑️ Permanently delete an API key

    Without --force flag, prompts for confirmation (type 'yes' to confirm).

    \b
    Examples:
      n8n-deploy apikey delete my_key --force        # Skip confirmation
      echo "yes" | n8n-deploy apikey delete my_key   # Confirm via stdin
    """
    try:
        # Use default config from environment variables
        config = get_config(base_folder=data_dir, db_filename=db_filename)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)

        # If not forced, ask for confirmation
        if not force:
            if no_emoji:
                console.print(f"About to permanently delete API key: {key_name}")
                console.print("Type 'yes' to confirm: ", end="")
            else:
                console.print(f"⚠️  About to permanently delete API key: {key_name}")
                console.print("   Type 'yes' to confirm: ", end="")

            confirmation = input().strip().lower()
            if confirmation != "yes":
                if no_emoji:
                    console.print("Deletion cancelled")
                else:
                    console.print("❌ Deletion cancelled")
                raise click.Abort()
            force = True  # User confirmed, proceed with deletion

        success = key_api.delete_api_key(key_name, force=force, no_emoji=no_emoji)
        if not success:
            raise click.ClickException("Failed to delete API key")
    except click.Abort:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to delete API key: {e}")


@apikey.command("test", cls=CustomCommand)
@click.argument("key_name")
@click.option("--server-url", help="Server URL to test against (uses N8N_SERVER_URL if not specified)")
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification (for self-signed certificates)")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def test_apikey(
    key_name: str,
    server_url: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
) -> None:
    """🧪 Test API key validity against n8n server

    Test if the API key can authenticate successfully with an n8n server.

    \b
    Examples:
      n8n-deploy apikey test my_key --server-url http://n8n.local:5678
      N8N_SERVER_URL=http://n8n.local n8n-deploy apikey test my_key
      n8n-deploy apikey test my_key --server-url https://n8n.local --skip-ssl-verify
    """
    try:
        # Use default config from environment variables
        config = get_config(base_folder=data_dir, db_filename=db_filename)
        db_api = DBApi(config=config)
        key_api = KeyApi(db=db_api, config=config)
        success = key_api.test_api_key(key_name, server_url=server_url, skip_ssl_verify=skip_ssl_verify, no_emoji=no_emoji)
        if not success:
            raise click.ClickException("API key test failed")
    except Exception as e:
        raise click.ClickException(f"Failed to test API key: {e}")
