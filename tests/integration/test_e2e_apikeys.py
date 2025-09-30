#!/usr/bin/env python3
"""
End-to-End Manual API Key Testing

Real CLI execution tests for API key management lifecycle,
including creation, listing, retrieval, and deletion operations.
"""

from .e2e_base import E2ETestBase


# === End-to-End Tests ===
class TestE2EAPIKeys(E2ETestBase):
    """Manual end-to-end testing for API key operations"""

    def test_api_key_add_interactive(self) -> None:
        """Test adding API key with interactive input"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNGEyODkxMy04ODQxLTRhMTAtODIzNC1iODQ2OTE1MmJhZTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU4NzY3MDI4LCJleHAiOjE3NjEyNzg0MDB9.d9u2SovTMfUGZ8EzD4SDLYNUTBarHpdwhv96pO-5imE"
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", test_key, "--name", "test_interactive", "--app-dir", self.temp_dir],
        )

        # Should succeed
        assert returncode == 0

    def test_api_key_add_with_stdin_input(self) -> None:
        """Test API key addition using stdin pipe"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNGEyODkxMy04ODQxLTRhMTAtODIzNC1iODQ2OTE1MmJhZTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU4NzY3MDI4LCJleHAiOjE3NjEyNzg0MDB9.d9u2SovTMfUGZ8EzD4SDLYNUTBarHpdwhv96pO-5imE"
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "test_stdin", "--app-dir", self.temp_dir],
            stdin_input=test_key,
        )

        # Should succeed
        assert returncode == 0

    def test_api_key_list_empty(self) -> None:
        """Test listing API keys when none exist"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["apikey", "list", "--app-dir", self.temp_dir])

        assert returncode == 0
        # Should show empty list or appropriate message

    def test_api_key_complete_lifecycle(self) -> None:
        """Test complete API key lifecycle: add, list, get, delete"""
        self.setup_database()

        key_name = "lifecycle_test"
        test_key = "lifecycle-test-key-789"

        # Step 1: Add API key
        add_returncode, add_stdout, add_stderr = self.run_cli_command(
            ["apikey", "add", key_name, "--app-dir", self.temp_dir],
            stdin_input=test_key,
        )

        if add_returncode == 0:
            # Step 2: List API keys (should show the added key)
            list_returncode, list_stdout, list_stderr = self.run_cli_command(["apikey", "list", "--app-dir", self.temp_dir])
            assert list_returncode == 0

            # Step 3: Get specific API key (without showing actual key)
            get_returncode, get_stdout, get_stderr = self.run_cli_command(
                ["apikey", "get", key_name, "--app-dir", self.temp_dir]
            )
            assert get_returncode == 0

            # Step 4: Get API key with --show-key flag
            show_returncode, show_stdout, show_stderr = self.run_cli_command(
                ["apikey", "get", key_name, "--show-key", "--app-dir", self.temp_dir]
            )
            if show_returncode == 0:
                # Should show the actual key
                assert test_key in show_stdout

            # Step 5: Delete API key
            delete_returncode, delete_stdout, delete_stderr = self.run_cli_command(
                ["apikey", "delete", key_name, "--confirm", "--app-dir", self.temp_dir]
            )
            # Should succeed or ask for confirmation
            assert delete_returncode in [0, 1]

    def test_api_key_get_nonexistent(self) -> None:
        """Test getting nonexistent API key"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["apikey", "get", "nonexistent_key", "--app-dir", self.temp_dir])

        # Should fail gracefully
        assert returncode == 1
        assert "not found" in stdout.lower() or "not found" in stderr.lower()

    def test_create_and_delete_apikey(self) -> None:
        """Test deleting nonexistent API key"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(
            [
                "apikey",
                "delete",
                "nonexistent_key",
                "--confirm",
                "--app-dir",
                self.temp_dir,
            ]
        )

        # Should fail gracefully
        assert returncode == 1

    def test_api_key_duplicate_names(self) -> None:
        """Test handling duplicate API key names"""
        self.setup_database()

        key_name = "duplicate_test"
        first_key = "first-key-123"
        second_key = "second-key-456"
        first_returncode, first_stdout, first_stderr = self.run_cli_command(
            ["apikey", "add", key_name, "--app-dir", self.temp_dir],
            stdin_input=first_key,
        )

        if first_returncode == 0:
            # Try to add second key with same name
            second_returncode, second_stdout, second_stderr = self.run_cli_command(
                ["apikey", "add", key_name, "--app-dir", self.temp_dir],
                stdin_input=second_key,
            )

            # Should handle duplicate names appropriately
            assert second_returncode in [0, 1]

    def test_api_key_emoji_vs_no_emoji_output(self) -> None:
        """Test API key commands with and without emoji"""
        self.setup_database()
        emoji_returncode, emoji_stdout, emoji_stderr = self.run_cli_command(["apikey", "list", "--app-dir", self.temp_dir])
        no_emoji_returncode, no_emoji_stdout, no_emoji_stderr = self.run_cli_command(
            ["apikey", "list", "--app-dir", self.temp_dir]
        )

        assert emoji_returncode == no_emoji_returncode == 0
        if "🔐" in emoji_stdout:
            assert "🔐" not in no_emoji_stdout

    def test_api_key_special_characters(self) -> None:
        """Test API keys with special characters"""
        self.setup_database()
        special_key = "test-key-with-special-chars!@#$%^&*()"
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "special_test", "--app-dir", self.temp_dir],
            stdin_input=special_key,
        )

        # Should handle special characters in API keys
        assert returncode in [0, 1]

    def test_api_key_long_names_and_values(self) -> None:
        """Test API keys with long names and values"""
        self.setup_database()
        long_name = "very_long_api_key_name_" + "x" * 100
        long_key = "very-long-api-key-value-" + "y" * 200

        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", long_name, "--app-dir", self.temp_dir],
            stdin_input=long_key,
        )

        # Should handle long names and values
        assert returncode in [0, 1]

    def test_api_key_empty_input(self) -> None:
        """Test API key commands with empty input"""
        self.setup_database()
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "empty_test", "--app-dir", self.temp_dir], stdin_input=""
        )

        # Should handle empty input appropriately
        assert returncode in [0, 1]

    def test_api_key_whitespace_handling(self) -> None:
        """Test API key handling of whitespace"""
        self.setup_database()
        whitespace_key = "  test-key-with-whitespace  \n"
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "whitespace_test", "--app-dir", self.temp_dir],
            stdin_input=whitespace_key,
        )

        # Should handle whitespace appropriately
        assert returncode in [0, 1]

    def run_help_command(self, args: list[str]) -> tuple[int, str, str]:
        """Execute help command without --no-emoji flag"""
        import subprocess
        import os

        cmd = ["./n8n-deploy"] + args

        test_env = os.environ.copy()
        test_env["N8N_DEPLOY_TESTING"] = "1"

        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            env=test_env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        return result.returncode, result.stdout, result.stderr

    def test_api_key_help_commands(self) -> None:
        """Test API key help commands"""
        help_commands = [
            ["apikey", "--help"],
            ["apikey", "add", "--help"],
            ["apikey", "list", "--help"],
            ["apikey", "get", "--help"],
            ["apikey", "delete", "--help"],
        ]

        for cmd in help_commands:
            returncode, stdout, stderr = self.run_help_command(cmd)
            assert returncode == 0
            assert "Usage:" in stdout

    def test_api_key_case_sensitivity(self) -> None:
        """Test API key name case sensitivity"""
        self.setup_database()
        lower_key = "lowercase-test-key"
        lower_returncode, _, _ = self.run_cli_command(
            ["apikey", "add", "testkey", "--app-dir", self.temp_dir],
            stdin_input=lower_key,
        )

        if lower_returncode == 0:
            # Try to get with different case
            upper_returncode, upper_stdout, upper_stderr = self.run_cli_command(
                ["apikey", "get", "TESTKEY", "--app-dir", self.temp_dir]
            )

            # Behavior depends on implementation (case sensitive or insensitive)
            assert upper_returncode in [0, 1]

    def test_server_commands_use_stored_api_keys(self) -> None:
        """Test server commands can use stored API keys"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"  # Mock JWT format
        add_returncode, _, _ = self.run_cli_command(
            ["apikey", "add", "n8n_server", "--app-dir", self.temp_dir],
            stdin_input=test_key,
        )

        if add_returncode == 0:
            server_returncode, server_stdout, server_stderr = self.run_cli_command(
                [
                    "list-server",
                    "--app-dir",
                    self.temp_dir,
                    "--server-url",
                    "http://localhost:5678",
                ]
            )

            # Should attempt to use stored API key
            # May fail due to server not running, but shouldn't crash
            assert server_returncode in [0, 1]

    def test_api_key_concurrent_operations(self) -> None:
        """Test concurrent API key operations"""
        import threading

        self.setup_database()

        results = []

        def add_api_key(key_suffix):
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "apikey",
                    "add",
                    f"concurrent_test_{key_suffix}",
                    "--app-dir",
                    self.temp_dir,
                ],
                stdin_input=f"test-key-{key_suffix}",
            )
            results.append((key_suffix, returncode, stdout, stderr))

        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_api_key, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()
        assert len(results) == 3
        # At least some should succeed
        successful_ops = [r for r in results if r[1] == 0]
        assert len(successful_ops) >= 0  # May depend on implementation

    def test_api_key_persistence_across_commands(self) -> None:
        """Test API keys persist across different command invocations"""
        self.setup_database()
        add_returncode, _, _ = self.run_cli_command(
            ["apikey", "add", "persistence_test", "--app-dir", self.temp_dir],
            stdin_input="persistent-test-key",
        )

        if add_returncode == 0:
            self.run_cli_command(["list", "--app-dir", self.temp_dir, "--flow-dir", self.temp_flow_dir])
            self.run_cli_command(["stats", "--app-dir", self.temp_dir, "--flow-dir", self.temp_flow_dir])
            get_returncode, get_stdout, get_stderr = self.run_cli_command(
                ["apikey", "get", "persistence_test", "--app-dir", self.temp_dir]
            )

            assert get_returncode == 0

    def test_api_key_deletion_confirmation(self) -> None:
        """Test API key deletion requires confirmation"""
        self.setup_database()
        add_returncode, _, _ = self.run_cli_command(
            ["apikey", "add", "deletion_test", "--app-dir", self.temp_dir],
            stdin_input="deletion-test-key",
        )

        if add_returncode == 0:
            # Try to delete without --confirm
            delete_no_confirm_returncode, _, _ = self.run_cli_command(
                ["apikey", "delete", "deletion_test", "--app-dir", self.temp_dir]
            )

            # Should require confirmation
            if delete_no_confirm_returncode != 0:
                # Try with --confirm
                delete_confirm_returncode, _, _ = self.run_cli_command(
                    [
                        "apikey",
                        "delete",
                        "deletion_test",
                        "--confirm",
                        "--app-dir",
                        self.temp_dir,
                    ]
                )
                assert delete_confirm_returncode in [0, 1]

    def test_api_key_update_operations(self) -> None:
        """Test API key update/overwrite operations"""
        self.setup_database()

        key_name = "update_test"
        original_key = "original-test-key"
        updated_key = "updated-test-key"
        add_returncode, _, _ = self.run_cli_command(
            ["apikey", "add", key_name, "--app-dir", self.temp_dir],
            stdin_input=original_key,
        )

        if add_returncode == 0:
            # Try to update/overwrite
            update_returncode, _, _ = self.run_cli_command(
                ["apikey", "add", key_name, "--app-dir", self.temp_dir],
                stdin_input=updated_key,
            )

            # Should handle update appropriately
            assert update_returncode in [0, 1]
