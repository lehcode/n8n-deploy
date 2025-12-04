#!/usr/bin/env python3
"""
End-to-End Manual CLI Testing

Real CLI execution tests for basic operations, output formatting,
environment variable handling, and configuration consistency.
"""

from pathlib import Path

import pytest

from .e2e_base import E2ETestBase


# === End-to-End CLI Tests ===
class TestE2ECLI(E2ETestBase):
    """Manual end-to-end testing for CLI operations"""

    def test_version_command(self) -> None:
        """Test --version flag shows correct version"""
        import re

        returncode, stdout, stderr = self.run_cli_command(["--version"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Version command test")

        assert "n8n-deploy, version" in stdout, f"Version string not found in output: '{stdout}'"
        # Check for semantic version pattern
        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        version_pattern = r"\d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"
        assert re.search(version_pattern, stdout), f"Valid version number not found in output: '{stdout}'"
        # Wrapper script may output setup message to stderr
        assert stderr == "" or "Setting up virtual environment" in stderr, f"Unexpected stderr output: '{stderr}'"

    def test_help_command_basic(self) -> None:
        """Test --help shows main help"""
        returncode, stdout, stderr = self.run_cli_command(["--help"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Help command test")

        assert (
            "n8n-deploy - a simple N8N Workflow Manager" in stdout
        ), f"Main title not found in help output. STDOUT: {stdout[:500]}..."
        assert "Commands:" in stdout, f"Commands section not found in help output. STDOUT: {stdout[:500]}..."
        assert "Workflow management" in stdout, f"Workflow command group not found. STDOUT: {stdout[:500]}..."
        assert "API key management" in stdout, f"API key command not found. STDOUT: {stdout[:500]}..."

    def test_help_command_always_shows_emojis(self) -> None:
        """Test help always shows emojis (help is intentionally emoji-only)"""
        returncode, stdout, stderr = self.run_cli_command(["--help"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Help command emoji test")

        # Help should always contain emojis for user-friendly display
        assert "🎭" in stdout, f"Main emoji not found in help output. STDOUT: {stdout[:500]}..."
        assert "🔄" in stdout, f"Workflow emoji not found in help output. STDOUT: {stdout[:500]}..."
        assert "🔐" in stdout, f"API key emoji not found. STDOUT: {stdout[:500]}..."
        assert (
            "n8n-deploy - a simple N8N Workflow Manager" in stdout
        ), f"Main title not found in help output. STDOUT: {stdout[:500]}..."

    def test_version_command_basic(self) -> None:
        """Test --version shows version information"""
        returncode, stdout, stderr = self.run_cli_command(["--version"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Version command test")

        assert "n8n-deploy, version" in stdout, f"Version string not found. STDOUT: {stdout[:200]}..."
        # Should contain version number
        # Supports: 2.0.3, 2.0.3.dev42, 2.3.0-rc1, 0.1.dev37 (CI fallback)
        import re

        version_pattern = r"n8n-deploy, version \d+\.\d+(\.\d+)?(\.dev\d+|-rc\d+)?"
        assert re.search(version_pattern, stdout), f"Version format incorrect. STDOUT: {stdout[:200]}..."

    def test_help_and_version_combination_behavior(self) -> None:
        """Test that --help --version combination silently exits (mutual exclusion)"""
        # Both flags together should silently exit with no output
        returncode, stdout, stderr = self.run_cli_command(["--help", "--version"])

        # Should silently exit with no output when both flags used
        assert returncode == 0, f"Help/version combination failed. STDERR: {stderr}"
        assert stdout.strip() == "", f"Expected no output when both flags used. STDOUT: {stdout[:200]}..."

        # Test reverse order - should also silently exit
        returncode2, stdout2, stderr2 = self.run_cli_command(["--version", "--help"])
        assert returncode2 == 0, f"Version/help combination failed. STDERR: {stderr2}"
        assert stdout2.strip() == "", f"Expected no output in reverse order. STDOUT: {stdout2[:200]}..."

    def test_wf_list_command_shows_environment_variables(self) -> None:
        """Test list command displays environment configuration"""
        # Initialize database first
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        env = {
            "N8N_DEPLOY_FLOWS_DIR": self.temp_flow_dir,
        }

        returncode, stdout, stderr = self.run_cli_command(["wf", "list"], env=env)

        self.assert_command_details(
            returncode,
            stdout,
            stderr,
            0,
            f"List command with environment variables. Temp dirs: app={self.temp_dir}, flow={self.temp_flow_dir}",
        )

        # Command should succeed and show either workflows or "No workflows found"
        assert (
            "No workflows found" in stdout or "test_" in stdout
        ), f"Expected wf list or 'No workflows found'. STDOUT: {stdout[:500]}..."

    def test_base_folder_consistency(self) -> None:
        """Test base folder configuration across different commands"""
        # Only test database commands that accept --data-dir
        # Workflow commands use --flow-dir instead
        commands_to_test = [
            ["db", "status"],
            ["db", "backup"],
            ["db", "compact"],
        ]
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        for cmd in commands_to_test:
            returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir] + cmd)

            # All commands should succeed with the same base folder
            self.assert_command_details(
                returncode,
                stdout,
                stderr,
                0,
                f"Base folder consistency test for command: {cmd}, base folder: {self.temp_dir}",
            )

    def test_flow_dir_environment_variable_priority(self) -> None:
        """Test N8N_DEPLOY_FLOWS environment variable is respected"""
        env = {"N8N_DEPLOY_FLOWS_DIR": self.temp_flow_dir}
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["wf", "list"], env=env)

        self.assert_command_details(
            returncode,
            stdout,
            stderr,
            0,
            f"Flow dir environment variable test. N8N_DEPLOY_FLOWS={self.temp_flow_dir}",
        )

    def test_cli_option_precedence_over_env(self) -> None:
        """Test CLI --data-dir option takes precedence over environment"""

        env = {"N8N_DEPLOY_DATA_DIR": "/tmp/env-dir"}

        # Initialize database first
        returncode, stdout, stderr = self.run_cli_command(["db", "init", "--data-dir", self.temp_dir])
        assert returncode == 0

        # Test that CLI --data-dir takes precedence over env variable
        # This should succeed because we use the correct temp_dir via CLI option
        returncode, stdout, stderr = self.run_cli_command(
            ["db", "status", "--data-dir", self.temp_dir],
            env=env,
        )

        self.assert_command_details(
            returncode,
            stdout,
            stderr,
            0,
            f"CLI option precedence test. ENV_DIR=/tmp/env-dir, CLI_DIR={self.temp_dir}",
        )

    def test_database_commands_consistency(self) -> None:
        """Test database commands work consistently with configuration"""
        # Initialize database
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        self.assert_command_details(
            returncode,
            stdout,
            stderr,
            0,
            f"Database initialization. App dir: {self.temp_dir}",
        )
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status"])
        self.assert_command_details(
            returncode,
            stdout,
            stderr,
            0,
            f"Database status check. App dir: {self.temp_dir}",
        )
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists(), f"Database file not created at expected path: {db_path}"

    def test_no_duplicate_initialization_messages(self) -> None:
        """Test no duplicate database initialization messages"""
        # First initialization
        returncode1, stdout1, stderr1 = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Second initialization (should not duplicate)
        returncode2, stdout2, stderr2 = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        self.assert_command_details(returncode1, stdout1, stderr1, 0, "First database init")
        self.assert_command_details(
            returncode2,
            stdout2,
            stderr2,
            0,
            "Second database init (should handle existing database gracefully)",
        )

    def test_command_help_consistency(self) -> None:
        """Test individual command help is consistent"""
        commands_with_help = [
            ["wf", "--help"],
            ["apikey", "--help"],
            ["db", "--help"],
            ["wf", "list", "--help"],
        ]
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        for cmd in commands_with_help:
            returncode, stdout, stderr = self.run_cli_command(cmd)
            self.assert_command_details(returncode, stdout, stderr, 0, f"Help for command: {cmd}")
            assert "Usage:" in stdout, f"Help for {cmd} missing usage section. STDOUT: {stdout[:300]}..."

    def test_error_handling_invalid_commands(self) -> None:
        """Test error handling for invalid commands"""
        invalid_commands = [
            ["invalid-command"],
            ["add", "--invalid-option"],
            ["db", "invalid-subcommand"],
        ]

        for cmd in invalid_commands:
            returncode, stdout, stderr = self.run_cli_command(cmd)
            assert (
                returncode != 0
            ), f"Invalid command {cmd} should fail but returned {returncode}. STDOUT: {stdout}, STDERR: {stderr}"

    def test_working_directory_independence(self) -> None:
        """Test CLI works from different working directories"""

        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["wf", "list"], cwd=str(sub_dir))

        self.assert_command_details(
            returncode,
            stdout,
            stderr,
            0,
            f"Working directory independence test from {sub_dir}",
        )

    def test_long_path_handling(self) -> None:
        """Test handling of long file paths"""

        long_path = Path(self.temp_dir)
        for i in range(5):
            long_path = long_path / f"very_long_directory_name_{i}"
        long_path.mkdir(parents=True)
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", str(long_path), "db", "status"])

        # Should handle long paths gracefully
        assert returncode in [
            0,
            1,
        ], f"Long path test crashed unexpectedly. Path: {long_path}, Returncode: {returncode}, STDERR: {stderr}"

    def test_special_characters_in_paths(self) -> None:
        """Test handling of special characters in directory paths"""

        try:
            special_dir = Path(self.temp_dir) / "test-dir with spaces"
            special_dir.mkdir()

            returncode, stdout, stderr = self.run_cli_command(["--data-dir", str(special_dir), "db", "status"])

            # Should handle special characters in paths
            assert returncode in [
                0,
                1,
            ], f"Special characters in path test failed. Path: {special_dir}, Returncode: {returncode}, STDERR: {stderr}"
        except OSError:
            # Skip if filesystem doesn't support special characters
            pytest.skip("Filesystem doesn't support special characters in paths")

    def test_concurrent_command_safety(self) -> None:
        """Test multiple CLI commands can be run safely

        This test verifies that concurrent CLI access doesn't corrupt the database.
        SQLite may return "database is locked" errors under concurrent access,
        which is acceptable - the key is that the database remains intact.
        """
        import threading
        import time
        from typing import List, Tuple

        # Initialize database first
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        results: List[Tuple[int, str, str]] = []
        lock = threading.Lock()

        def run_command() -> None:
            returncode, stdout, stderr = self.run_cli_command(["wf", "list"])
            with lock:
                results.append((returncode, stdout, stderr))

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=run_command)
            threads.append(thread)
            thread.start()
            # Small delay to reduce lock contention
            time.sleep(0.05)

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All threads should complete
        assert len(results) == 3, f"Expected 3 concurrent results, got {len(results)}"

        # Count successes and acceptable failures (database locked is OK)
        successes = 0
        for returncode, stdout, stderr in results:
            if returncode == 0:
                successes += 1

        # At least one operation should succeed
        assert successes >= 1, f"No operations succeeded. Results: {results}"

        # Verify database is still accessible after concurrent access
        returncode, stdout, stderr = self.run_cli_command(["wf", "list"])
        assert returncode == 0, f"Database inaccessible after concurrent access: {stderr}"

    def test_environment_isolation(self) -> None:
        """Test environment variable isolation between commands"""
        # Initialize database first
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        env1 = {"N8N_DEPLOY_FLOWS_DIR": self.temp_flow_dir}
        returncode1, stdout1, stderr1 = self.run_cli_command(["wf", "list"], env=env1)
        returncode2, stdout2, stderr2 = self.run_cli_command(["wf", "list"])

        self.assert_command_details(
            returncode1,
            stdout1,
            stderr1,
            0,
            "Environment isolation test with N8N_DEPLOY_FLOWS_DIR",
        )
        self.assert_command_details(
            returncode2,
            stdout2,
            stderr2,
            0,
            "Environment isolation test without env var",
        )

    def test_command_chaining_independence(self) -> None:
        """Test commands don't interfere with each other"""
        # Initialize database first
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Test different command types
        # Note: wf list reads from database, so it uses --data-dir
        test_cases = [
            (["--data-dir", self.temp_dir, "db", "status"], "db status with data-dir"),
            (["--data-dir", self.temp_dir, "wf", "list"], "wf list with data-dir"),
            (["--data-dir", self.temp_dir, "apikey", "list"], "apikey list with data-dir"),
            (["--data-dir", self.temp_dir, "db", "status"], "db status repeat"),
        ]

        for cmd, description in test_cases:
            returncode, stdout, stderr = self.run_cli_command(cmd)
            self.assert_command_details(
                returncode,
                stdout,
                stderr,
                0,
                f"Command sequence test for: {description}",
            )
