#!/usr/bin/env python3
"""Delete workflow command."""

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


def _confirm_deletion(workflow_name: str, actual_id: str, is_draft: bool, no_emoji: bool) -> bool:
    """Show confirmation prompt for workflow deletion."""
    if is_draft:
        prompt_msg = f"Remove draft workflow '{workflow_name}' ({actual_id}) from database?"
    else:
        prompt_msg = f"Delete workflow '{workflow_name}' ({actual_id}) from server and database?"

    if no_emoji:
        return click.confirm(prompt_msg)
    return click.confirm(f"{prompt_msg}")


def _output_success(workflow_name: str, is_draft: bool, no_emoji: bool) -> None:
    """Output success message after deletion."""
    if is_draft:
        success_msg = f"Removed draft workflow '{workflow_name}' from database"
    else:
        success_msg = f"Deleted workflow '{workflow_name}' from server and database"

    if no_emoji:
        console.print(success_msg)
    else:
        console.print(f"[green]{success_msg}[/green]")


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
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.argument("workflow_id", metavar="WF_ID|WF_NAME|FILENAME")
def delete(
    workflow_id: str,
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
    yes: bool,
) -> None:
    """🗑️ Delete workflow from n8n server and database

    Deletes a workflow using its n8n workflow ID (e.g., 'deAVBp391wvomsWY'),
    workflow name, or filename. The workflow is deleted from the remote server
    first, then removed from the local database. The JSON file is NOT deleted.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (set via 'wf add --link-remote')
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    \b
    Examples:
      n8n-deploy wf delete workflow-name              # Uses linked server
      n8n-deploy wf delete workflow-name --remote staging  # Override to staging
      n8n-deploy wf delete deAVBp391wvomsWY --yes    # Skip confirmation
      n8n-deploy wf delete my-workflow.json          # Delete by filename
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

        # Get workflow info for confirmation
        try:
            workflow_info = manager.get_workflow_info(workflow_id)
            workflow_name = workflow_info.get("name", workflow_id)
            actual_id = workflow_info["wf"].id
        except Exception:
            workflow_name = workflow_id
            actual_id = workflow_id

        is_draft = actual_id.startswith("draft_")

        # Confirmation
        if not yes and not _confirm_deletion(workflow_name, actual_id, is_draft, no_emoji):
            if no_emoji:
                console.print("Operation cancelled")
            else:
                console.print("[yellow]Operation cancelled[/yellow]")
            return

        # Delete from server first (unless draft)
        if not is_draft:
            success = manager.delete_n8n_workflow(actual_id)
            if not success:
                error_msg = "Failed to delete workflow from server"
                if no_emoji:
                    console.print(error_msg)
                else:
                    console.print(f"[red]{error_msg}[/red]")
                raise click.Abort()

        # Remove from database
        manager.remove_workflow(actual_id)
        _output_success(workflow_name, is_draft, no_emoji)

    except click.Abort:
        raise
    except Exception as e:
        error_msg = f"Failed to delete workflow: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
