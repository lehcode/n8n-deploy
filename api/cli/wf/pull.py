#!/usr/bin/env python3
"""Pull workflow command."""

from typing import Optional

import click
from rich.console import Console

from ...config import NOT_PROVIDED, get_config
from ...workflow import WorkflowApi
from ..app import (
    HELP_DB_FILENAME,
    HELP_FLOW_DIR,
    HELP_NO_EMOJI,
    CustomCommand,
    cli_data_dir_help,
)

console = Console()


def _prompt_for_filename(workflow_id: str, no_emoji: bool) -> str:
    """Prompt user for filename for new workflow."""
    default_filename = f"{workflow_id}.json"
    if no_emoji:
        console.print(f"New workflow detected. Enter filename (default: {default_filename}):")
    else:
        console.print(f"New workflow detected. Enter filename (default: [cyan]{default_filename}[/cyan]):")

    target_filename: str = click.prompt("Filename", default=default_filename, show_default=False)

    if target_filename and not target_filename.endswith(".json"):
        target_filename = f"{target_filename}.json"

    return target_filename


@click.command(cls=CustomCommand)
@click.option(
    "--remote",
    metavar="N8N_SERVER_NAME|N8N_SERVER_URL",
    help="n8n server (name or URL) - uses linked API key if name provided",
)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--filename", metavar="FILENAME", help="Custom filename for new workflows (e.g., 'my-workflow.json')")
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="WORKFLOW_ID|WORKFLOW_NAME")
def pull(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    filename: Optional[str],
    no_emoji: bool,
) -> None:
    """📥 Download workflow from n8n server

    Downloads a workflow using its n8n workflow ID (e.g., 'deAVBp391wvomsWY') or workflow name.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (if workflow exists in database)
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    Use --remote to override with server name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.

    For new workflows (not in database), use --filename to specify the local filename.
    If not provided, you will be prompted to enter one.

    Examples:
      n8n-deploy workflow pull workflow-name              # Uses linked server
      n8n-deploy workflow pull workflow-name --remote staging  # Override to staging
      n8n-deploy workflow pull abc123 --filename my-workflow.json  # Custom filename
    """
    try:
        config = get_config(
            base_folder=data_dir,
            flow_folder=flow_dir if flow_dir is not None else NOT_PROVIDED,
            db_filename=db_filename,
        )
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise click.Abort()

    from ..db import check_database_exists

    check_database_exists(config.database_path, output_json=False, no_emoji=no_emoji)

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)

        target_filename = filename
        try:
            manager.get_workflow_info(workflow_id)
        except ValueError:
            # New workflow - prompt for filename if not provided
            if not target_filename:
                target_filename = _prompt_for_filename(workflow_id, no_emoji)

        success = manager.pull_workflow(workflow_id, filename=target_filename)

        if success:
            success_msg = f"Pulled workflow '{workflow_id}' from server"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]{success_msg}[/green]")
        else:
            error_msg = f"Failed to pull workflow '{workflow_id}'"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        error_msg = f"Failed to pull wf: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
