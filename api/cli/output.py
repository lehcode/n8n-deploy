#!/usr/bin/env python3
"""
CLI Output Formatting Utilities

Centralizes emoji handling and output formatting to eliminate duplicate code
across CLI commands. Provides consistent user experience with emoji/no-emoji modes.
"""

from typing import Any, Dict, List

import click
from rich.console import Console
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
    table.add_column("n8n ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("File Path", style="blue")
    table.add_column("File Exists", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Created", justify="center")
    table.add_column("Last Synced", justify="center")
    table.add_column("Push", justify="right")
    table.add_column("Pull", justify="right")

    for wf in workflows:
        # Construct full file path from flow_folder and workflow ID
        flow_folder = wf.get("flow_folder", "")
        file_path = f"{flow_folder}/{wf['id']}.json" if flow_folder else f"{wf['id']}.json"

        # File existence indicator with color
        file_exists = wf.get("file_exists", False)
        if no_emoji:
            file_status = "Yes" if file_exists else "No"
        else:
            file_status = "[green]✓[/green]" if file_exists else "[red]✗[/red]"

        table.add_row(
            wf["id"],
            wf["name"],
            file_path,
            file_status,
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


def format_server_table(servers: List[Dict[str, Any]], no_emoji: bool = False) -> None:
    """
    Format and display servers in a table

    Args:
        servers: List of server dicts
        no_emoji: If True, disable emoji in output
    """
    table = Table(title="n8n Servers" if not no_emoji else None)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URL", style="magenta")
    table.add_column("Description", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Last Used", style="yellow")
    table.add_column("Created", style="green")

    for server in servers:
        status = server.get("is_active", True)
        if no_emoji:
            status_str = "Active" if status else "Inactive"
        else:
            status_str = "[green]✓[/green]" if status else "[red]✗[/red]"

        last_used = server.get("last_used")
        if last_used:
            last_used_str = str(last_used)[:16] if isinstance(last_used, str) else str(last_used)[:16]
        else:
            last_used_str = "Never"

        table.add_row(
            server["name"],
            server["url"],
            server.get("description") or "",
            status_str,
            last_used_str,
            str(server.get("created_at", ""))[:16],
        )

    console.print(table)


# JSON-aware output helpers


def output_result(
    result: Dict[str, Any],
    success_msg: str,
    output_json: bool = False,
    no_emoji: bool = False,
    emoji: str = "✅",
) -> None:
    """Output result in JSON or text format

    Consolidates the common pattern of checking output_json/no_emoji flags.

    Args:
        result: Dict to output as JSON
        success_msg: Message to show in text mode
        output_json: If True, output JSON format
        no_emoji: If True, omit emoji in text mode
        emoji: Emoji to use in text mode (default: checkmark)
    """
    if output_json:
        from rich.json import JSON

        console.print(JSON.from_data(result))
    elif no_emoji:
        console.print(success_msg)
    else:
        console.print(f"{emoji} {success_msg}")


def output_success(
    result: Dict[str, Any],
    success_msg: str,
    output_json: bool = False,
    no_emoji: bool = False,
) -> None:
    """Output success result in JSON or text format

    Wrapper for output_result with green styling.

    Args:
        result: Dict to output as JSON
        success_msg: Message to show in text mode
        output_json: If True, output JSON format
        no_emoji: If True, omit emoji in text mode
    """
    if output_json:
        from rich.json import JSON

        console.print(JSON.from_data(result))
    elif no_emoji:
        console.print(success_msg)
    else:
        console.print(f"[green]✅ {success_msg}[/green]")


def output_error_result(
    error_msg: str,
    output_json: bool = False,
    no_emoji: bool = False,
    abort: bool = False,
) -> None:
    """Output error in JSON or text format

    Consolidates error output handling with optional CLI abort.

    Args:
        error_msg: Error message
        output_json: If True, output JSON format
        no_emoji: If True, omit emoji in text mode
        abort: If True, raise click.Abort after output

    Raises:
        click.Abort: If abort=True
    """
    if output_json:
        from rich.json import JSON

        console.print(JSON.from_data({"success": False, "error": error_msg}))
    elif no_emoji:
        console.print(f"ERROR: {error_msg}")
    else:
        console.print(f"[red]❌ {error_msg}[/red]")

    if abort:
        raise click.Abort()


def output_warning_result(
    warning_msg: str,
    output_json: bool = False,
    no_emoji: bool = False,
) -> None:
    """Output warning in text format (no JSON for warnings)

    Args:
        warning_msg: Warning message
        output_json: If True, skip output (warnings not shown in JSON mode)
        no_emoji: If True, omit emoji in text mode
    """
    if output_json:
        return  # Warnings typically not shown in JSON mode
    elif no_emoji:
        console.print(f"WARNING: {warning_msg}")
    else:
        console.print(f"[yellow]⚠️  {warning_msg}[/yellow]")
