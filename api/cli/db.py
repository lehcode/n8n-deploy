#!/usr/bin/env python3
"""
Database management commands for n8n-deploy CLI

Handles database initialization, status, maintenance, and backup operations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ..config import get_config
from ..db import DBApi
from .app import CustomGroup

console = Console()


@click.group(cls=CustomGroup)
def db() -> None:
    """🎭 Database management commands

    Manage the SQLite database that stores workflow metadata.
    Use 'n8n-deploy db COMMAND --help' for specific command options.
    """
    pass


@db.command()
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
@click.option("--no-emoji", is_flag=True, help="Disable emoji output for automation/scripting")
@click.option("--force", is_flag=True, help="Use existing database without prompting")
def init(app_dir: Optional[str], no_emoji: bool, force: bool) -> None:
    """Initialize n8n-deploy database

    Create the SQLite database with the required schema.
    Will prompt if database already exists.
    """
    # Database init only needs base folder, not workflow directories
    from ..config import AppConfig

    base_path = Path(app_dir) if app_dir else Path.cwd()
    config = AppConfig(base_folder=base_path)
    db_path = config.base_folder / "n8n-deploy.db"

    # Check if database already exists
    if db_path.exists():
        import sys

        # If force flag is set or running in non-interactive mode, use existing database
        if force or not sys.stdin.isatty():
            if no_emoji:
                console.print(f"Database already exists: {db_path}")
                console.print("Using existing database")
            else:
                console.print(f"🗄️ Database already exists: {db_path}")
                console.print("✅ Using existing database")
            return

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
        if not sys.stdin.isatty():
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
            if no_emoji:
                console.print("Using existing database")
            else:
                console.print("✅ Using existing database")
            return
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
    DBApi(config=config)
    if no_emoji:
        console.print("Database initialized")
    else:
        console.print("✅ Database initialized")

    # Issue helpful warnings for unspecified directories
    import os

    flow_dir = os.environ.get("N8N_FLOW_DIR")
    if not flow_dir:
        if no_emoji:
            console.print()
            console.print("NOTE: Workflow directory not configured.")
            console.print("Set N8N_FLOW_DIR environment variable or use --flow-dir option")
            console.print("for workflow operations (add, list, etc.)")
        else:
            console.print()
            console.print("📁 NOTE: Workflow directory not configured.")
            console.print("Set N8N_FLOW_DIR environment variable or use --flow-dir option")
            console.print("for workflow operations (add, list, etc.)")


@db.command()
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def status(app_dir: Optional[str], format: str) -> None:
    """Show database status and statistics

    Display database path, size, schema version, and record counts.
    Use --format json for machine-readable output.
    """
    config = get_config(base_folder=app_dir)
    db = DBApi(config=config)

    # Get database statistics
    stats = db.get_database_stats()

    status_data = {
        "database_path": stats.database_path,
        "database_size": stats.database_size,
        "schema_version": stats.schema_version,
        "workflow_count": stats.tables.get("workflows", 0),
        "api_key_count": stats.tables.get("api_keys", 0),
    }

    if format == "json":
        console.print(JSON(json.dumps(status_data, indent=2, default=str)))
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


@db.command()
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
@click.option("--no-emoji", is_flag=True, help="Disable emoji output for automation/scripting")
def compact(app_dir: Optional[str], no_emoji: bool) -> None:
    """Compact database to optimize storage"""
    config = get_config(base_folder=app_dir)
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


@db.command()
@click.argument("backup_path", required=False)
@click.option("--app-dir", type=click.Path(), help="Application directory for database and backups")
def backup(
    backup_path: Optional[str],
    app_dir: Optional[str],
) -> None:
    """Create database backup"""
    config = get_config(base_folder=app_dir)

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
