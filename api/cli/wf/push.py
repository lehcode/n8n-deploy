#!/usr/bin/env python3
"""Push workflow command."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

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


@dataclass
class PushResult:
    """Result of a single workflow push operation."""

    workflow_id: str
    success: bool
    message: str


def _output_push_summary(results: List[PushResult], no_emoji: bool) -> None:
    """Output summary of multi-workflow push operation."""
    if len(results) == 1:
        # Single workflow: simple output (backwards compatible)
        r = results[0]
        if r.success:
            msg = f"Pushed workflow '{r.workflow_id}' to server"
            if no_emoji:
                console.print(msg)
            else:
                console.print(f"[green]{msg}[/green]")
        else:
            msg = f"Failed to push workflow '{r.workflow_id}': {r.message}"
            if no_emoji:
                console.print(msg)
            else:
                console.print(f"[red]{msg}[/red]")
        return

    # Multiple workflows: summary table
    success_count = sum(1 for r in results if r.success)
    failed_count = len(results) - success_count

    console.print("")  # Blank line before summary

    if no_emoji:
        console.print("=== Push Summary ===")
    else:
        console.print("[bold]=== Push Summary ===[/bold]")

    for r in results:
        if r.success:
            if no_emoji:
                console.print(f"  [OK]   {r.workflow_id}")
            else:
                console.print(f"  [green]OK[/green]   {r.workflow_id}")
        else:
            if no_emoji:
                console.print(f"  [FAIL] {r.workflow_id}: {r.message}")
            else:
                console.print(f"  [red]FAIL[/red] {r.workflow_id}: {r.message}")

    console.print("")

    # Final status line
    if failed_count == 0:
        msg = f"All {success_count} workflow(s) pushed successfully"
        if no_emoji:
            console.print(msg)
        else:
            console.print(f"[green]{msg}[/green]")
    elif success_count == 0:
        msg = f"All {failed_count} workflow(s) failed"
        if no_emoji:
            console.print(msg)
        else:
            console.print(f"[red]{msg}[/red]")
    else:
        msg = f"{success_count} succeeded, {failed_count} failed"
        if no_emoji:
            console.print(msg)
        else:
            console.print(f"[yellow]{msg}[/yellow]")


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
@click.argument("workflow_ids", metavar="WORKFLOW_ID|WORKFLOW_NAME", nargs=-1, required=True)
def push(
    workflow_ids: Tuple[str, ...],
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    no_emoji: bool,
) -> None:
    """Upload one or more workflows to n8n server

    Uploads workflows using their n8n workflow ID (e.g., 'deAVBp391wvomsWY')
    or workflow name. Multiple workflows can be specified, separated by spaces.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (set via 'wf add --link-remote')
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    Use --remote to override with server name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.

    Exit Codes:
      0 - All workflows pushed successfully
      1 - One or more workflows failed

    Examples:
      n8n-deploy wf push workflow-name                    # Single workflow
      n8n-deploy wf push wf1 wf2 wf3                     # Multiple workflows
      n8n-deploy wf push wf1 wf2 --remote staging        # All to same server
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
        # Initialize manager once (shares remote/ssl config for all pushes)
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)

        # Track results
        results: List[PushResult] = []
        total = len(workflow_ids)

        # Process each workflow
        for idx, workflow_id in enumerate(workflow_ids, 1):
            # Progress indicator for multiple workflows
            if total > 1:
                if no_emoji:
                    console.print(f"\n[{idx}/{total}] Processing: {workflow_id}")
                else:
                    console.print(f"\n[cyan][{idx}/{total}][/cyan] Processing: {workflow_id}")

            try:
                success = manager.push_workflow(workflow_id)

                if success:
                    results.append(PushResult(workflow_id=workflow_id, success=True, message="Pushed successfully"))
                else:
                    results.append(PushResult(workflow_id=workflow_id, success=False, message="Push failed"))
            except Exception as e:
                results.append(PushResult(workflow_id=workflow_id, success=False, message=str(e)))

        # Output summary
        _output_push_summary(results, no_emoji)

        # Exit code: non-zero if any failed
        failed_count = sum(1 for r in results if not r.success)
        if failed_count > 0:
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
