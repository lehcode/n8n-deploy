#!/usr/bin/env python3
"""Search workflow command."""

from typing import Optional

import click
from rich.console import Console
from rich.json import JSON

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
from ..output import print_workflow_search_table

console = Console()


@click.command(cls=CustomCommand)
@click.argument("query")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--table", "output_table", is_flag=True, help=HELP_TABLE)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def search(
    query: str,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    output_json: bool,
    output_table: bool,
    no_emoji: bool,
) -> None:
    """🔍 Search workflows by name or workflow ID

    Searches both:
    - User-friendly names assigned in n8n-deploy (e.g., 'signup-flow')
    - n8n workflow IDs (e.g., 'deAVBp391wvomsWY' or partial matches)

    Results are ordered by relevance: exact matches first, then partial matches.
    Use exact n8n workflow IDs for direct operations like pull/push/delete.
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
        workflows = manager.search_workflows(query)

        if output_json:
            console.print(JSON.from_data(workflows))
        else:
            print_workflow_search_table(workflows, no_emoji, query)

    except Exception as e:
        error_msg = f"Failed to search workflows: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
