#!/usr/bin/env python3
"""Add workflow command."""

from typing import Optional

import click
from rich.console import Console

from ...config import NOT_PROVIDED, get_config
from ...workflow import WorkflowApi
from ..app import (
    HELP_DB_FILENAME,
    HELP_FLOW_DIR,
    HELP_JSON,
    HELP_NO_EMOJI,
    CustomCommand,
    cli_data_dir_help,
)
from ..output import cli_error
from .common import (
    ensure_workflow_id,
    link_workflow_to_server,
    output_add_success,
    read_workflow_file,
    resolve_server_for_linking,
)

console = Console()


@click.command(cls=CustomCommand)
@click.argument("workflow_file")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option("--link-remote", help="Link workflow to n8n server (server name or URL)")
@click.option("--json", "output_json", is_flag=True, help=HELP_JSON)
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
def add(
    workflow_file: str,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    link_remote: Optional[str],
    output_json: bool,
    no_emoji: bool,
) -> None:
    """➕ Register local workflow JSON file to database

    Adds a workflow from a local JSON file to the database. The workflow file
    should be in the flow directory. Optionally link to a remote n8n server.

    \b
    Examples:
      n8n-deploy wf add deAVBp391wvomsWY.json
      n8n-deploy wf add workflow.json --link-remote production
      n8n-deploy wf add workflow.json --link-remote https://n8n.example.com
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
        cli_error(str(e), no_emoji)
        raise click.Abort()

    from ..db import check_database_exists

    check_database_exists(config.database_path, output_json=output_json, no_emoji=no_emoji)

    try:
        result = read_workflow_file(config, workflow_file, output_json, no_emoji)
        if result is None:
            return
        _, workflow_data = result

        workflow_id, workflow_name = ensure_workflow_id(workflow_data, workflow_file, output_json, no_emoji)

        manager = WorkflowApi(config=config)
        manager.add_workflow(workflow_id, workflow_name, filename=workflow_file)

        output_add_success(workflow_id, workflow_name, output_json, no_emoji)

        if link_remote:
            server_name, server_id = resolve_server_for_linking(config, link_remote, output_json, no_emoji)
            link_workflow_to_server(manager, workflow_id, server_id, server_name, output_json, no_emoji)

    except click.Abort:
        raise
    except Exception as e:
        if output_json:
            from rich.json import JSON

            console.print(JSON.from_data({"success": False, "error": str(e)}))
        else:
            cli_error(f"Failed to add workflow: {e}", no_emoji)
