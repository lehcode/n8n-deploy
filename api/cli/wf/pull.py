#!/usr/bin/env python3
"""Pull workflow command."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import click
from rich.console import Console

from ..db import is_interactive_mode
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
class PullResult:
    """Result of a single workflow pull operation."""

    workflow_id: str
    success: bool
    message: str


def _prompt_for_filename(workflow_id: str, no_emoji: bool, non_interactive: bool = False) -> str:
    """Prompt user for filename for new workflow.

    In non-interactive mode, returns default filename without prompting.

    Args:
        workflow_id: The workflow ID (used for default filename)
        no_emoji: Whether to suppress emoji in output
        non_interactive: Force non-interactive mode (suppress prompts)
    """
    default_filename = f"{workflow_id}.json"

    # Non-interactive mode: use default without prompting
    if non_interactive or not is_interactive_mode():
        prefix = "" if no_emoji else "Info: "
        console.print(f"{prefix}Using default filename: {default_filename}")
        return default_filename

    # Interactive mode: prompt user
    if no_emoji:
        console.print(f"New workflow detected. Enter filename (default: {default_filename}):")
    else:
        console.print(f"New workflow detected. Enter filename (default: [cyan]{default_filename}[/cyan]):")

    target_filename: str = click.prompt("Filename", default=default_filename, show_default=False)

    if target_filename and not target_filename.endswith(".json"):
        target_filename = f"{target_filename}.json"

    return target_filename


def _output_pull_summary(results: List[PullResult], no_emoji: bool) -> None:
    """Output summary of multi-workflow pull operation."""
    if len(results) == 1:
        # Single workflow: simple output (backwards compatible)
        r = results[0]
        if r.success:
            msg = f"Pulled workflow '{r.workflow_id}' from server"
            if no_emoji:
                console.print(msg)
            else:
                console.print(f"[green]{msg}[/green]")
        else:
            msg = f"Failed to pull workflow '{r.workflow_id}': {r.message}"
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
        console.print("=== Pull Summary ===")
    else:
        console.print("[bold]=== Pull Summary ===[/bold]")

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
        msg = f"All {success_count} workflow(s) pulled successfully"
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
    "--server",
    "remote",
    metavar="N8N_SERVER_NAME|N8N_SERVER_URL",
    help="n8n server (name or URL) - uses linked API key if name provided",
)
@click.option("--skip-ssl-verify", is_flag=True, help="Skip SSL certificate verification for self-signed certificates")
@click.option("--data-dir", type=click.Path(), help=cli_data_dir_help)
@click.option("--flow-dir", type=click.Path(), help=HELP_FLOW_DIR)
@click.option("--db-filename", type=str, help=HELP_DB_FILENAME)
@click.option(
    "--filename",
    "--output",
    "filename",
    metavar="FILENAME",
    help="Custom filename for new workflows (only for single workflow)",
)
@click.option("--non-interactive", is_flag=True, help="Suppress prompts, use defaults for automation")
@click.option("--no-emoji", is_flag=True, help=HELP_NO_EMOJI)
@click.argument("workflow_ids", metavar="WORKFLOW_ID|WORKFLOW_NAME", nargs=-1, required=True)
def pull(
    workflow_ids: Tuple[str, ...],
    remote: Optional[str],
    skip_ssl_verify: bool,
    data_dir: Optional[str],
    flow_dir: Optional[str],
    db_filename: Optional[str],
    filename: Optional[str],
    non_interactive: bool,
    no_emoji: bool,
) -> None:
    """Download one or more workflows from n8n server

    Downloads workflows using their n8n workflow ID (e.g., 'deAVBp391wvomsWY')
    or workflow name. Multiple workflows can be specified, separated by spaces.

    Server Resolution Priority (lowest to highest):
    1. Workflow's linked server (if workflow exists in database)
    2. N8N_SERVER_URL environment variable
    3. --remote option (overrides all)

    Use --remote to override with server name (e.g., 'production') or URL.
    If server name is used, the linked API key will be used automatically.

    For new workflows (not in database), use --filename to specify the local filename.
    Note: --filename only works with a single workflow. For multiple workflows,
    default filenames ({workflow_id}.json) are used.

    Exit Codes:
      0 - All workflows pulled successfully
      1 - One or more workflows failed

    Examples:
      n8n-deploy wf pull workflow-name                    # Single workflow
      n8n-deploy wf pull wf1 wf2 wf3                     # Multiple workflows
      n8n-deploy wf pull wf1 wf2 --remote staging        # All from same server
      n8n-deploy wf pull abc123 --filename my-wf.json    # Custom filename (single only)
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

    # Warn if --filename provided with multiple workflows
    if filename and len(workflow_ids) > 1:
        if no_emoji:
            console.print("Warning: --filename ignored when pulling multiple workflows")
        else:
            console.print("[yellow]Warning: --filename ignored when pulling multiple workflows[/yellow]")
        filename = None

    try:
        # Initialize manager once (shares remote/ssl config for all pulls)
        manager = WorkflowApi(config=config, skip_ssl_verify=skip_ssl_verify, remote=remote)

        # Track results
        results: List[PullResult] = []
        total = len(workflow_ids)

        # For multiple workflows, force non-interactive mode
        effective_non_interactive = non_interactive or total > 1

        # Process each workflow
        for idx, workflow_id in enumerate(workflow_ids, 1):
            # Progress indicator for multiple workflows
            if total > 1:
                if no_emoji:
                    console.print(f"\n[{idx}/{total}] Processing: {workflow_id}")
                else:
                    console.print(f"\n[cyan][{idx}/{total}][/cyan] Processing: {workflow_id}")

            try:
                target_filename = filename if total == 1 else None

                # Check if workflow exists in database
                try:
                    manager.get_workflow_info(workflow_id)
                except ValueError:
                    # New workflow - prompt for filename if not provided (single workflow only)
                    if not target_filename:
                        target_filename = _prompt_for_filename(workflow_id, no_emoji, effective_non_interactive)

                success = manager.pull_workflow(workflow_id, filename=target_filename)

                if success:
                    results.append(PullResult(workflow_id=workflow_id, success=True, message="Pulled successfully"))
                else:
                    results.append(PullResult(workflow_id=workflow_id, success=False, message="Pull failed"))
            except Exception as e:
                results.append(PullResult(workflow_id=workflow_id, success=False, message=str(e)))

        # Output summary
        _output_pull_summary(results, no_emoji)

        # Exit code: non-zero if any failed
        failed_count = sum(1 for r in results if not r.success)
        if failed_count > 0:
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        error_msg = f"Failed to pull workflow: {e}"
        if no_emoji:
            console.print(error_msg)
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise click.Abort()
