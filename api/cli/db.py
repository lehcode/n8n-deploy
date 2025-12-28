#!/usr/bin/env python3
"""
Database management commands for n8n-deploy CLI

Handles database initialization, status, maintenance, and backup operations.

Exports:
    - db: Database command group
    - check_database_exists: Helper function for database existence validation
    - is_interactive_mode: Helper function to detect interactive mode
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from ..config import get_config, AppConfig
from ..db import DBApi
from .app import cli_data_dir_help, handle_verbose_flag, HELP_DB_FILENAME, HELP_JSON, HELP_NO_EMOJI, CustomCommand, CustomGroup

console = Console()


def is_interactive_mode() -> bool:
    """Detect if running in interactive mode.

    Checks multiple indicators in priority order:
    1. CI environment variables (CI, JENKINS, GITLAB_CI, etc.)
    2. TERM environment variable
    3. stdin.isatty() check

    Returns:
        bool: True if interactive mode, False otherwise
    """
    # Check for common CI/automation environment variables
    ci_vars = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "JENKINS",
        "JENKINS_URL",
        "GITLAB_CI",
        "GITHUB_ACTIONS",
        "TRAVIS",
        "CIRCLECI",
        "BUILDKITE",
        "DRONE",
        "TEAMCITY_VERSION",
    ]

    for var in ci_vars:
        if os.environ.get(var):
            return False

    # Check TERM variable (unset or "dumb" in non-interactive environments)
    term = os.environ.get("TERM", "")
    if not term or term == "dumb":
        return False

    # Final check: stdin.isatty()
    return sys.stdin.isatty()


def check_database_exists(db_path: Path, output_json: bool = False, no_emoji: bool = False) -> None:
    """Check if database exists and is initialized, abort with error message if not.

    Args:
        db_path: Path to the database file
        output_json: Whether to output error in JSON format
        no_emoji: Whether to suppress emoji in error messages

    Raises:
        click.Abort: If database does not exist or is not initialized
    """
    if not db_path.exists():
        if output_json:
            error_data = {
                "success": False,
                "error": "database_not_found",
                "message": f"Database does not exist at {db_path}",
                "suggestion": "Run 'n8n-deploy db init' to create it",
            }
            console.print(json.dumps(error_data, indent=2))
        else:
            error_msg = f"Database does not exist at {db_path}. Run 'n8n-deploy db init' to create it."
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]❌ {error_msg}[/red]")
        raise click.Abort()

    # Check if database is initialized by checking for schema_info table
    import sqlite3

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_info'")
        has_schema = cursor.fetchone() is not None
        conn.close()

        if not has_schema:
            if output_json:
                error_data = {
                    "success": False,
                    "error": "database_not_initialized",
                    "message": f"Database file exists at {db_path} but is not initialized",
                    "suggestion": "Run 'n8n-deploy db init --import' to initialize",
                }
                console.print(json.dumps(error_data, indent=2))
            else:
                error_msg = f"Database file exists at {db_path} but is not initialized. Run 'n8n-deploy db init --import' to initialize."
                if no_emoji:
                    console.print(error_msg)
                else:
                    console.print(f"[red]❌ {error_msg}[/red]")
            raise click.Abort()
    except sqlite3.Error as e:
        if output_json:
            error_data = {
                "success": False,
                "error": "database_error",
                "message": f"Failed to check database: {e}",
            }
            console.print(json.dumps(error_data, indent=2))
        else:
            error_msg = f"Failed to check database: {e}"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]❌ {error_msg}[/red]")
        raise click.Abort()


def _setup_init_config(data_dir: Optional[str], db_filename: str) -> Tuple[AppConfig, Path, bool]:
    """Setup configuration for init command.

    Returns:
        Tuple of (config, db_path, custom_filename_provided)
    """
    if data_dir:
        base_path = Path(data_dir)
    else:
        env_app_dir = os.environ.get("N8N_DEPLOY_DATA_DIR")
        base_path = Path(env_app_dir) if env_app_dir else Path.cwd()

    config = AppConfig(base_folder=base_path, db_filename=db_filename)
    db_path = config.database_path
    custom_filename_provided = db_filename != "n8n-deploy.db"

    return config, db_path, custom_filename_provided


def _output_existing_db_message(db_path: Path, flow_dir: Optional[str], output_json: bool, no_emoji: bool) -> None:
    """Output message for existing initialized database."""
    if output_json:
        result: Dict[str, Any] = {
            "success": True,
            "database_path": str(db_path),
            "message": "Using existing database",
            "already_exists": True,
            "flow_dir_configured": bool(flow_dir),
            "flow_dir": flow_dir if flow_dir else None,
        }
        console.print(json.dumps(result, indent=2))
    elif no_emoji:
        console.print(f"Database already exists: {db_path}")
        console.print("Using existing database")
    else:
        console.print(f"🗄️ Database already exists: {db_path}")
        console.print("✅ Using existing database")


def _handle_existing_db_auto_import(db_path: Path, config: AppConfig, output_json: bool, no_emoji: bool) -> bool:
    """Handle existing database with auto-import.

    Returns:
        True if should return early (db already initialized)
        False if should continue to initialization
    """
    db_api_check = DBApi(config=config)
    schema_version = db_api_check.schema_api.get_schema_version()

    if schema_version > 0:
        flow_dir = os.environ.get("N8N_DEPLOY_FLOWS_DIR")
        _output_existing_db_message(db_path, flow_dir, output_json, no_emoji)
        return True

    # Database file exists but is not initialized
    if no_emoji:
        console.print(f"Database file exists at {db_path} but is not initialized. Initializing...")
    else:
        console.print(f"🔧 Database file exists at {db_path} but is not initialized. Initializing...")
    return False


def _show_existing_db_options(db_path: Path, no_emoji: bool) -> None:
    """Display options for existing database."""
    if no_emoji:
        console.print(f"Database already exists: {db_path}")
        console.print("Options:")
        console.print("1. Use existing database (recommended)")
        console.print("2. Delete and recreate")
        console.print("3. Cancel")
    else:
        console.print(f"🗄️ Database already exists: {db_path}")
        console.print("Options:")
        console.print("1️⃣ Use existing database (recommended)")
        console.print("2️⃣ Delete and recreate")
        console.print("3️⃣ Cancel")


def _get_user_choice() -> int:
    """Get user choice for existing database handling."""
    if not is_interactive_mode():
        stdin_input = sys.stdin.read().strip()
        if stdin_input:
            try:
                return int(stdin_input)
            except ValueError:
                return 1
        return 1
    result: int = click.prompt("Choose option", type=int, default="1")
    return result


def _handle_existing_db_interactive(db_path: Path, config: AppConfig, no_emoji: bool) -> bool:
    """Handle existing database in interactive mode.

    Returns:
        True if should continue to initialization
        False if should return early
    """
    _show_existing_db_options(db_path, no_emoji)
    choice = _get_user_choice()

    if choice == 1:
        db_api = DBApi(config=config)
        schema_version = db_api.schema_api.get_schema_version()

        if schema_version > 0:
            if no_emoji:
                console.print("Using existing database")
            else:
                console.print("✅ Using existing database")
            return False

        if no_emoji:
            console.print("Database file exists but is not initialized. Initializing...")
        else:
            console.print("🔧 Database file exists but is not initialized. Initializing...")
        return True

    if choice == 2:
        db_path.unlink()
        if no_emoji:
            console.print("Deleted existing database")
        else:
            console.print("🗑️ Deleted existing database")
        return True

    # choice == 3 or other
    if no_emoji:
        console.print("Database initialization cancelled")
    else:
        console.print("❌ Database initialization cancelled")
    return False


def _perform_db_init(config: AppConfig, output_json: bool, no_emoji: bool) -> None:
    """Perform database initialization and output results."""
    db_api = DBApi(config=config)
    db_api.schema_api.initialize_database()

    flow_dir = os.environ.get("N8N_DEPLOY_FLOWS_DIR")
    db_path = config.database_path

    if output_json:
        result: Dict[str, Any] = {
            "success": True,
            "database_path": str(db_path),
            "message": "Database initialized",
            "flow_dir_configured": bool(flow_dir),
            "flow_dir": flow_dir if flow_dir else None,
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if no_emoji:
        console.print("Database initialized")
    else:
        console.print("✅ Database initialized")

    if not flow_dir:
        console.print()
        if no_emoji:
            console.print("NOTE: Workflow directory not configured.")
        else:
            console.print("⚠️ NOTE: Workflow directory not configured.")
        console.print("Set N8N_DEPLOY_FLOWS_DIR environment variable or use --flow-dir option")
        console.print("for workflow operations ('wf add', 'wf push', 'wf pull', etc.)")


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
def db() -> None:
    """🎭 Database management commands

    Manage the SQLite database that stores workflow metadata.
    Use 'n8n-deploy db COMMAND --help' for specific command options.
    """
    pass


@db.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, default="n8n-deploy.db", help=HELP_DB_FILENAME)
@click.option("--import", "auto_import", is_flag=True, help="Accept existing database without prompting")
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def init(data_dir: Optional[str], db_filename: str, auto_import: bool, output_json: bool, no_emoji: bool) -> None:
    """🎬 Initialize n8n-deploy database

    Create the SQLite database with the required schema.
    Will prompt if database already exists.

    If --db-filename is specified with an existing file, it will be imported automatically.

    NOTE: Database must be initialized before using other commands.
    """
    if output_json:
        no_emoji = True

    config, db_path, custom_filename_provided = _setup_init_config(data_dir, db_filename)
    should_auto_import = auto_import or (custom_filename_provided and db_path.exists())

    if db_path.exists():
        if should_auto_import:
            if _handle_existing_db_auto_import(db_path, config, output_json, no_emoji):
                return
        else:
            if not _handle_existing_db_interactive(db_path, config, no_emoji):
                return

    _perform_db_init(config, output_json, no_emoji)


@db.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def status(data_dir: Optional[str], db_filename: Optional[str], output_json: bool, no_emoji: bool) -> None:
    """📊 Show database status and statistics

    Use '--json' for machine-readable output.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    config = get_config(base_folder=data_dir, db_filename=db_filename)
    db_path = config.database_path

    # Check if database exists
    check_database_exists(db_path, output_json=output_json, no_emoji=no_emoji)

    db = DBApi(config=config)

    # Get database statistics - handle missing tables gracefully
    try:
        stats = db.get_database_stats()
    except Exception as e:
        # Database file exists but tables are missing or corrupted
        if "no such table" in str(e):
            if output_json:
                error_data = {
                    "success": False,
                    "error": "database_not_initialized",
                    "message": f"Database file exists at {db_path} but is not initialized",
                    "suggestions": [
                        "Run 'n8n-deploy db init --import' to initialize with existing workflows",
                        "Run 'n8n-deploy db init' for a fresh start",
                    ],
                }
                console.print(json.dumps(error_data, indent=2))
            else:
                error_msg = (
                    f"Database file exists at {db_path} but is not initialized.\n"
                    f"Run 'n8n-deploy db init --import' to initialize with existing workflows, "
                    f"or 'n8n-deploy db init' for a fresh start."
                )
                if no_emoji:
                    console.print(error_msg)
                else:
                    console.print(f"[red]❌ {error_msg}[/red]")
        else:
            # Other database errors
            if output_json:
                error_data = {"success": False, "error": "database_error", "message": str(e)}
                console.print(json.dumps(error_data, indent=2))
            else:
                error_msg = f"Failed to read database: {e}"
                if no_emoji:
                    console.print(error_msg)
                else:
                    console.print(f"[red]❌ {error_msg}[/red]")
        raise click.Abort()

    status_data = {
        "success": True,
        "database_path": str(stats.database_path),
        "database_size": stats.database_size,
        "schema_version": stats.schema_version,
        "workflow_count": stats.tables.get("workflows", 0),
        "api_key_count": stats.tables.get("api_keys", 0),
    }

    if output_json:
        console.print(json.dumps(status_data, indent=2))
    else:
        table = Table(title="Database Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Database Path", str(status_data["database_path"]))
        table.add_row("Database Size", f"{status_data['database_size']:,} bytes")
        table.add_row("Schema Version", str(status_data["schema_version"]))
        table.add_row("Workflows", str(status_data["workflow_count"]))
        table.add_row("API Keys", str(status_data["api_key_count"]))

        console.print(table)


