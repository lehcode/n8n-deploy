#!/usr/bin/env python3
"""Stats workflow command."""

from typing import Optional

import click
from rich.console import Console
from rich.json import JSON
from rich.table import Table

from ...config import NOT_PROVIDED, get_config
from ...workflow import WorkflowApi
from ..app import (
    HELP_DB_FILENAME,
    HELP_FLOW_DIR,
    HELP_JSON,
    HELP_NO_EMOJI,
    HELP_TABLE,
    CustomCommand,
    cli_data_dir_help,
)

console = Console()


def _print_individual_stats(stats_data: dict[str, object]) -> None:
    """Print stats for a single workflow."""
    table = Table()
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in stats_data.items():
        table.add_row(key, str(value) if value is not None else "-")

    console.print(table)


def _print_overall_stats(stats_data: dict[str, object]) -> None:
    """Print overall workflow statistics."""
    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="magenta")

    table.add_row("Total Workflows", str(stats_data["total_workflows"]))
    table.add_row("Total Push Operations", str(stats_data["total_push_operations"]))
    table.add_row("Total Pull Operations", str(stats_data["total_pull_operations"]))

    console.print(table)


@click.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", required=False, metavar="wf-id")
def stats(
    workflow_id: Optional[str],
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """📊 Show workflow statistics

    Shows overall workflow statistics if no workflow-id is provided,
    or detailed statistics for a specific workflow if workflow-id is given.

    The workflow-id should be the actual n8n workflow ID (e.g., 'deAVBp391wvomsWY'),
    not the user-friendly name assigned in n8n-deploy.
    """
    if output_json:
        no_emoji = True

    try:
        config = get_config(
            base_folder=data_dir,
            flow_folder=flow_dir if flow_dir is not None else NOT_PROVIDED,
            db_filename=db_filename,
        )
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    try:
        manager = WorkflowApi(config=config)
        stats_data = manager.get_workflow_stats(workflow_id)

        if output_json:
            console.print(JSON.from_data(stats_data))
        elif workflow_id:
            _print_individual_stats(stats_data)
        else:
            _print_overall_stats(stats_data)

    except Exception as e:
        error_msg = f"Failed to get stats: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
