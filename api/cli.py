#!/usr/bin/env python3
"""
CLI interface for the Python workflow manager
"""

import click
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.json import JSON

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.manager import WorkflowManager
from api.n8n_deploy_db import n8n_deploy_DB
from api.config import get_config
from api.api_keys import ApiKeyManager


console = Console()


@click.group()
@click.option(
    "--app-dir",
    type=click.Path(),
    help="Application directory for n8n-deploy data (database, backups). Defaults to current directory if not specified.",
)
@click.option(
    "--flow-dir",
    type=click.Path(),
    help="Flow folder for workflow files. Uses N8N_FLOW_DIR env var or same as app directory if not specified.",
)
@click.option(
    "--no-emoji", is_flag=True, help="Disable emoji output for script parsing"
)
@click.version_option(version="2.0.0", prog_name="n8n-deploy")
@click.pass_context
def cli(
    ctx: click.Context,
    app_dir: Optional[str],
    flow_dir: Optional[str],
    no_emoji: bool,
) -> None:
    """🎭 n8n-deploy - a simple N8N Workflow Manager

    Simple n8n workflow deployment tool with SQLite metadata store.
    """
    ctx.ensure_object(dict)

    # Store emoji preference
    ctx.obj["no_emoji"] = no_emoji

    # Use new configuration system
    config = get_config(base_folder=app_dir, flow_folder=flow_dir)
    ctx.obj["config"] = config


@cli.command()
@click.argument("workflow_id")
@click.pass_context
def pull(ctx: click.Context, workflow_id: str) -> None:
    """📥 Pull workflow from n8n instance"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    success = manager.pull_workflow(workflow_id)
    if not success:
        raise click.ClickException("Failed to pull workflow")


@cli.command()
@click.argument("workflow_id")
@click.pass_context
def push(ctx: click.Context, workflow_id: str) -> None:
    """📤 Push workflow to n8n instance"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    success = manager.push_workflow(workflow_id)
    if not success:
        raise click.ClickException("Failed to push workflow")


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option("--only", is_flag=True, help="Show only workflows that can be backed up")
@click.option("--table", is_flag=True, help="Force table output (overrides --format)")
@click.pass_context
def list(ctx: click.Context, format: str, only: bool, table: bool) -> None:
    """📋 List all workflows"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    workflows = manager.list_workflows(only_backupable=only)

    # Force table format if --table flag is used
    if table:
        format = "table"

    if format == "json":
        console.print(JSON(json.dumps(workflows, indent=2, default=str)))
    else:
        no_emoji = ctx.obj.get("no_emoji", False)

        # Tables always exclude emojis for better shell compatibility
        title = f"Workflows{' (Backupable Only)' if only else ''}"

        table_obj = Table(title=title)
        table_obj.add_column("ID", style="cyan")
        table_obj.add_column("Name", style="green")
        table_obj.add_column("Type", style="yellow")
        table_obj.add_column("Status", style="red")
        table_obj.add_column("File Exists", justify="center")
        table_obj.add_column("Backupable", justify="center")
        table_obj.add_column("Nodes", justify="right")
        table_obj.add_column("Last Synced", style="dim")

        for wf in workflows:
            last_synced = (
                wf["last_synced"].strftime("%Y-%m-%d %H:%M")
                if wf["last_synced"]
                else "Never"
            )

            # Format file exists and backupable columns
            if no_emoji:
                file_exists_icon = "Y" if wf["file_exists"] else "N"
                backupable_icon = "Y" if wf["backupable"] else "N"
            else:
                file_exists_icon = "✓" if wf["file_exists"] else "✗"
                backupable_icon = "✓" if wf["backupable"] else "✗"

            table_obj.add_row(
                wf["id"][:12] + "...",
                wf["name"],
                wf["type"],
                wf["status"],
                file_exists_icon,
                backupable_icon,
                str(wf["node_count"]),
                last_synced,
            )

        console.print(table_obj)


@cli.command()
@click.argument("query")
@click.pass_context
def search(ctx: click.Context, query: str) -> None:
    """🔍 Search workflows by content"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    results = manager.search_workflows(query)

    if not results:
        console.print(f"No workflows found matching: {query}")
        return

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Description", style="dim")

    for wf in results:
        description = (
            (wf.description[:50] + "...")
            if wf.description and len(wf.description) > 50
            else (wf.description or "")
        )
        table.add_row(wf.id[:12] + "...", wf.name, wf.type, description)

    console.print(table)


