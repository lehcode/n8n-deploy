#!/usr/bin/env python3
"""
Environment configuration display commands
"""

import json
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .app import CustomCommand

console = Console()

# Check if dotenv is available and development mode is enabled
HAS_DOTENV = False
if os.getenv("ENVIRONMENT", "").lower() == "development":
    try:
        from dotenv import load_dotenv

        HAS_DOTENV = True
    except ImportError:
        pass


@click.command(cls=CustomCommand)
@click.option("--data-dir", type=click.Path(), help="Application directory path")
@click.option("--flow-dir", type=click.Path(), help="Flow directory path")
@click.option("--remote", type=str, help="n8n server URL")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format for scripting")
@click.option("--table", "output_table", is_flag=True, help="Output in table format with emoji")
def env(
    data_dir: Optional[str],
    flow_dir: Optional[str],
    remote: Optional[str],
    output_json: bool,
    output_table: bool,
) -> None:
    """🌍 Show environment configuration and variable precedence

    Displays current configuration values and their sources (CLI, env vars, .env files).
    Useful for debugging configuration issues and understanding precedence.

    Note: .env file support requires ENVIRONMENT=development
    """
    # Load .env files if in development mode
    if HAS_DOTENV:
        load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
        load_dotenv(dotenv_path=Path.home() / ".env", override=False)

    # Check for .env files
    cwd_env = Path.cwd() / ".env"
    home_env = Path.home() / ".env"

    # Determine actual values and their sources
    config_items = []

    # App Directory
    data_dir_value = data_dir or os.getenv("N8N_DEPLOY_DATA") or str(Path.cwd())
    data_dir_source = "CLI" if data_dir else ("N8N_DEPLOY_DATA" if os.getenv("N8N_DEPLOY_DATA") else "default (cwd)")
    config_items.append(("N8N_DEPLOY_DATA", data_dir_value, data_dir_source))

    # Flow Directory
    flow_dir_value = flow_dir or os.getenv("N8N_DEPLOY_FLOWS") or str(Path.cwd())
    flow_dir_source = "CLI" if flow_dir else ("N8N_DEPLOY_FLOWS" if os.getenv("N8N_DEPLOY_FLOWS") else "default (cwd)")
    config_items.append(("N8N_DEPLOY_FLOWS", flow_dir_value, flow_dir_source))

    # Server URL
    server_url_value = remote or os.getenv("N8N_SERVER_URL") or "not set"
    server_url_source = "CLI" if remote else ("N8N_SERVER_URL" if os.getenv("N8N_SERVER_URL") else "not set")
    config_items.append(("N8N_SERVER_URL", server_url_value, server_url_source))

    # API Key (don't show the value, just the source)
    api_key_set = bool(os.getenv("N8N_DEPLOY_SERVER_KEY"))
    api_key_source = "N8N_DEPLOY_SERVER_KEY" if api_key_set else "not set"
    config_items.append(("N8N_DEPLOY_SERVER_KEY", "***" if api_key_set else "not set", api_key_source))

    # Testing flag
    testing_value = os.getenv("N8N_DEPLOY_TESTING", "not set")
    testing_source = "N8N_DEPLOY_TESTING" if os.getenv("N8N_DEPLOY_TESTING") else "not set"
    config_items.append(("N8N_DEPLOY_TESTING", testing_value, testing_source))

    # Environment mode (development/production)
    env_mode = os.getenv("ENVIRONMENT", "production")
    env_source = "ENVIRONMENT" if os.getenv("ENVIRONMENT") else "default"
    dotenv_status = "enabled" if HAS_DOTENV else "disabled"

    # Add to config_items - value depends on format
    config_items.append(("ENVIRONMENT", env_mode, env_source))

    if output_json:
        # JSON output for programmatic use
        # Priority order depends on whether dotenv is enabled
        if HAS_DOTENV:
            priority_order = [
                "CLI options (--data-dir, --flow-dir, --remote)",
                "Environment variables (N8N_DEPLOY_DATA, N8N_DEPLOY_FLOWS, etc.)",
                ".env files (current directory > user home)",
                "Defaults (current working directory)",
            ]
        else:
            priority_order = [
                "CLI options (--data-dir, --flow-dir, --remote)",
                "Environment variables (N8N_DEPLOY_DATA, N8N_DEPLOY_FLOWS, etc.)",
                "Defaults (current working directory)",
            ]

        output = {
            "variables": {var: {"value": value, "source": source} for var, value, source in config_items},
            "priority_order": priority_order,
        }

        # Only include dotenv info in development mode
        if HAS_DOTENV:
            output["dotenv_files"] = {
                "current_directory": {"path": str(cwd_env), "exists": cwd_env.exists()},
                "user_home": {"path": str(home_env), "exists": home_env.exists()},
            }

        # Use click.echo for JSON to avoid Rich's text processing
        click.echo(json.dumps(output, indent=2, ensure_ascii=False))
    elif output_table:
        # Rich emoji table output
        console.print("\n🌍 [bold cyan]Environment Configuration[/bold cyan]\n")

        # .env files status
        env_table = Table(title=".env Files", show_header=True)
        env_table.add_column("Location", style="cyan")
        env_table.add_column("Path", style="white")
        env_table.add_column("Status", style="green")

        env_table.add_row("Current directory", str(cwd_env), "✅ exists" if cwd_env.exists() else "❌ not found")
        env_table.add_row("User home", str(home_env), "✅ exists" if home_env.exists() else "❌ not found")
        console.print(env_table)

        # Configuration variables
        console.print("\n📋 [bold cyan]Configuration Variables[/bold cyan]\n")
        config_table = Table(show_header=True)
        config_table.add_column("Variable", style="cyan", no_wrap=True)
        config_table.add_column("Value", style="white")
        config_table.add_column("Source", style="yellow")

        for var, value, source in config_items:
            # Add .env status annotation for ENVIRONMENT variable in display formats
            display_value = f"{value} (.env: {dotenv_status})" if var == "ENVIRONMENT" else value
            config_table.add_row(var, display_value, source)

        console.print(config_table)

        # Priority order
        console.print("\n📌 [bold cyan]Priority Order[/bold cyan]")
        console.print("  1️⃣  CLI options (--data-dir, --flow-dir, --remote)")
        console.print("  2️⃣  Environment variables (N8N_DEPLOY_DATA, N8N_DEPLOY_FLOWS, etc.)")
        if HAS_DOTENV:
            console.print("  3️⃣  .env files (current directory > user home)")
            console.print("  4️⃣  Defaults (current working directory)")
        else:
            console.print("  3️⃣  Defaults (current working directory)")
        console.print()
    else:
        # Default: Plain text output (no format specified)
        console.print("\n=== Environment Configuration ===\n")
        console.print(f".env file (cwd):  {cwd_env} ({'exists' if cwd_env.exists() else 'not found'})")
        console.print(f".env file (home): {home_env} ({'exists' if home_env.exists() else 'not found'})")
        console.print("\n=== Configuration Variables ===\n")
        for var, value, source in config_items:
            # Add .env status annotation for ENVIRONMENT variable in display formats
            display_value = f"{value} (.env: {dotenv_status})" if var == "ENVIRONMENT" else value
            console.print(f"{var:25} = {display_value:40} (source: {source})")
        console.print("\n=== Priority Order ===")
        console.print("1. CLI options (--data-dir, --flow-dir, --remote)")
        console.print("2. Environment variables (N8N_DEPLOY_DATA, N8N_DEPLOY_FLOWS, etc.)")
        if HAS_DOTENV:
            console.print("3. .env files (current directory > user home)")
            console.print("4. Defaults (current working directory)")
        else:
            console.print("3. Defaults (current working directory)")
