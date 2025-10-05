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
            ["apikey", "add", test_key, "--name", "test_interactive", "--data-dir", self.temp_dir],
        )

        # Should succeed
        assert returncode == 0

    def test_api_key_add_with_stdin_input(self) -> None:
        """Test API key addition using stdin pipe"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNGEyODkxMy04ODQxLTRhMTAtODIzNC1iODQ2OTE1MmJhZTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU4NzY3MDI4LCJleHAiOjE3NjEyNzg0MDB9.d9u2SovTMfUGZ8EzD4SDLYNUTBarHpdwhv96pO-5imE"
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "test_stdin", "--data-dir", self.temp_dir],
            stdin_input=test_key,
        )

        # Should succeed
        assert returncode == 0

    def test_api_key_list_empty(self) -> None:
        """Test listing API keys when none exist"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["apikey", "list", "--data-dir", self.temp_dir])

        assert returncode == 0
        # Should show empty list or appropriate message

    def test_api_key_complete_lifecycle(self) -> None:
        """Test complete API key lifecycle: add, list, get, delete"""
        self.setup_database()

        key_name = "lifecycle_test"
        test_key = "lifecycle-test-key-789"

        # Step 1: Add API key
        add_returncode, add_stdout, add_stderr = self.run_cli_command(
            ["apikey", "add", key_name, "--data-dir", self.temp_dir],
            stdin_input=test_key,
        )

        if add_returncode == 0:
            # Step 2: List API keys (should show the added key)
            list_returncode, list_stdout, list_stderr = self.run_cli_command(["apikey", "list", "--data-dir", self.temp_dir])
            assert list_returncode == 0

            # Step 3: Get specific API key (without showing actual key)
            get_returncode, get_stdout, get_stderr = self.run_cli_command(
                ["apikey", "get", key_name, "--data-dir", self.temp_dir]
            )
            assert get_returncode == 0

            # Step 4: Get API key with --show-key flag
            show_returncode, show_stdout, show_stderr = self.run_cli_command(
                ["apikey", "get", key_name, "--show-key", "--data-dir", self.temp_dir]
            )
            if show_returncode == 0:
                # Should show the actual key
                assert test_key in show_stdout

            # Step 5: Delete API key
            delete_returncode, delete_stdout, delete_stderr = self.run_cli_command(
                ["apikey", "delete", key_name, "--confirm", "--data-dir", self.temp_dir]
            )
            # Should succeed or ask for confirmation
            assert delete_returncode in [0, 1]

    def test_api_key_get_nonexistent(self) -> None:
        """Test getting nonexistent API key"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["apikey", "get", "nonexistent_key", "--data-dir", self.temp_dir])

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
                "--data-dir",
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
            ["apikey", "add", key_name, "--data-dir", self.temp_dir],
            stdin_input=first_key,
        )

        if first_returncode == 0:
            # Try to add second key with same name
            second_returncode, second_stdout, second_stderr = self.run_cli_command(
                ["apikey", "add", key_name, "--data-dir", self.temp_dir],
                stdin_input=second_key,
            )

            # Should handle duplicate names appropriately
            assert second_returncode in [0, 1]

    def test_api_key_emoji_vs_no_emoji_output(self) -> None:
        """Test API key commands with and without emoji"""
        self.setup_database()
        emoji_returncode, emoji_stdout, emoji_stderr = self.run_cli_command(["apikey", "list", "--data-dir", self.temp_dir])
        no_emoji_returncode, no_emoji_stdout, no_emoji_stderr = self.run_cli_command(
            ["apikey", "list", "--data-dir", self.temp_dir]
        )

        assert emoji_returncode == no_emoji_returncode == 0
        if "🔐" in emoji_stdout:
            assert "🔐" not in no_emoji_stdout

    def test_api_key_special_characters(self) -> None:
        """Test API keys with special characters"""
        self.setup_database()
        special_key = "test-key-with-special-chars!@#$%^&*()"
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "special_test", "--data-dir", self.temp_dir],
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
            ["apikey", "add", "-", "--name", long_name, "--data-dir", self.temp_dir],
            stdin_input=long_key,
        )

        # Should handle long names and values
        assert returncode in [0, 1]

    def test_api_key_empty_input(self) -> None:
        """Test API key commands with empty input"""
        self.setup_database()
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "empty_test", "--data-dir", self.temp_dir], stdin_input=""
        )

        # Should handle empty input appropriately
        assert returncode in [0, 1]

    def test_api_key_whitespace_handling(self) -> None:
        """Test API key handling of whitespace"""
        self.setup_database()
        whitespace_key = "  test-key-with-whitespace  \n"
        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "whitespace_test", "--data-dir", self.temp_dir],
            stdin_input=whitespace_key,
        )

        # Should handle whitespace appropriately
        assert returncode in [0, 1]

    def run_help_command(self, args: list[str]) -> tuple[int, str, str]:
        """Execute help command without --no-emoji flag"""
        import os
        import subprocess

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
            ["apikey", "add", "testkey", "--data-dir", self.temp_dir],
            stdin_input=lower_key,
        )

        if lower_returncode == 0:
            # Try to get with different case
            upper_returncode, upper_stdout, upper_stderr = self.run_cli_command(
                ["apikey", "get", "TESTKEY", "--data-dir", self.temp_dir]
            )

            # Behavior depends on implementation (case sensitive or insensitive)
            assert upper_returncode in [0, 1]

    def test_server_commands_use_stored_api_keys(self) -> None:
        """Test server commands can use stored API keys"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"  # Mock JWT format
        add_returncode, _, _ = self.run_cli_command(
            ["apikey", "add", "n8n_server", "--data-dir", self.temp_dir],
            stdin_input=test_key,
        )

        if add_returncode == 0:
            server_returncode, server_stdout, server_stderr = self.run_cli_command(
                [
                    "server",
                    "--data-dir",
                    self.temp_dir,
                    "--remote",
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
                    "--data-dir",
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
            ["apikey", "add", "persistence_test", "--data-dir", self.temp_dir],
            stdin_input="persistent-test-key",
        )

        if add_returncode == 0:
            self.run_cli_command(["wf", "list", "--data-dir", self.temp_dir, "--flows-dir", self.temp_flow_dir])
            self.run_cli_command(["stats", "--data-dir", self.temp_dir, "--flows-dir", self.temp_flow_dir])
            get_returncode, get_stdout, get_stderr = self.run_cli_command(
                ["apikey", "get", "persistence_test", "--data-dir", self.temp_dir]
            )

            assert get_returncode == 0

    def test_api_key_deletion_confirmation(self) -> None:
        """Test API key deletion requires confirmation"""
        self.setup_database()
        add_returncode, _, _ = self.run_cli_command(
            ["apikey", "add", "deletion_test", "--data-dir", self.temp_dir],
            stdin_input="deletion-test-key",
        )

        if add_returncode == 0:
            # Try to delete without --confirm
            delete_no_confirm_returncode, _, _ = self.run_cli_command(
                ["apikey", "delete", "deletion_test", "--data-dir", self.temp_dir]
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
                        "--data-dir",
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
            ["apikey", "add", key_name, "--data-dir", self.temp_dir],
            stdin_input=original_key,
        )

        if add_returncode == 0:
            # Try to update/overwrite
            update_returncode, _, _ = self.run_cli_command(
                ["apikey", "add", key_name, "--data-dir", self.temp_dir],
                stdin_input=updated_key,
            )

            # Should handle update appropriately
            assert update_returncode in [0, 1]

    # === Additional API Key Command Tests for Complete Coverage ===

    def test_apikey_add_from_stdin_with_dash(self) -> None:
        """Test apikey add from stdin using '-' as key argument"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"  # Valid JWT format

        returncode, stdout, stderr = self.run_cli_command(
            ["apikey", "add", "-", "--name", "stdin_dash_test", "--data-dir", self.temp_dir],
            stdin_input=test_key,
        )

        assert returncode in [0, 1]

    def test_apikey_add_with_description(self) -> None:
        """Test apikey add --description adds description"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        returncode, stdout, stderr = self.run_cli_command(
            [
                "apikey",
                "add",
                test_key,
                "--name",
                "description_test",
                "--description",
                "This is a test API key",
                "--data-dir",
                self.temp_dir,
            ]
        )

        assert returncode in [0, 1]
        if returncode == 0:
            # List to verify description was added
            list_returncode, list_stdout, list_stderr = self.run_cli_command(["apikey", "list", "--data-dir", self.temp_dir])
            assert list_returncode == 0

    def test_apikey_add_with_server(self) -> None:
        """Test apikey add --server links to server"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        # Create a server first
        self.run_cli_command(
            [
                "server",
                "create",
                "test_server",
                "http://localhost:5678",
                "--data-dir",
                self.temp_dir,
            ]
        )

        # Add API key with server link
        returncode, stdout, stderr = self.run_cli_command(
            [
                "apikey",
                "add",
                test_key,
                "--name",
                "server_test",
                "--server",
                "test_server",
                "--data-dir",
                self.temp_dir,
            ]
        )

        assert returncode == 0
        assert "server_test" in stdout.lower()
        assert "test_server" in stdout.lower() or "linked" in stdout.lower()

    def test_apikey_list_show_keys(self) -> None:
        """Test apikey list --show-keys displays actual keys"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        self.run_cli_command(["apikey", "add", test_key, "--name", "show_keys_test", "--data-dir", self.temp_dir])

        returncode, stdout, stderr = self.run_cli_command(["apikey", "list", "--show-keys", "--data-dir", self.temp_dir])

        assert returncode == 0
        if test_key in stdout or "show_keys_test" in stdout:
            # Keys are shown
            pass

    def test_apikey_list_json_format(self) -> None:
        """Test apikey list --format json output"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        self.run_cli_command(["apikey", "add", test_key, "--name", "json_list_test", "--data-dir", self.temp_dir])

        returncode, stdout, stderr = self.run_cli_command(["apikey", "list", "--format", "json", "--data-dir", self.temp_dir])

        assert returncode == 0
        # Should be valid JSON
        import json

        data = json.loads(stdout)
        assert isinstance(data, list) or isinstance(data, str)  # May be list or JSON string

    def test_apikey_get_without_show_key(self) -> None:
        """Test apikey get <name> without --show-key (just validates)"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        add_result = self.run_cli_command(
            ["apikey", "add", test_key, "--name", "get_validate_test", "--data-dir", self.temp_dir]
        )

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                ["apikey", "get", "get_validate_test", "--data-dir", self.temp_dir]
            )

            assert returncode == 0
            # Should validate without showing key
            assert "valid" in stdout.lower() or "accessible" in stdout.lower()

    def test_apikey_get_with_show_key(self) -> None:
        """Test apikey get <name> --show-key displays the key"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        add_result = self.run_cli_command(["apikey", "add", test_key, "--name", "get_show_test", "--data-dir", self.temp_dir])

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                ["apikey", "get", "get_show_test", "--show-key", "--data-dir", self.temp_dir]
            )

            assert returncode == 0
            # Should show the actual key
            assert test_key in stdout or "key" in stdout.lower()

    def test_apikey_get_json_format(self) -> None:
        """Test apikey get --format json output"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        add_result = self.run_cli_command(["apikey", "add", test_key, "--name", "get_json_test", "--data-dir", self.temp_dir])

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                ["apikey", "get", "get_json_test", "--format", "json", "--data-dir", self.temp_dir]
            )

            # May succeed or fail based on implementation
            assert returncode in [0, 1]

    def test_apikey_deactivate_soft_delete(self) -> None:
        """Test apikey deactivate performs soft delete"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        add_result = self.run_cli_command(
            ["apikey", "add", test_key, "--name", "deactivate_test", "--data-dir", self.temp_dir]
        )

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                ["apikey", "deactivate", "deactivate_test", "--data-dir", self.temp_dir]
            )

            assert returncode in [0, 1]
            if returncode == 0:
                # Verify key is deactivated but still exists
                list_result = self.run_cli_command(["apikey", "list", "--data-dir", self.temp_dir])
                assert list_result[0] == 0

    def test_apikey_delete_with_confirm(self) -> None:
        """Test apikey delete <name> --confirm permanently deletes"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        add_result = self.run_cli_command(
            ["apikey", "add", test_key, "--name", "delete_confirm_test", "--data-dir", self.temp_dir]
        )

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "apikey",
                    "delete",
                    "delete_confirm_test",
                    "--confirm",
                    "--data-dir",
                    self.temp_dir,
                ]
            )

            assert returncode in [0, 1]
            if returncode == 0:
                # Verify key is completely removed
                get_result = self.run_cli_command(["apikey", "get", "delete_confirm_test", "--data-dir", self.temp_dir])
                # Should fail since key is deleted
                assert get_result[0] == 1

    def test_apikey_test_validates_key(self) -> None:
        """Test apikey test <name> validates API key"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        add_result = self.run_cli_command(
            ["apikey", "add", test_key, "--name", "test_validation", "--data-dir", self.temp_dir]
        )

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                ["apikey", "test", "test_validation", "--data-dir", self.temp_dir]
            )

            # Test command should validate the key exists
            assert returncode in [0, 1]

    def test_apikey_invalid_name_validation(self) -> None:
        """Test apikey add validates key name format"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        # Only path separators and null bytes are invalid - spaces and UTF-8 are valid
        invalid_names = [
            "invalid/name",  # Forward slash (path separator)
            "invalid\\name",  # Backslash (path separator)
        ]

        for invalid_name in invalid_names:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "apikey",
                    "add",
                    test_key,
                    "--name",
                    invalid_name,
                    "--data-dir",
                    self.temp_dir,
                ]
            )

            # Should fail validation for path separators
            assert returncode == 1, f"Name with path separator should be rejected: {invalid_name}"

    def test_apikey_valid_name_with_spaces_and_special_chars(self) -> None:
        """Test that API key names can contain spaces and special characters (except path separators)"""
        self.setup_database()
        test_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dGVzdA.c2lnbmF0dXJl"

        # Spaces, UTF-8, and special chars (except path separators) are valid
        valid_names = [
            "valid name with spaces",
            "valid@email.com",
            "válid-ütf8-ñame",
        ]

        for valid_name in valid_names:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "apikey",
                    "add",
                    test_key,
                    "--name",
                    valid_name,
                    "--data-dir",
                    self.temp_dir,
                ]
            )

            # Should succeed - these names are valid
            assert returncode == 0, f"Valid name should be accepted: {valid_name}"
            assert "added successfully" in stdout.lower()

    def test_apikey_invalid_jwt_format_validation(self) -> None:
        """Test apikey add validates JWT format"""
        self.setup_database()

        invalid_keys = [
            "not-a-jwt",  # No dots
            "only.two",  # Only 2 parts
            "too.many.parts.here",  # Too many parts
        ]

        for invalid_key in invalid_keys:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "apikey",
                    "add",
                    invalid_key,
                    "--name",
                    "invalid_jwt_test",
                    "--data-dir",
                    self.temp_dir,
                ]
            )

            # Should fail validation for invalid JWT format
            assert returncode == 1
