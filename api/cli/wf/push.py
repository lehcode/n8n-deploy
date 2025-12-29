#!/usr/bin/env python3
"""Push workflow command."""

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
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_id", metavar="WORKFLOW_ID|WORKFLOW_NAME")
def push(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
) -> None:
    """📤 Upload workflow to n8n server

    Uploads a workflow using its n8n workflow ID (e.g., 'deAVBp391wvomsWY') or workflow name.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (set via 'wf add --link-remote')
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    Use --remote to override with server name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.

    Examples:
      n8n-deploy workflow push workflow-name              # Uses linked server
      n8n-deploy workflow push workflow-name --remote staging  # Override to staging
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

    try:
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)
        success = manager.push_workflow(workflow_id)

        if success:
            success_msg = f"Pushed workflow '{workflow_id}' to server"
            if no_emoji:
                console.print(success_msg)
            else:
                console.print(f"[green]{success_msg}[/green]")
        else:
            error_msg = f"Failed to push workflow '{workflow_id}'"
            if no_emoji:
                console.print(error_msg)
            else:
                console.print(f"[red]{error_msg}[/red]")
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        error_msg = f"Failed to push workflow: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
