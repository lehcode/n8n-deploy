#!/usr/bin/env python3
"""
Environment configuration display commands
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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


def _gather_config_items(
    data_dir: Optional[str], flow_dir: Optional[str], remote: Optional[str]
) -> Tuple[List[Tuple[str, str, str]], str]:
    """Gather configuration items and their sources.

    Returns:
        Tuple of (config_items list, dotenv_status string)
    """
    config_items: List[Tuple[str, str, str]] = []

    # App Directory
    data_dir_value = data_dir or os.getenv("N8N_DEPLOY_DATA_DIR") or str(Path.cwd())
    data_dir_source = "CLI" if data_dir else ("N8N_DEPLOY_DATA_DIR" if os.getenv("N8N_DEPLOY_DATA_DIR") else "default (cwd)")
    config_items.append(("N8N_DEPLOY_DATA_DIR", data_dir_value, data_dir_source))

    # Flow Directory
    flow_dir_value = flow_dir or os.getenv("N8N_DEPLOY_FLOWS_DIR") or str(Path.cwd())
    flow_dir_source = "CLI" if flow_dir else ("N8N_DEPLOY_FLOWS_DIR" if os.getenv("N8N_DEPLOY_FLOWS_DIR") else "default (cwd)")
    config_items.append(("N8N_DEPLOY_FLOWS_DIR", flow_dir_value, flow_dir_source))

    # Server URL
    server_url_value = remote or os.getenv("N8N_SERVER_URL") or "not set"
    server_url_source = "CLI" if remote else ("N8N_SERVER_URL" if os.getenv("N8N_SERVER_URL") else "not set")
    config_items.append(("N8N_SERVER_URL", server_url_value, server_url_source))

    # API Key (don't show the value, just the source)
    api_key_set = bool(os.getenv("N8N_API_KEY"))
    api_key_source = "N8N_API_KEY" if api_key_set else "not set"
    config_items.append(("N8N_API_KEY", "***" if api_key_set else "not set", api_key_source))

    # Testing flag
    testing_value = os.getenv("N8N_DEPLOY_TESTING", "not set")
    testing_source = "N8N_DEPLOY_TESTING" if os.getenv("N8N_DEPLOY_TESTING") else "not set"
    config_items.append(("N8N_DEPLOY_TESTING", testing_value, testing_source))

    # Environment mode
    env_mode = os.getenv("ENVIRONMENT", "production")
    env_source = "ENVIRONMENT" if os.getenv("ENVIRONMENT") else "default"
    config_items.append(("ENVIRONMENT", env_mode, env_source))

    dotenv_status = "enabled" if HAS_DOTENV else "disabled"
    return config_items, dotenv_status


def _get_priority_order() -> List[str]:
    """Get the configuration priority order list."""
    if HAS_DOTENV:
        return [
            "CLI options (--data-dir, --flow-dir, --remote)",
            "Environment variables (N8N_DEPLOY_DATA_DIR, N8N_DEPLOY_FLOWS_DIR, etc.)",
            ".env files (current directory > user home)",
            "Defaults (current working directory)",
        ]
    return [
        "CLI options (--data-dir, --flow-dir, --remote)",
        "Environment variables (N8N_DEPLOY_DATA_DIR, N8N_DEPLOY_FLOWS_DIR, etc.)",
        "Defaults (current working directory)",
    ]


def _output_json(config_items: List[Tuple[str, str, str]], cwd_env: Path, home_env: Path) -> None:
    """Output configuration in JSON format."""
    output: Dict[str, Any] = {
        "variables": {var: {"value": value, "source": source} for var, value, source in config_items},
        "priority_order": _get_priority_order(),
    }

    if HAS_DOTENV:
        output["dotenv_files"] = {
            "current_directory": {"path": str(cwd_env), "exists": cwd_env.exists()},
            "user_home": {"path": str(home_env), "exists": home_env.exists()},
        }

    click.echo(json.dumps(output, indent=2, ensure_ascii=False))


def _output_table(
    config_items: List[Tuple[str, str, str]],
    cwd_env: Path,
    home_env: Path,
    dotenv_status: str,
) -> None:
    """Output configuration in Rich table format with emoji."""
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
        display_value = f"{value} (.env: {dotenv_status})" if var == "ENVIRONMENT" else value
        config_table.add_row(var, display_value, source)
    console.print(config_table)

    # Priority order
    console.print("\n📌 [bold cyan]Priority Order[/bold cyan]")
    for i, item in enumerate(_get_priority_order(), 1):
        emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"][i - 1]
        console.print(f"  {emoji}  {item}")
    console.print()


def _output_plain(
    config_items: List[Tuple[str, str, str]],
    cwd_env: Path,
    home_env: Path,
    dotenv_status: str,
) -> None:
    """Output configuration in plain text format."""
    console.print("\n=== Environment Configuration ===\n")
    console.print(f".env file (cwd):  {cwd_env} ({'exists' if cwd_env.exists() else 'not found'})")
    console.print(f".env file (home): {home_env} ({'exists' if home_env.exists() else 'not found'})")
    console.print("\n=== Configuration Variables ===\n")

    for var, value, source in config_items:
        display_value = f"{value} (.env: {dotenv_status})" if var == "ENVIRONMENT" else value
        console.print(f"{var:25} = {display_value:40} (source: {source})")

    console.print("\n=== Priority Order ===")
    for i, item in enumerate(_get_priority_order(), 1):
        console.print(f"{i}. {item}")


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

    # Gather configuration
    config_items, dotenv_status = _gather_config_items(data_dir, flow_dir, remote)

    # Output in requested format
    if output_json:
        _output_json(config_items, cwd_env, home_env)
    elif output_table:
        _output_table(config_items, cwd_env, home_env, dotenv_status)
    else:
        _output_plain(config_items, cwd_env, home_env, dotenv_status)