@cli.command()
@click.argument("workflow_id")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def stats(ctx: click.Context, workflow_id: str, format: str) -> None:
    """📊 Show workflow statistics"""
    manager = WorkflowManager(config=ctx.obj.get("config"))

    try:
        stats = manager.get_workflow_stats(workflow_id)

        if format == "json":
            console.print(JSON(json.dumps(stats, indent=2, default=str)))
        else:
            table = Table(title=f"Workflow Stats: {stats['name']}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            for key, value in stats.items():
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, bool):
                    value = "Yes" if value else "No"

                table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)

    except ValueError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("workflow_id")
@click.argument("name")
@click.argument("file_path")
@click.option(
    "--type", default="main", type=click.Choice(["main", "subflow", "utility"])
)
@click.pass_context
def add(
    ctx: click.Context, workflow_id: str, name: str, file_path: str, type: str
) -> None:
    """➕ Add new workflow to management"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    manager.add_workflow(workflow_id, name, file_path, type)


@cli.command()
@click.argument("workflow_id")
@click.confirmation_option(prompt="Are you sure you want to remove this workflow?")
@click.pass_context
def remove(ctx: click.Context, workflow_id: str) -> None:
    """🗑️  Remove workflow from management"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    manager.remove_workflow(workflow_id)


@cli.command()
@click.argument("workflow_id")
@click.pass_context
def sync(ctx: click.Context, workflow_id: str) -> None:
    """🔄 Sync workflow metadata to database"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    success = manager.sync_to_database(workflow_id)
    if success:
        console.print(f"✅ Synced workflow: {workflow_id}")
    else:
        raise click.ClickException("Failed to sync workflow")


@cli.group()
def db() -> None:
    """🎭 Database management commands"""
    pass


@db.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize n8n-deploy database"""
    n8n_deploy_DB()  # Database is initialized on creation
    no_emoji = ctx.obj.get("no_emoji", False)
    if no_emoji:
        console.print("Database initialized")
    else:
        console.print("✅ Database initialized")


@db.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def status(format: str) -> None:
    """Show database status and statistics"""
    db = n8n_deploy_DB()
    stats = db.get_database_stats()

    if format == "json":
        console.print(JSON(json.dumps(stats.dict(), indent=2, default=str)))
    else:
        table = Table(title="Database Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Database Path", stats.database_path)
        table.add_row("Database Size", f"{stats.database_size:,} bytes")
        table.add_row("Schema Version", str(stats.schema_version))
        table.add_row("Last Updated", stats.last_updated.strftime("%Y-%m-%d %H:%M:%S"))

        console.print(table)

        # Tables statistics
        tables_table = Table(title="Table Statistics")
        tables_table.add_column("Table", style="cyan")
        tables_table.add_column("Records", justify="right", style="green")

        for table_name, count in stats.tables.items():
            tables_table.add_row(table_name.title(), f"{count:,}")

        console.print(tables_table)


@db.command()
def vacuum() -> None:
    """Optimize database storage"""
    db = n8n_deploy_DB()
    db.vacuum()


@db.command()
def compact() -> None:
    """Compact database to optimize storage"""
    db = n8n_deploy_DB()
    db.compact()