@db.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def compact(data_dir: Optional[str], db_filename: Optional[str], no_emoji: bool) -> None:
    """🗜️ Compact database to optimize storage"""
    config = get_config(base_folder=data_dir, db_filename=db_filename)
    db_path = config.database_path

    # Check if database exists
    check_database_exists(db_path, no_emoji=no_emoji)

    db = DBApi(config=config)

    if no_emoji:
        console.print("Optimizing database...")
    else:
        console.print("🎭 Optimizing database...")

    # Perform compact operation
    db.compact()

    if no_emoji:
        console.print("Database optimization complete")
    else:
        console.print("✅ Database optimization complete")


@db.command(cls=CustomCommand)
@click.argument("backup_path", required=False)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
def backup(
    backup_path: Optional[str],
    data_dir: Optional[str],
    db_filename: Optional[str],
) -> None:
    """💾 Create database backup"""
    config = get_config(base_folder=data_dir, db_filename=db_filename)
    db_path = config.database_path

    # Check if database exists
    check_database_exists(db_path, no_emoji=False)

    if not backup_path:
        # Create backup in the proper backups directory with timestamp
        backup_filename = f"n8n_deploy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        if config:
            # Ensure backups directory exists
            config.backups_path.mkdir(parents=True, exist_ok=True)
            backup_path = str(config.backups_path / backup_filename)
        else:
            backup_path = backup_filename

    db = DBApi(config=config)
    db.backup(backup_path)
    console.print(f"✅ Database backup created: {backup_path}")
