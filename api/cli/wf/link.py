#!/usr/bin/env python3
"""Link workflow command."""

from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.json import JSON

from ...config import NOT_PROVIDED, get_config
from ...models import Workflow
from ...workflow import WorkflowApi
from ..app import (
    HELP_DB_FILENAME,
    HELP_JSON,
    HELP_NO_EMOJI,
    CustomCommand,
    cli_data_dir_help,
)
from ..output import cli_error
from .common import resolve_server_for_linking

console = Console()


def _find_workflow(manager: WorkflowApi, workflow_id: str, output_json: bool, no_emoji: bool) -> Optional[Workflow]:
    """Find workflow by ID or name."""
    workflow_obj = manager.db.get_workflow(workflow_id)
    if not workflow_obj:
        workflows = manager.db.search_workflows(workflow_id)
        if len(workflows) == 1:
            return workflows[0]
        elif len(workflows) > 1:
            error_msg = f"Multiple workflows match '{workflow_id}'. Use the full workflow ID."
            if output_json:
                console.print(JSON.from_data({"success": False, "error": error_msg}))
            else:
                cli_error(error_msg, no_emoji)
            raise click.Abort()
    return workflow_obj


def _output_success(workflow_obj: Workflow, updated_fields: List[str], output_json: bool, no_emoji: bool) -> None:
    """Output success message for link command."""
    result = {
        "success": True,
        "workflow_id": workflow_obj.id,
        "workflow_name": workflow_obj.name,
        "updated": updated_fields,
    }

    if output_json:
        console.print(JSON.from_data(result))
    elif no_emoji:
        console.print(f"Updated workflow '{workflow_obj.name}': {', '.join(updated_fields)}")
    else:
        console.print(f"Updated workflow '{workflow_obj.name}': {', '.join(updated_fields)}")


@click.command(cls=CustomCommand)
@click.argument("workflow_id")
@click.option("--flow-dir", type=click.Path(), help="Update workflow's flow directory")
@click.option("--server", "server_name", help="Link workflow to server (by name)")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def link(
    workflow_id: str,
    flow_dir: Optional[str],
    server_name: Optional[str],
    data_dir: Optional[str],
    db_filename: Optional[str],
    output_json: bool,
    no_emoji: bool,
) -> None:
    """🔗 Update workflow metadata (flow-dir, server)

    Updates stored metadata for a workflow without performing push/pull.
    Use this to configure where a workflow's files are located or which
    server it should sync with.

    \b
    Examples:
      n8n-deploy wf link my-workflow --flow-dir ./workflows
      n8n-deploy wf link my-workflow --server production
      n8n-deploy wf link my-workflow --flow-dir ./workflows --server production
    """
    if output_json:
        no_emoji = True

    try:
        config = get_config(
            base_folder=data_dir,
            flow_folder=NOT_PROVIDED,
            db_filename=db_filename,
        )
    except ValueError as e:
        cli_error(str(e), no_emoji)
        raise click.Abort()

    from ..db import check_database_exists

    check_database_exists(config.database_path, output_json=output_json, no_emoji=no_emoji)

    try:
        manager = WorkflowApi(config=config)
        workflow_obj = _find_workflow(manager, workflow_id, output_json, no_emoji)

        if not workflow_obj:
            error_msg = f"Workflow '{workflow_id}' not found in database"
            if output_json:
                console.print(JSON.from_data({"success": False, "error": error_msg}))
            else:
                cli_error(error_msg, no_emoji)
            raise click.Abort()

        updated_fields: List[str] = []

        # Update flow_dir
        if flow_dir is not None:
            resolved_path = str(Path(flow_dir).resolve())
            workflow_obj.file_folder = resolved_path
            updated_fields.append(f"flow-dir={resolved_path}")

        # Update server linkage
        if server_name is not None:
            server_name_resolved, server_id = resolve_server_for_linking(config, server_name, output_json, no_emoji)
            workflow_obj.server_id = server_id
            updated_fields.append(f"server={server_name_resolved}")

        if not updated_fields:
            warning_msg = "No updates specified. Use --flow-dir or --server"
            if output_json:
                console.print(JSON.from_data({"success": False, "error": warning_msg}))
            else:
                if no_emoji:
                    console.print(warning_msg)
                else:
                    console.print(f"[yellow]{warning_msg}[/yellow]")
            return

        manager.db.update_workflow(workflow_obj)
        _output_success(workflow_obj, updated_fields, output_json, no_emoji)

    except click.Abort:
        raise
    except Exception as e:
        error_msg = f"Failed to update workflow: {e}"
        if output_json:
            console.print(JSON.from_data({"success": False, "error": error_msg}))
        else:
            cli_error(error_msg, no_emoji)
        raise click.Abort()
