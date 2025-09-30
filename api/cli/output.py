#!/usr/bin/env python3
"""
CLI Output Formatting Utilities

Centralizes emoji handling and output formatting to eliminate duplicate code
across CLI commands. Provides consistent user experience with emoji/no-emoji modes.
"""

from typing import Any, Callable, Dict, List, Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

console = Console()


def format_message(msg: str, emoji: str = "", no_emoji: bool = False) -> str:
    """Format message with optional emoji prefix

    Args:
        msg: The message text
        emoji: Emoji character to prepend (if no_emoji is False)
        no_emoji: If True, omit the emoji prefix

    Returns:
        Formatted message string
    """
    prefix = "" if no_emoji else f"{emoji} "
    return f"{prefix}{msg}"


def print_success(msg: str, no_emoji: bool = False) -> None:
    """Print success message in green

    Args:
        msg: Success message to display
        no_emoji: If True, omit emoji prefix
    """
    console.print(f"[green]{format_message(msg, '✅', no_emoji)}[/green]")


def print_error(msg: str, no_emoji: bool = False) -> None:
    """Print error message in red

    Args:
        msg: Error message to display
        no_emoji: If True, omit emoji prefix
    """
    console.print(f"[red]{format_message(msg, '❌', no_emoji)}[/red]")


def print_warning(msg: str, no_emoji: bool = False) -> None:
    """Print warning message in yellow

    Args:
        msg: Warning message to display
        no_emoji: If True, omit emoji prefix
    """
    console.print(f"[yellow]{format_message(msg, '⚠️', no_emoji)}[/yellow]")


def print_info(msg: str, no_emoji: bool = False) -> None:
    """Print info message

    Args:
        msg: Info message to display
        no_emoji: If True, omit emoji prefix
    """
    console.print(format_message(msg, "ℹ️", no_emoji))


def cli_error(msg: str, no_emoji: bool = False) -> None:
    """Print error message and abort CLI execution

    Args:
        msg: Error message to display
        no_emoji: If True, omit emoji prefix

    Raises:
        click.Abort: Always raises to terminate CLI
    """
    print_error(msg, no_emoji)
    raise click.Abort()


def cli_confirm(prompt: str, default: bool = False, no_emoji: bool = False) -> bool:
    """Prompt user for confirmation

    Args:
        prompt: Question to ask user
        default: Default value if user just presses enter
        no_emoji: If True, omit emoji prefix

    Returns:
        True if user confirmed, False otherwise
    """
    formatted_prompt = format_message(prompt, "❓", no_emoji)
    return click.confirm(formatted_prompt, default=default)


class OutputFormatter:
    """Context-aware output formatter for CLI commands

    Stores no_emoji preference to avoid passing it to every call.

    Example:
        >>> fmt = OutputFormatter(no_emoji=True)
        >>> fmt.success("Operation completed")
        >>> fmt.error("Something went wrong")
    """

    def __init__(self, no_emoji: bool = False):
        """Initialize formatter with emoji preference

        Args:
            no_emoji: If True, all output will omit emojis
        """
        self.no_emoji = no_emoji

    def format(self, msg: str, emoji: str = "") -> str:
        """Format message with optional emoji

        Args:
            msg: Message text
            emoji: Emoji character to prepend

        Returns:
            Formatted message string
        """
        return format_message(msg, emoji, self.no_emoji)

    def success(self, msg: str) -> None:
        """Print success message"""
        print_success(msg, self.no_emoji)

    def error(self, msg: str) -> None:
        """Print error message"""
        print_error(msg, self.no_emoji)

    def warning(self, msg: str) -> None:
        """Print warning message"""
        print_warning(msg, self.no_emoji)

    def info(self, msg: str) -> None:
        """Print info message"""
        print_info(msg, self.no_emoji)

    def abort(self, msg: str) -> None:
        """Print error and abort CLI

        Raises:
            click.Abort: Always raises
        """
        cli_error(msg, self.no_emoji)

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """Prompt user for confirmation

        Args:
            prompt: Question to ask
            default: Default value

        Returns:
            True if confirmed, False otherwise
        """
        return cli_confirm(prompt, default, self.no_emoji)


# Table formatting helpers