@db.command()
@click.argument("backup_path", required=False)
@click.pass_context
def backup(ctx: click.Context, backup_path: Optional[str]) -> None:
    """Create database backup"""
    config = ctx.obj.get("config")

    if not backup_path:
        # Create backup in the proper backups directory with timestamp
        backup_filename = (
            f"n8n_deploy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        if config:
            # Ensure backups directory exists
            config.backups_path.mkdir(parents=True, exist_ok=True)
            backup_path = str(config.backups_path / backup_filename)
        else:
            backup_path = backup_filename

    db = n8n_deploy_DB()
    db.backup(backup_path)


@cli.command("backup-workflows")
@click.option(
    "--backup-dir",
    type=click.Path(),
    help="Directory to store backup (default: ./backups)",
)
@click.pass_context
def backup_workflows(ctx: click.Context, backup_dir: Optional[str]) -> None:
    """📦 Create tar.gz backup of all registered workflows"""
    manager = WorkflowManager(config=ctx.obj.get("config"))

    try:
        backup_dir_path = Path(backup_dir) if backup_dir else None
        metadata = manager.backup_all_workflows(backup_dir_path)

        console.print(f"\n📦 Backup Summary:")
        console.print(f"   📁 File: {metadata['filename']}")
        console.print(f"   📊 Workflows: {metadata['workflow_count']}")
        console.print(f"   💾 Size: {metadata['file_size']:,} bytes")
        console.print(f"   🔍 Hash: {metadata['sha256_hash'][:32]}...")

    except Exception as e:
        raise click.ClickException(f"Backup failed: {e}")


@cli.command("restore-workflows")
@click.argument("backup_file", type=click.Path(exists=True))
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def restore_workflows(ctx: click.Context, backup_file: str, force: bool) -> None:
    """📥 Restore workflows from tar.gz backup"""
    manager = WorkflowManager(config=ctx.obj.get("config"))

    success = manager.restore_workflows_backup(Path(backup_file), force=force)
    if not success:
        raise click.ClickException("Restore failed")


@cli.command("verify-backup")
@click.argument("backup_file", type=click.Path(exists=True))
@click.pass_context
def verify_backup(ctx: click.Context, backup_file: str) -> None:
    """🔍 Verify backup file integrity"""
    manager = WorkflowManager(config=ctx.obj.get("config"))

    is_valid = manager.verify_backup_integrity(Path(backup_file))
    if is_valid:
        console.print("✅ Backup integrity verified")
    else:
        raise click.ClickException("Backup integrity check failed")


@cli.command("list-backups")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list_backups(ctx: click.Context, format: str) -> None:
    """📋 List all available workflow backups"""
    manager = WorkflowManager(config=ctx.obj.get("config"))
    backups = manager.list_backups()

    if format == "json":
        console.print(JSON(json.dumps(backups, indent=2, default=str)))
    else:
        if not backups:
            console.print("No backups found")
            return

        table = Table(title="Workflow Backups")
        table.add_column("Filename", style="cyan")
        table.add_column("Created", style="green")
        table.add_column("Workflows", justify="right")
        table.add_column("Size", justify="right")
        table.add_column("Status", style="yellow")

        for backup in backups:
            # Handle different backup sources (database vs filesystem)
            if backup.get("in_database", True):
                created = backup.get("timestamp", backup.get("stored_at", "Unknown"))
                if isinstance(created, str) and "T" in created:
                    try:
                        created_dt = datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        )
                        created = created_dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        created = created[:16] if len(created) > 16 else created

                workflows = str(backup.get("workflow_count", "?"))
                size = (
                    f"{backup.get('file_size', 0):,}"
                    if backup.get("file_size")
                    else "?"
                )
                status = "Tracked" if backup.get("in_database") else "Untracked"
            else:
                # Filesystem backup not in database
                created = backup.get("modified", datetime.now()).strftime(
                    "%Y-%m-%d %H:%M"
                )
                workflows = "?"
                size = f"{backup.get('file_size', 0):,}"
                status = "Untracked"

            table.add_row(backup["filename"], created, workflows, size, status)

        console.print(table)


# API Key Management Commands
@cli.group()
def apikey() -> None:
    """🔐 API key management commands"""
    pass


@apikey.command("add")
@click.argument("name")
@click.option("--key", prompt=True, hide_input=True, help="API key value")
@click.option("--description", help="Description of the API key")
@click.option("--expires-days", type=int, help="Number of days until expiration")
@click.pass_context
def add_apikey(
    ctx: click.Context,
    name: str,
    key: str,
    description: Optional[str],
    expires_days: Optional[int],
) -> None:
    """🔑 Add a new API key to storage"""
    try:
        api_manager = ApiKeyManager(config=ctx.obj.get("config"))
        key_id = api_manager.add_api_key(
            name=name,
            api_key=key,
            description=description,
            expires_days=expires_days,
        )
        no_emoji = ctx.obj.get("no_emoji", False)

        if no_emoji:
            console.print(f"API key '{name}' added successfully")
            console.print(f"ID: {key_id}")
            if expires_days:
                console.print(f"Expires in: {expires_days} days")
        else:
            console.print(f"✅ API key '{name}' added successfully")
            console.print(f"   ID: {key_id}")
            if expires_days:
                console.print(f"   Expires in: {expires_days} days")
    except Exception as e:
        raise click.ClickException(f"Failed to add API key: {e}")


