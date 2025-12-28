#!/usr/bin/env python3
"""
CLI Consistency Tests

Ensures consistent behavior across all CLI commands including help messages,
output formats, and command structure.
"""

import os
import subprocess
from typing import List

import pytest

os.environ["N8N_DEPLOY_TESTING"] = "1"

# Expected usage text that should appear in all help messages
EXPECTED_USAGE = "Usage: n8n-deploy COMMAND [OPTIONS]..."


def get_all_commands() -> List[List[str]]:
    """
    Get all CLI commands to test.

    Returns list of command paths like:
    - ["wf", "list"]
    - ["db", "status"]
    - ["apikey", "add"]
    """
    commands = [
        # Main command
        [],
        # Workflow commands
        ["wf"],
        ["wf", "add"],
        ["wf", "list"],
        ["wf", "delete"],
        ["wf", "search"],
        ["wf", "stats"],
        ["wf", "pull"],
        ["wf", "push"],
        ["wf", "server"],
        # Database commands
        ["db"],
        ["db", "init"],
        ["db", "status"],
        ["db", "backup"],
        ["db", "compact"],
        # API key commands
        ["apikey"],
        ["apikey", "add"],
        ["apikey", "list"],
        ["apikey", "activate"],
        ["apikey", "deactivate"],
        ["apikey", "delete"],
        ["apikey", "test"],
        # Server commands
        ["server"],
        ["server", "create"],
        ["server", "list"],
        ["server", "remove"],
        ["server", "keys"],
        # Environment command
        ["env"],
    ]
    return commands


def get_command_groups() -> List[List[str]]:
    """
    Get command groups that should show generic 'COMMAND [OPTIONS]...' usage.

    Command groups are the parent commands that have subcommands.
    """
    return [
        [],  # Main command
        ["wf"],  # Workflow group
        ["db"],  # Database group
        ["apikey"],  # API key group
        ["server"],  # Server group
    ]


@pytest.mark.integration
class TestCLIHelpConsistency:
    """Test that all CLI commands have consistent help messages"""

    @pytest.mark.parametrize("command_path", get_all_commands())
    def test_help_usage_format_consistency(self, command_path: List[str]) -> None:
        """
        Test that every command's help shows consistent usage format.

        This ensures consistent help output across all commands.
        Command groups show: "Usage: n8n-deploy COMMAND [OPTIONS]..."
        Specific commands show: "Usage: n8n-deploy wf add [OPTIONS]..."
        """
        cmd = ["./n8n-deploy"] + command_path + ["--help"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Help should always succeed
        assert result.returncode == 0, f"Help failed for {' '.join(command_path or ['root'])}"

        output = result.stdout + result.stderr

        # All help should start with "Usage: n8n-deploy"
        assert output.startswith("Usage: n8n-deploy"), (
            f"Command {' '.join(command_path or ['root'])} help does not start with expected usage prefix.\n"
            f"Got output:\n{output[:200]}"
        )

        # All help should include "[OPTIONS]..."
        assert "[OPTIONS]..." in output, (
            f"Command {' '.join(command_path or ['root'])} help does not contain [OPTIONS]... format.\n"
            f"Got output:\n{output[:200]}"
        )

    def test_all_commands_tested(self) -> None:
        """
        Verify that we're testing all available commands.

        This is a meta-test to ensure the command list is complete.
        """
        commands = get_all_commands()

        # Should test at least 28 commands (main + subcommands)
        # Note: Was 30+ before workflow backup removal (createbackup, restore, backups, verify)
        # Was 27 after apikey get removal (security enhancement)
        # Was 28 after apikey activate addition
        assert len(commands) >= 28, f"Only testing {len(commands)} commands, expected at least 28"

        # Should include main groups
        command_groups = [cmd[0] for cmd in commands if len(cmd) > 0]
        assert "wf" in command_groups
        assert "db" in command_groups
        assert "apikey" in command_groups
        assert "server" in command_groups
        assert "env" in command_groups