def print_workflow_table(workflows: List[Dict[str, Any]], no_emoji: bool = False) -> None:
    """Print workflows in a formatted table

    Args:
        workflows: List of workflow dictionaries
        no_emoji: If True, shows plain message when no workflows found
    """
    if not workflows:
        msg = "No workflows found"
        if no_emoji:
            console.print(msg)
        else:
            console.print(f"[yellow]{msg}[/yellow]")
        return

    table = Table()
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Created", justify="center")
    table.add_column("Last Synced", justify="center")
    table.add_column("Push Count", justify="right")
    table.add_column("Pull Count", justify="right")

    for wf in workflows:
        table.add_row(
            wf["id"],
            wf["name"],
            str(wf["status"]),
            str(wf["created_at"])[:10] if wf["created_at"] else "-",
            str(wf["last_synced"])[:10] if wf["last_synced"] else "-",
            str(wf["push_count"] or 0),
            str(wf["pull_count"] or 0),
        )

    console.print(table)


def print_workflow_search_table(workflows: List[Any], no_emoji: bool = False, query: str = "") -> None:
    """Print workflow search results in a formatted table

    Args:
        workflows: List of Workflow objects
        no_emoji: If True, shows plain message when no workflows found
        query: The search query (for display in no-results message)
    """
    if not workflows:
        msg = f"No workflows found matching '{query}'" if query else "No workflows found"
        if no_emoji:
            console.print(msg)
        else:
            console.print(f"[yellow]{msg}[/yellow]")
        return

    table = Table()
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Created", justify="center")

    for wf in workflows:
        table.add_row(
            wf.id,
            wf.name,
            str(wf.status),
            str(wf.created_at)[:10] if wf.created_at else "-",
        )

    console.print(table)


def print_backup_table(backups: List[Dict[str, Any]], no_emoji: bool = False) -> None:
    """Print backups in a formatted table (database records)

    Args:
        backups: List of backup dictionaries from database
        no_emoji: If True, shows plain message when no backups found
    """
    if not backups:
        msg = "No backups found"
        if no_emoji:
            console.print(msg)
        else:
            console.print(f"[yellow]{msg}[/yellow]")
        return

    table = Table()
    table.add_column("Backup ID", style="cyan", no_wrap=False)
    table.add_column("Filename", style="magenta")
    table.add_column("Workflow Count", justify="right")
    table.add_column("Created", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Validated", justify="center")

    for backup in backups:
        # Format file size
        size = backup.get("file_size", 0)
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"

        # Format timestamp
        timestamp = backup.get("timestamp", "")
        if timestamp:
            # Extract date from ISO format
            timestamp_display = str(timestamp)[:10]
        else:
            timestamp_display = "-"

        # Validation status
        validated = "✓" if backup.get("api_validated") else "-"

        table.add_row(
            str(backup.get("backup_id", ""))[:12] + "...",  # Truncate UUID
            backup.get("filename", "-"),
            str(backup.get("workflow_count", 0)),
            timestamp_display,
            size_str,
            validated,
        )

    console.print(table)


def print_backup_files_table(backup_files: List[Any], no_emoji: bool = False, backup_path: str = "") -> None:
    """Print backup files from filesystem in a formatted table

    Args:
        backup_files: List of Path objects for backup files
        no_emoji: If True, shows plain message when no backups found
        backup_path: Directory path for display
    """
    if not backup_files:
        msg = f"No backup files found in {backup_path}" if backup_path else "No backup files found"
        if no_emoji:
            console.print(msg)
        else:
            console.print(f"[yellow]{msg}[/yellow]")
        return

    from datetime import datetime

    table = Table()
    table.add_column("Backup File", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Modified", justify="center")

    for backup_file in sorted(backup_files):
        stat = backup_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        modified_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

        table.add_row(
            backup_file.name,
            f"{size_mb:.1f} MB",
            modified_str,
        )

    if backup_path:
        console.print(f"\nBackup directory: {backup_path}")
    console.print(table)


def output_json_or_table(
    data: List[Any],
    format: str,
    no_emoji: bool,
    table_func: Callable[..., None],
    query: str = "",
) -> None:
    """Output data as JSON or formatted table

    Args:
        data: Data to output (list of dicts or objects)
        format: Output format ("json" or "table")
        no_emoji: Whether to suppress emojis
        table_func: Function to call for table formatting
        query: Optional query string for search results
    """
    if format == "json":
        # Convert objects to dictionaries if needed
        if data and hasattr(data[0], "__dict__"):
            json_data = []
            for item in data:
                if hasattr(item, "id"):
                    # Workflow object
                    json_data.append(
                        {
                            "id": item.id,
                            "name": item.name,
                            "status": str(item.status),
                            "created_at": str(item.created_at) if item.created_at else None,
                            "last_synced": str(item.last_synced) if item.last_synced else None,
                        }
                    )
                else:
                    json_data.append(item.__dict__)
            console.print(JSON.from_data(json_data))
        else:
            console.print(JSON.from_data(data))
    else:
        if query:
            table_func(data, no_emoji, query)
        else:
            table_func(data, no_emoji)