@apikey.command("list")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list_apikeys(ctx: click.Context, format: str) -> None:
    """📋 List all stored API keys"""
    try:
        api_manager = ApiKeyManager(config=ctx.obj.get("config"))
        keys = api_manager.list_api_keys()

        if format == "json":
            console.print(JSON(json.dumps(keys, indent=2, default=str)))
        else:
            if not keys:
                console.print("No API keys found")
                return

            no_emoji = ctx.obj.get("no_emoji", False)

            # Tables always exclude emojis for better shell compatibility
            table = Table(title="API Keys")

            table.add_column("Name", style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Created", style="blue")
            table.add_column("Last Used", style="yellow")
            table.add_column("Status", style="magenta")
            table.add_column("Description", style="dim")

            for key in keys:
                created = key["created_at"]
                if isinstance(created, str):
                    created = created[:16]  # Truncate datetime

                last_used = key["last_used"]
                if last_used:
                    last_used = (
                        str(last_used)[:16]
                        if isinstance(last_used, str)
                        else str(last_used)[:16]
                    )
                else:
                    last_used = "Never"

                # Tables always use text-only status for better shell compatibility
                status_icons = {
                    "active": "Active",
                    "inactive": "Inactive",
                    "expired": "Expired",
                    "expiring_soon": "Expiring Soon",
                }
                status = status_icons.get(key["status"], key["status"])

                table.add_row(
                    key["name"],
                    key["id"][:8] + "...",
                    str(created),
                    last_used,
                    status,
                    key["description"] or "",
                )

            console.print(table)
    except Exception as e:
        raise click.ClickException(f"Failed to list API keys: {e}")


@apikey.command("get")
@click.argument("key_name_or_id")
@click.option(
    "--show-key", is_flag=True, help="Show the actual API key (use with caution)"
)
@click.pass_context
def get_apikey(ctx: click.Context, key_name_or_id: str, show_key: bool) -> None:
    """🔍 Retrieve an API key"""
    try:
        api_manager = ApiKeyManager(config=ctx.obj.get("config"))
        no_emoji = ctx.obj.get("no_emoji", False)

        if show_key:
            api_key = api_manager.get_api_key(key_name_or_id)
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
        else:
            # Just test if key exists and is valid
            success = api_manager.test_api_key(key_name_or_id)
            if success:
                if no_emoji:
                    console.print(f"API key is valid and accessible: {key_name_or_id}")
                else:
                    console.print(
                        f"✅ API key is valid and accessible: {key_name_or_id}"
                    )
            else:
                if no_emoji:
                    console.print(f"API key not found or invalid: {key_name_or_id}")
                else:
                    console.print(f"❌ API key not found or invalid: {key_name_or_id}")
    except Exception as e:
        raise click.ClickException(f"Failed to retrieve API key: {e}")


@apikey.command("deactivate")
@click.argument("key_name_or_id")
@click.pass_context
def deactivate_apikey(ctx: click.Context, key_name_or_id: str) -> None:
    """🚫 Deactivate an API key (soft delete)"""
    try:
        api_manager = ApiKeyManager(config=ctx.obj.get("config"))
        success = api_manager.deactivate_api_key(key_name_or_id)
        if not success:
            raise click.ClickException("Failed to deactivate API key")
    except Exception as e:
        raise click.ClickException(f"Failed to deactivate API key: {e}")


@apikey.command("delete")
@click.argument("key_name_or_id")
@click.option("--confirm", is_flag=True, help="Confirm permanent deletion")
@click.pass_context
def delete_apikey(ctx: click.Context, key_name_or_id: str, confirm: bool) -> None:
    """🗑️ Permanently delete an API key"""
    try:
        api_manager = ApiKeyManager(config=ctx.obj.get("config"))
        success = api_manager.delete_api_key(key_name_or_id, confirm=confirm)
        if not success:
            raise click.ClickException("Failed to delete API key")
    except Exception as e:
        raise click.ClickException(f"Failed to delete API key: {e}")


@apikey.command("test")
@click.argument("key_name_or_id")
@click.pass_context
def test_apikey(ctx: click.Context, key_name_or_id: str) -> None:
    """🧪 Test API key validity"""
    try:
        api_manager = ApiKeyManager(config=ctx.obj.get("config"))
        success = api_manager.test_api_key(key_name_or_id)
        if not success:
            raise click.ClickException("API key test failed")
    except Exception as e:
        raise click.ClickException(f"Failed to test API key: {e}")


def main() -> None:
    """Main CLI entry point"""
    cli()


if __name__ == "__main__":
    main()
