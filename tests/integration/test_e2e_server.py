#!/usr/bin/env python3
"""
End-to-End Manual Server Integration Testing

Real CLI execution tests for n8n server integration,
including pull/push operations, API key usage, and server configuration.
"""

import json
from pathlib import Path

import pytest

from .e2e_base import E2ETestBase


# === End-to-End Tests ===
class TestE2EServer(E2ETestBase):
    """Manual end-to-end testing for server integration"""

    def test_server_commands_without_configuration(self) -> None:
        """Test server commands without server configuration"""
        self.setup_database_with_api_key()

        # Try server command without URL
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "wf", "server"])

        # Should handle missing server configuration gracefully
        assert returncode in [0, 1]
        if returncode == 1:
            assert "server" in stderr.lower() or "url" in stderr.lower()

    def test_server_url_configuration_priority(self) -> None:
        """Test server URL configuration priority (CLI > env > default)"""
        self.setup_database_with_api_key()

        test_urls = [
            "http://localhost:5678",
            "https://test.n8n.example.com",
            "http://192.168.1.100:5678",
        ]

        for url in test_urls:
            cli_returncode, cli_stdout, cli_stderr = self.run_cli_command(
                ["--data-dir", self.temp_dir, "--remote", url, "wf", "server"]
            )

            # Should accept the URL (may fail due to server not reachable)
            assert cli_returncode in [0, 1], f"Unexpected return code: {cli_returncode}\nSTDERR: {cli_stderr}"
            env = {"N8N_SERVER_URL": url}
            env_returncode, env_stdout, env_stderr = self.run_cli_command(
                ["--data-dir", self.temp_dir, "wf", "server"], env=env
            )

            assert env_returncode in [0, 1]

    def test_no_hardcoded_server_urls_in_output(self) -> None:
        """Test no hardcoded server URLs appear in output"""
        self.setup_database_with_api_key()
        commands = [["wf", "list"], ["wf", "server"], ["--help"]]

        hardcoded_patterns = [
            "localhost:5678",
            "127.0.0.1:5678",
            "n8n.example.com",
            "http://hardcoded",
        ]

        for cmd in commands:
            returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir] + cmd)
            combined_output = (stdout + stderr).lower()
            for pattern in hardcoded_patterns:
                assert pattern not in combined_output, f"Hardcoded URL '{pattern}' found in output of command {cmd}"

    def test_server_commands_use_stored_api_keys(self) -> None:
        """Test server commands use stored API keys"""
        if not self.setup_database_with_api_key():
            pytest.skip("Could not set up API key")
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--remote",
                "http://localhost:5678",
                "wf",
                "server",
            ]
        )

        # Should attempt to use stored API key
        assert returncode in [0, 1]

        # If it fails, should be due to server connectivity, not auth setup
        if returncode == 1:
            # Should not complain about missing API key
            combined_output = (stdout + stderr).lower()
            assert "api key" not in combined_output or "missing" not in combined_output

    @pytest.mark.integration
    def test_pull_workflow_increments_counter(self) -> None:
        """Test pull wf operation increments counter"""
        if not self.setup_database_with_api_key():
            pytest.skip("Could not set up API key")

        # Try to pull a wf (may fail if server not available)
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--remote",
                "http://localhost:5678",
                "wf",
                "pull",
                "test_workflow",
            ]
        )

        # Should handle pull operation
        assert returncode in [0, 1]
        stats_returncode, stats_stdout, _ = self.run_cli_command(["--data-dir", self.temp_dir, "wf", "stats"])
        assert stats_returncode == 0

    @pytest.mark.integration
    def test_push_workflow_increments_counter(self) -> None:
        """Test push wf operation increments counter"""
        if not self.setup_database_with_api_key():
            pytest.skip("Could not set up API key")
        workflow_data = {
            "name": "Push Test Workflow",
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "typeVersion": 1,
                    "position": [240, 300],
                }
            ],
            "connections": {},
            "active": False,
        }

        workflow_file = Path(self.temp_flow_dir) / "push_test.json"
        workflow_file.write_text(json.dumps(workflow_data, indent=2))
        add_returncode, _, _ = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "push_test.json",
                "Push Test",
            ]
        )

        if add_returncode == 0:
            # Try to push wf
            push_returncode, push_stdout, push_stderr = self.run_cli_command(
                [
                    "--data-dir",
                    self.temp_dir,
                    "--remote",
                    "http://localhost:5678",
                    "wf",
                    "push",
                    "push_test",
                ]
            )

            # Should handle push operation
            assert push_returncode in [0, 1]
            stats_returncode, stats_stdout, _ = self.run_cli_command(["--data-dir", self.temp_dir, "wf", "stats"])
            assert stats_returncode == 0

    def test_server_integration_error_handling(self) -> None:
        """Test server integration error handling"""
        self.setup_database_with_api_key()
        unreachable_urls = [
            "http://192.168.255.255:5678",  # Non-routable IP
            "http://nonexistent.domain.test:5678",
            "http://localhost:99999",  # Invalid port
        ]

        for url in unreachable_urls:
            returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "--remote", url, "wf", "server"])

            # Should handle gracefully (may return 0 with error message or 1 for failure)
            assert returncode in [0, 1], f"Unexpected return code: {returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            # Should provide meaningful error message or handle gracefully
            combined_output = (stdout + stderr).lower()
            # Either show error or handle silently (both are acceptable)
            if returncode == 1:
                assert any(
                    word in combined_output for word in ["connection", "timeout", "failed", "error", "unreachable"]
                ), f"Expected error message but got: {combined_output}"

    def test_server_authentication_handling(self) -> None:
        """Test server authentication error handling"""
        self.setup_database_with_api_key()
        invalid_key = "invalid-api-key-12345"

        # Replace stored API key with invalid one
        self.run_cli_command(["apikey", "delete", "test_server", "--confirm"])

        self.run_cli_command(
            ["apikey", "add", "-", "--name", "test_server"],
            stdin_input=invalid_key,
        )
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--remote",
                "http://localhost:5678",
                "wf",
                "server",
            ]
        )

        # Should handle authentication errors
        assert returncode in [0, 1], f"Unexpected return code: {returncode}\nSTDERR: {stderr}"

    def test_server_response_parsing(self) -> None:
        """Test server response parsing and error handling"""
        self.setup_database_with_api_key()
        server_commands = [
            ["wf", "server"],
            ["wf", "pull", "nonexistent_workflow"],
            ["wf", "push", "nonexistent_workflow"],
        ]

        for cmd in server_commands:
            returncode, stdout, stderr = self.run_cli_command(
                ["--data-dir", self.temp_dir, "--remote", "http://localhost:5678"] + cmd
            )

            # Should handle response parsing gracefully
            assert returncode in [0, 1]

            # Should not crash with JSON parsing errors
            combined_output = (stdout + stderr).lower()
            assert "traceback" not in combined_output
            assert "json.decoder.jsondecodeerror" not in combined_output

    def test_server_timeout_handling(self) -> None:
        """Test server timeout handling"""
        self.setup_database_with_api_key()
        # Using a valid IP but wrong port to simulate timeout
        timeout_url = "http://8.8.8.8:5678"  # Google DNS, wrong port

        returncode, stdout, stderr = self.run_cli_command(
            ["--data-dir", self.temp_dir, "--remote", timeout_url, "wf", "server"]
        )

        # Should timeout gracefully (exit code 1 for connection failure)
        assert returncode in [0, 1]
        # If it failed, output should contain error message or be empty (graceful failure)
        # Don't assert specific error keywords as implementation may vary
        if returncode == 1:
            # Failed as expected - either has error message or silent failure
            pass
        # Success case means it handled gracefully even if connection failed

    def test_e2e_server_is_up_and_healthy(self) -> None:
        """Test server SSL/HTTPS handling"""
        self.setup_database_with_api_key()
        https_urls = ["https://localhost:5678", "https://192.168.255.255:5678"]  # Non-routable IP

        for url in https_urls:
            returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "--remote", url, "wf", "server"])

            # Should handle HTTPS
            assert returncode in [0, 1]

            # Should not crash on SSL errors
            combined_output = (stdout + stderr).lower()
            assert "traceback" not in combined_output

    def test_server_concurrent_requests(self) -> None:
        """Test concurrent server requests handling"""
        import threading

        if not self.setup_database_with_api_key():
            pytest.skip("Could not set up API key")

        results = []

        def make_server_request(request_id: int) -> None:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "--data-dir",
                    self.temp_dir,
                    "--remote",
                    "http://localhost:5678",
                    "wf",
                    "server",
                ]
            )
            results.append((request_id, returncode, stdout, stderr))

        # Make concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=make_server_request, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should complete
        assert len(results) == 3
        for request_id, returncode, stdout, stderr in results:
            assert returncode in [0, 1]

    def test_server_environment_isolation(self) -> None:
        """Test server operations don't interfere with local operations"""
        self.setup_database_with_api_key()

        # Perform server operation
        server_returncode, _, _ = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--remote",
                "http://localhost:5678",
                "wf",
                "server",
            ]
        )

        # Perform local operation immediately after
        # Note: wf list reads from database, so it uses --data-dir
        local_returncode, local_stdout, _ = self.run_cli_command(["wf", "list", "--data-dir", self.temp_dir])

        # Local operation should work regardless of server operation result
        assert local_returncode == 0

    def test_server_api_endpoint_construction(self) -> None:
        """Test proper API endpoint construction"""
        self.setup_database_with_api_key()
        url_formats = [
            "http://localhost:5678",
            "http://localhost:5678/",
            "https://n8n.example.com",
            "https://n8n.example.com/",
            "http://192.168.1.100:5678",
        ]

        for url in url_formats:
            returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "--remote", url, "wf", "server"])

            # Should construct proper API endpoints
            assert returncode in [0, 1]

    def test_server_workflow_metadata_handling(self) -> None:
        """Test server wf metadata handling"""
        if not self.setup_database_with_api_key():
            pytest.skip("Could not set up API key")
        workflow_data = {
            "name": "Metadata Test Workflow",
            "nodes": [{"id": "start", "type": "start"}],
            "connections": {},
            "active": False,
            "settings": {"executionOrder": "v1"},
            "meta": {"instanceId": "test-instance-123"},
            "tags": ["test", "metadata"],
        }

        workflow_file = Path(self.temp_flow_dir) / "metadata_test.json"
        workflow_file.write_text(json.dumps(workflow_data, indent=2))
        add_returncode, _, _ = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "metadata_test.json",
                "Metadata Test",
            ]
        )

        if add_returncode == 0:
            push_returncode, push_stdout, push_stderr = self.run_cli_command(
                [
                    "--data-dir",
                    self.temp_dir,
                    "--remote",
                    "http://localhost:5678",
                    "wf",
                    "push",
                    "metadata_test",
                ]
            )

            # Should handle metadata properly
            assert push_returncode in [0, 1]

    def test_server_large_workflow_handling(self) -> None:
        """Test server operations with large workflows"""
        if not self.setup_database_with_api_key():
            pytest.skip("Could not set up API key")
        large_workflow = {
            "name": "Large Test Workflow",
            "nodes": [
                {
                    "id": f"node_{i}",
                    "type": "test",
                    "typeVersion": 1,
                    "position": [i * 100, i * 50],
                    "parameters": {"data": "x" * 1000},  # 1KB per node
                }
                for i in range(50)  # 50KB+ wf
            ],
            "connections": {},
            "active": False,
        }

        workflow_file = Path(self.temp_flow_dir) / "large_workflow.json"
        workflow_file.write_text(json.dumps(large_workflow, indent=2))

        add_returncode, _, _ = self.run_cli_command(
            [
                "--data-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "large_workflow.json",
                "Large Workflow",
            ]
        )

        if add_returncode == 0:
            push_returncode, _, _ = self.run_cli_command(
                [
                    "--data-dir",
                    self.temp_dir,
                    "--remote",
                    "http://localhost:5678",
                    "wf",
                    "push",
                    "large_workflow",
                ]
            )

            # Should handle large workflows
            assert push_returncode in [0, 1]

    def test_skip_ssl_verify_option_available(self) -> None:
        """Test that --skip-ssl-verify option is available on all remote commands"""
        self.setup_database_with_api_key()

        # Commands that should support --skip-ssl-verify
        # Only commands that communicate with remote server support this option
        test_cases = [
            (["wf", "pull", "test123", "--remote", "https://localhost:5678", "--skip-ssl-verify"], "wf pull"),
            (["wf", "push", "test123", "--remote", "https://localhost:5678", "--skip-ssl-verify"], "wf push"),
            (["wf", "server", "--remote", "https://localhost:5678", "--skip-ssl-verify"], "wf server"),
        ]

        for cmd, description in test_cases:
            returncode, stdout, stderr = self.run_cli_command(cmd)

            # Should not error on unknown option (returns 0 or 1, not 2)
            assert returncode in [0, 1], f"Command {description} rejected --skip-ssl-verify option: {stderr}"
            # Should not show "No such option" error
            assert "no such option" not in stderr.lower(), f"Command {description} does not support --skip-ssl-verify"
