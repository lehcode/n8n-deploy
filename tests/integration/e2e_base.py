#!/usr/bin/env python3
"""
Base class for End-to-End testing with common CLI execution patterns.

Provides shared functionality for E2E test classes to eliminate duplication.
"""

import os
import subprocess
import tempfile
from typing import Dict, Iterator, List, Optional, Tuple

import pytest


class E2ETestBase:
    """Base class for manual end-to-end testing"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self) -> Iterator[None]:
        """Set up clean test environment for each test"""
        # Ensure testing environment is set
        os.environ["N8N_DEPLOY_TESTING"] = "1"
        self.temp_dir = tempfile.mkdtemp()
        self.temp_flow_dir = tempfile.mkdtemp()

        # Set app directory for tests (so apikey commands can find database)
        os.environ["N8N_DEPLOY_DATA_DIR"] = self.temp_dir
        os.environ["N8N_DEPLOY_FLOWS_DIR"] = self.temp_flow_dir

        yield

        # Cleanup
        import shutil

        # Remove environment variables
        os.environ.pop("N8N_DEPLOY_DATA_DIR", None)
        os.environ.pop("N8N_DEPLOY_FLOWS_DIR", None)

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.temp_flow_dir, ignore_errors=True)

    def run_cli_command(
        self,
        args: List[str],
        stdin_input: str = "",
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 60,
    ) -> Tuple[int, str, str]:
        """Execute n8n-deploy CLI command and return result"""
        # Reorder arguments to handle global options correctly
        # Convert ["--data-dir", "/path", "command", ...] to ["command", "--data-dir", "/path", ...]
        reordered_args = []
        global_options = []
        i = 0

        # Extract global options from the beginning
        while i < len(args):
            if args[i] in ["--data-dir", "--flow-dir", "--remote"] and i + 1 < len(args):
                global_options.extend([args[i], args[i + 1]])
                i += 2
            elif args[i] in ["--no-emoji", "--force", "--unmask", "--only"]:
                global_options.append(args[i])
                i += 1
            else:
                # Found the command, add it and remaining args
                reordered_args = args[i:] + global_options
                break

        # If no command found, use original args
        if not reordered_args:
            reordered_args = args

        # Use absolute path to n8n-deploy script for working directory independence
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "n8n-deploy")
        cmd = [script_path] + reordered_args

        # Add --no-emoji to commands that support it for consistent test output
        if reordered_args:
            command = reordered_args[0]
            # Commands that support --no-emoji at the command level
            no_emoji_commands = {"show", "server"}
            # wf subcommands that support --no-emoji
            no_emoji_wf_subcommands = {"show", "server", "add", "search", "stats"}
            # apikey subcommands that support --no-emoji
            no_emoji_apikey_subcommands = {"add", "list", "get"}
            # db subcommands that support --no-emoji
            no_emoji_db_subcommands = {"init", "status", "compact"}

            if command in no_emoji_commands:
                cmd.append("--no-emoji")
            elif command == "wf" and len(reordered_args) > 1:
                wf_subcommand = reordered_args[1]
                if wf_subcommand in no_emoji_wf_subcommands:
                    cmd.append("--no-emoji")
            elif command == "apikey" and len(reordered_args) > 1:
                apikey_subcommand = reordered_args[1]
                if apikey_subcommand in no_emoji_apikey_subcommands:
                    cmd.append("--no-emoji")
            elif command == "db" and len(reordered_args) > 1:
                db_subcommand = reordered_args[1]
                if db_subcommand in no_emoji_db_subcommands:
                    cmd.append("--no-emoji")

        # Merge environment variables
        test_env = os.environ.copy()
        if env:
            test_env.update(env)

        result = subprocess.run(
            cmd,
            cwd=cwd or os.getcwd(),
            env=test_env,
            input=stdin_input,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return result.returncode, result.stdout, result.stderr

    def assert_command_details(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        expected_returncode: int,
        context: str,
    ) -> None:
        """Provide detailed assertion information for test failures"""
        if returncode != expected_returncode:
            failure_details = [
                f"E2E test assertion failed: {context}",
                f"Expected return code: {expected_returncode}",
                f"Actual return code: {returncode}",
                "--- STDOUT ---",
                stdout if stdout else "(empty)",
                "--- STDERR ---",
                stderr if stderr else "(empty)",
                "--- END ---",
            ]
            pytest.fail("\n".join(failure_details))

    def run_help_command(self, args: List[str]) -> Tuple[int, str, str]:
        """Execute help command without --no-emoji flag"""
        cmd = ["./n8n-deploy"] + args

        test_env = os.environ.copy()
        test_env["N8N_DEPLOY_TESTING"] = "1"

        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            env=test_env,
            capture_output=True,
            text=True,
            timeout=60,
        )

        return result.returncode, result.stdout, result.stderr

    def setup_database(self) -> None:
        """Initialize database for testing"""
        # Use --import to accept existing database without prompting
        returncode, stdout, stderr = self.run_cli_command(["db", "init", "--import"])
        self.assert_command_details(returncode, stdout, stderr, 0, "Database setup for E2E tests")

    def setup_database_with_api_key(self, api_key: str = "test-api-key-12345") -> bool:
        """Initialize database and add test API key"""
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        if returncode != 0:
            return False

        # Add API key
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "test_server"],
            stdin_input=f"{api_key}\n",
        )
        return returncode == 0
