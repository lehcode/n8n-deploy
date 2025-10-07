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
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ..config import get_config
from ..db import DBApi
from .app import HELP_APP_DIR, HELP_JSON, HELP_NO_EMOJI, CustomCommand, CustomGroup

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
    """Check if database exists and abort with appropriate error message if not.

    Args:
        db_path: Path to the database file
        output_json: Whether to output error in JSON format
        no_emoji: Whether to suppress emoji in error messages

    Raises:
        click.Abort: If database does not exist
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


@click.group(cls=CustomGroup)
def db() -> None:
    """🎭 Database management commands

    Manage the SQLite database that stores wf metadata.
    Use 'n8n-deploy db COMMAND --help' for specific command options.
    """
    pass


@db.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--filename", type=str, default="n8n-deploy.db", help="Database filename (default: n8n-deploy.db)")
@click.option("--import", "auto_import", is_flag=True, help="Accept existing database without prompting")
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def init(data_dir: Optional[str], filename: str, auto_import: bool, output_json: bool, no_emoji: bool) -> None:
    """🎬 Initialize n8n-deploy database

    Create the SQLite database with the required schema.
    Will prompt if database already exists.

    If --filename is specified with an existing file, it will be imported automatically.

    NOTE: Database must be initialized before using other commands.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True
    # Database init only needs base folder, not wf directories
    from ..config import AppConfig

    # Check environment variable if --data-dir not provided
    if data_dir:
        base_path = Path(data_dir)
    else:
        env_app_dir = os.environ.get("N8N_DEPLOY_DATA_DIR")
        base_path = Path(env_app_dir) if env_app_dir else Path.cwd()

    config = AppConfig(base_folder=base_path, db_filename=filename)
    db_path = config.database_path

    # Auto-import if:
    # 1. --import flag explicitly provided, OR
    # 2. Custom filename provided (not default) and file exists
    custom_filename_provided = filename != "n8n-deploy.db"
    should_auto_import = auto_import or (custom_filename_provided and db_path.exists())

    # Check if database already exists
    if db_path.exists():
        # Auto-import if flag provided or custom filename with existing file
        if should_auto_import:
            # Check if database is actually initialized
            db_api_check = DBApi(config=config)
            schema_version = db_api_check.schema_api.get_schema_version()

            if schema_version > 0:
                # Database is initialized, use it
                flow_dir = os.environ.get("N8N_DEPLOY_FLOWS_DIR")

                if output_json:
                    result = {
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
                return
            else:
                # Database file exists but is not initialized - initialize it
                if no_emoji:
                    console.print(f"Database file exists at {db_path} but is not initialized. Initializing...")
                else:
                    console.print(f"🔧 Database file exists at {db_path} but is not initialized. Initializing...")
                # Continue to initialization below
        else:
            # Interactive mode - show options
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

            # Handle stdin input for automation
            if not is_interactive_mode():
                # Non-interactive mode - read choice from stdin or use default
                stdin_input = sys.stdin.read().strip()
                if stdin_input:
                    try:
                        choice = int(stdin_input)
                    except ValueError:
                        choice = 1  # Default to option 1
                else:
                    choice = 1  # Default to option 1
            else:
                # Interactive mode - prompt user
                choice = click.prompt("Choose option", type=int, default="1")

            if choice == 1:
                # Check if database is actually initialized
                db_api = DBApi(config=config)
                schema_version = db_api.schema_api.get_schema_version()

                if schema_version > 0:
                    # Database is initialized, use it
                    if no_emoji:
                        console.print("Using existing database")
                    else:
                        console.print("✅ Using existing database")
                    return
                else:
                    # Database file exists but is not initialized - initialize it
                    if no_emoji:
                        console.print("Database file exists but is not initialized. Initializing...")
                    else:
                        console.print("🔧 Database file exists but is not initialized. Initializing...")
                    # Continue to initialization below
            elif choice == 2:
                db_path.unlink()
                if no_emoji:
                    console.print("Deleted existing database")
                else:
                    console.print("🗑️ Deleted existing database")
            else:
                if no_emoji:
                    console.print("Database initialization cancelled")
                else:
                    console.print("❌ Database initialization cancelled")
                return

    # Initialize database
    db_api = DBApi(config=config)
    db_api.schema_api.initialize_database()

    # Check flow directory configuration
    flow_dir = os.environ.get("N8N_DEPLOY_FLOWS_DIR")

    # Output based on output format
    if output_json:
        result = {
            "success": True,
            "database_path": str(db_path),
            "message": "Database initialized",
            "flow_dir_configured": bool(flow_dir),
            "flow_dir": flow_dir if flow_dir else None,
        }
        # Use print() instead of console.print() to avoid Rich wrapping JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if no_emoji:
            console.print("Database initialized")
        else:
            console.print("✅ Database initialized")

        # Issue helpful warnings for unspecified directories
        if not flow_dir:
            if no_emoji:
                console.print()
                console.print("NOTE: Workflow directory not configured.")
                console.print("Set N8N_DEPLOY_FLOWS_DIR environment variable or use --flow-dir option")
                console.print("for workflow operations ('wf add', 'wf push', 'wf pull', etc.)")
            else:
                console.print()
                console.print("⚠️ NOTE: Workflow directory not configured.")
                console.print("Set N8N_DEPLOY_FLOWS_DIR environment variable or use --flow-dir option")
                console.print("for workflow operations ('wf add', 'wf push', 'wf pull', etc.)")


@db.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def status(data_dir: Optional[str], output_json: bool, no_emoji: bool) -> None:
    """📊 Show database status and statistics

    Use '--json' for machine-readable output.
    """
    # JSON output implies no emoji
    if output_json:
        no_emoji = True

    config = get_config(base_folder=data_dir)
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
@click.option("--data-dir", type=click.Path(), help=HELP_APP_DIR)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def compact(data_dir: Optional[str], no_emoji: bool) -> None:
    """🗜️ Compact database to optimize storage"""
    config = get_config(base_folder=data_dir)
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
@click.option("--data-dir", type=click.Path(), help=HELP_APP_DIR)
def backup(
    backup_path: Optional[str],
    data_dir: Optional[str],
) -> None:
    """💾 Create database backup"""
    config = get_config(base_folder=data_dir)
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
