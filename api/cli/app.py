#!/usr/bin/env python3
"""
Main CLI entry point for n8n-deploy

Handles CLI initialization, version/help commands, and basic CLI infrastructure.
"""

from typing import Any, List, Optional

import click
from rich.console import Console

from .verbose import set_verbose

console = Console()

# Program name constant for consistent CLI help messages
PROG_NAME = "n8n-deploy"

# Common CLI option help texts
cli_data_dir_help = "Data directory for database and backups"
HELP_FLOW_DIR = "Plain directory where workflow JSON files are located"
HELP_DB_FILENAME = "Database filename (default: n8n-deploy.db)"
HELP_SERVER_URL = "n8n server URL (overrides N8N_SERVER_URL)"
HELP_NO_EMOJI = "Disable emoji output for automation/scripting"
HELP_JSON = "Output in JSON format for scripting/automation"
HELP_FORMAT = "Output format"  # Deprecated - use HELP_JSON/HELP_TABLE
HELP_TABLE = "Output in table format (default for interactive use)"


class CustomCommand(click.Command):
    """Custom Click Command that shows consistent usage format"""

    def format_usage(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Override format_usage to show consistent usage across all commands"""
        # Build the command path
        pieces: List[str] = []
        current_ctx: Optional[click.Context] = ctx
        while current_ctx is not None:
            if current_ctx.info_name:
                pieces.insert(0, current_ctx.info_name)
            current_ctx = current_ctx.parent

        # Build usage line showing the full command path
        command_path = " ".join(pieces[1:]) if len(pieces) > 1 else ""

        # Collect arguments for this command, preferring metavar over name
        args_str = ""
        if hasattr(self, "params"):
            args = []
            for p in self.params:
                if isinstance(p, click.Argument) and p.name:
                    # Use metavar if available, otherwise uppercase name
                    arg_display = p.metavar if hasattr(p, "metavar") and p.metavar else p.name.upper()
                    args.append(arg_display)
            if args:
                args_str = " " + " ".join(args)

        if command_path:
            usage_line = f"n8n-deploy {command_path}{args_str} [OPTIONS]..."
        else:
            usage_line = "n8n-deploy COMMAND [OPTIONS]..."

        formatter.write(f"Usage: {usage_line}\n\n")


class CustomGroup(click.Group):
    """Custom Click Group that formats usage as 'COMMAND [OPTIONS]...' instead of '[OPTIONS] COMMAND [ARGS]...'"""

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """Override to disable prefix matching - require exact command names"""
        return self.commands.get(cmd_name)

    def collect_usage_pieces(self, ctx: click.Context) -> List[str]:
        """Override to collect custom usage pieces"""
        # Get the original pieces first for the program name
        original_pieces = super().collect_usage_pieces(ctx)
        rv = []
        # Keep the program name from the original
        if original_pieces:
            rv.append(original_pieces[0])
        # Add just the command part - we'll handle OPTIONS separately
        rv.append("COMMAND")
        return rv

    def format_usage(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Override format_usage to completely control the output"""
        # Build the complete usage string we want
        usage_line = "n8n-deploy COMMAND [OPTIONS]..."

        # Write it directly
        formatter.write(f"Usage: {usage_line}\n\n")

    def parse_args(self, ctx: click.Context, args: List[str]) -> List[str]:
        """Override to handle version/help mutual exclusion and no-args behavior"""
        # Check for both --help and --version
        has_help = any(arg in ["--help", "-h"] for arg in args)
        has_version = "--version" in args

        if has_help and has_version:
            # Silently exit when both are used
            ctx.exit(0)

        return super().parse_args(ctx, args)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Override __call__ to handle no-args case with exit code 0"""
        import sys

        try:
            return super().__call__(*args, **kwargs)
        except Exception as e:
            # Handle NoArgsIsHelpError at runtime (not in type stubs)
            if e.__class__.__name__ == "NoArgsIsHelpError":
                print(str(e))
                sys.exit(0)
            raise


def handle_version_help(ctx: click.Context, _param: click.Parameter, value: Any) -> None:
    """Handle version/help mutual exclusion - silently ignore when both used"""
    if not value or ctx.resilient_parsing:
        return

    # Check if both version and help are requested
    import sys

    args = sys.argv[1:]
    has_help = any(arg in ["--help", "-h"] for arg in args)
    has_version = "--version" in args

    if has_help and has_version:
        # Silently ignore when both are used - exit with no output
        ctx.exit(0)

    # Show version from package metadata
    try:
        from importlib.metadata import version

        pkg_version = version("n8n-deploy")
    except Exception:
        from api import __version__

        pkg_version = __version__
    click.echo(f"n8n-deploy, version {pkg_version}")
    ctx.exit()


def handle_verbose_flag(ctx: click.Context, _param: click.Parameter, value: int) -> None:
    """Handle verbose flag - sets global verbose level

    Args:
        ctx: Click context
        _param: Click parameter (unused)
        value: Verbosity level count (0=off, 1=-v, 2=-vv)
    """
    if value and not ctx.resilient_parsing:
        set_verbose(value)


@click.group(cls=CustomGroup, context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
@click.option(
    "--version", is_flag=True, expose_value=False, is_eager=True, callback=handle_version_help, help="Show version and exit"
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    expose_value=False,
    is_eager=True,
    callback=handle_verbose_flag,
    help="Verbosity level (-v HTTP/SFTP ops, -vv +details/timing)",
)
def cli() -> None:
    """🎭 n8n-deploy - a simple N8N Workflow Manager

    Use 'n8n-deploy COMMAND --help' for detailed command options.

    ⚠️  NOTE: Run 'n8n-deploy db init' before using other commands.

    \b
    📂 Core Directories:

    \b
    App Directory ('--data-dir'):
      Stores application data (database, backups)
      Priority: '--data-dir' CLI option > N8N_DEPLOY_DATA_DIR env var > current directory
      Default file: n8n-deploy.db

    \b
    Flow Directory ('--flow-dir'):
      Contains workflow JSON files
      Priority: '--flow-dir' CLI option > N8N_DEPLOY_FLOWS_DIR env var > current directory
      Default: current directory

    \b
    🌐 Server Configuration:
      n8n Server URL: '--remote' CLI option > N8N_SERVER_URL env var
      API Keys: Stored in database, managed via 'apikey' commands
    """
    pass


# Register command groups
def register_commands() -> None:
    """Register all command groups with the main CLI"""
    from .apikey import apikey
    from .db import db
    from .env import env
    from .folder import folder
    from .server import server
    from .wf import wf

    # Register command groups
    cli.add_command(wf)
    cli.add_command(db)
    cli.add_command(apikey)
    cli.add_command(server)
    cli.add_command(env)
    cli.add_command(folder)


# Auto-register commands when module is imported
register_commands()


# This will be the main CLI app that other modules will extend
def get_cli_app() -> click.Group:
    """Get the main CLI application with all commands registered"""
    register_commands()
    return cli


if __name__ == "__main__":
    register_commands()
    cli()
