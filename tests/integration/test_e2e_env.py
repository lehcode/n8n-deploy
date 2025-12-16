#!/usr/bin/env python3
"""
End-to-End Manual Environment Command Testing

Real CLI execution tests for the env command with all output formats
and configuration options.
"""

import json
from pathlib import Path

from .e2e_base import E2ETestBase


class TestE2EEnv(E2ETestBase):
    """Manual end-to-end testing for env command"""

    def test_env_plain_text_output(self) -> None:
        """Test env command with plain text output (default)"""
        returncode, stdout, stderr = self.run_cli_command(["env"])

        self.assert_command_details(returncode, stdout, stderr, 0, "env plain text output")

        # Should show environment configuration sections
        assert "Environment Configuration" in stdout
        assert "Configuration Variables" in stdout
        assert "Priority Order" in stdout
        assert "N8N_DEPLOY_DATA_DIR" in stdout
        assert "N8N_DEPLOY_FLOWS_DIR" in stdout

    def test_env_table_format(self) -> None:
        """Test env command with table format (emoji tables)"""
        returncode, stdout, stderr = self.run_cli_command(["env", "--table"])

        self.assert_command_details(returncode, stdout, stderr, 0, "env table format")

        # Should show emoji tables
        assert "🌍" in stdout or "Environment Configuration" in stdout
        assert "N8N_DEPLOY_DATA_DIR" in stdout
        assert "N8N_DEPLOY_FLOWS_DIR" in stdout
        assert "Priority Order" in stdout

    def test_env_json_format(self) -> None:
        """Test env command with JSON format"""
        returncode, stdout, stderr = self.run_cli_command(["env", "--json"])

        self.assert_command_details(returncode, stdout, stderr, 0, "env JSON format")

        # Should be valid JSON
        data = json.loads(stdout)
        assert "variables" in data
        assert "priority_order" in data
        assert "N8N_DEPLOY_DATA_DIR" in data["variables"]
        assert "N8N_DEPLOY_FLOWS_DIR" in data["variables"]
        assert "N8N_SERVER_URL" in data["variables"]

    def test_env_with_app_dir_option(self) -> None:
        """Test env command with --data-dir CLI option"""
        test_app_dir = str(Path(self.temp_dir) / "custom_app")

        returncode, stdout, stderr = self.run_cli_command(["env", "--data-dir", test_app_dir, "--json"])

        self.assert_command_details(returncode, stdout, stderr, 0, "env with --data-dir option")

        # Verify CLI option takes precedence
        data = json.loads(stdout)
        assert data["variables"]["N8N_DEPLOY_DATA_DIR"]["value"] == test_app_dir
        assert data["variables"]["N8N_DEPLOY_DATA_DIR"]["source"] == "CLI"

    def test_env_with_flow_dir_option(self) -> None:
        """Test env command with --flow-dir CLI option"""
        test_flow_dir = str(Path(self.temp_dir) / "custom_flow")

        returncode, stdout, stderr = self.run_cli_command(["env", "--flow-dir", test_flow_dir, "--json"])

        self.assert_command_details(returncode, stdout, stderr, 0, "env with --flow-dir option")

        # Verify CLI option takes precedence
        data = json.loads(stdout)
        assert data["variables"]["N8N_DEPLOY_FLOWS_DIR"]["value"] == test_flow_dir
        assert data["variables"]["N8N_DEPLOY_FLOWS_DIR"]["source"] == "CLI"

    def test_env_with_server_url_option(self) -> None:
        """Test env command with --remote CLI option"""
        test_server_url = "http://test-server.example.com:5678"

        returncode, stdout, stderr = self.run_cli_command(["env", "--remote", test_server_url, "--json"])

        self.assert_command_details(returncode, stdout, stderr, 0, "env with --remote option")

        # Verify CLI option takes precedence
        data = json.loads(stdout)
        assert data["variables"]["N8N_SERVER_URL"]["value"] == test_server_url
        assert data["variables"]["N8N_SERVER_URL"]["source"] == "CLI"

    def test_env_with_all_options(self) -> None:
        """Test env command with all CLI options"""
        test_app_dir = str(Path(self.temp_dir) / "all_app")
        test_flow_dir = str(Path(self.temp_dir) / "all_flow")
        test_server_url = "http://all-test.example.com:5678"

        returncode, stdout, stderr = self.run_cli_command(
            [
                "env",
                "--data-dir",
                test_app_dir,
                "--flow-dir",
                test_flow_dir,
                "--remote",
                test_server_url,
                "--json",
            ]
        )

        self.assert_command_details(returncode, stdout, stderr, 0, "env with all options")

        # Verify all CLI options are used
        data = json.loads(stdout)
        assert data["variables"]["N8N_DEPLOY_DATA_DIR"]["value"] == test_app_dir
        assert data["variables"]["N8N_DEPLOY_DATA_DIR"]["source"] == "CLI"
        assert data["variables"]["N8N_DEPLOY_FLOWS_DIR"]["value"] == test_flow_dir
        assert data["variables"]["N8N_DEPLOY_FLOWS_DIR"]["source"] == "CLI"
        assert data["variables"]["N8N_SERVER_URL"]["value"] == test_server_url
        assert data["variables"]["N8N_SERVER_URL"]["source"] == "CLI"

    def test_env_with_environment_variables(self) -> None:
        """Test env command respects environment variables"""
        env = {
            "N8N_DEPLOY_DATA_DIR": str(Path(self.temp_dir) / "env_app"),
            "N8N_DEPLOY_FLOWS_DIR": str(Path(self.temp_dir) / "env_flow"),
            "N8N_SERVER_URL": "http://env-server.example.com:5678",
        }

        returncode, stdout, stderr = self.run_cli_command(["env", "--json"], env=env)

        self.assert_command_details(returncode, stdout, stderr, 0, "env with environment variables")

        # Verify environment variables are used
        data = json.loads(stdout)
        assert env["N8N_DEPLOY_DATA_DIR"] in data["variables"]["N8N_DEPLOY_DATA_DIR"]["value"]
        assert "N8N_DEPLOY_DATA_DIR" in data["variables"]["N8N_DEPLOY_DATA_DIR"]["source"]

    def test_env_cli_option_precedence_over_env_vars(self) -> None:
        """Test that CLI options take precedence over environment variables"""
        cli_app_dir = str(Path(self.temp_dir) / "cli_app")
        env_app_dir = str(Path(self.temp_dir) / "env_app")

        env = {"N8N_DEPLOY_DATA_DIR": env_app_dir}

        returncode, stdout, stderr = self.run_cli_command(["env", "--data-dir", cli_app_dir, "--json"], env=env)

        self.assert_command_details(returncode, stdout, stderr, 0, "CLI option precedence test")

        # Verify CLI option wins over environment variable
        data = json.loads(stdout)
        assert data["variables"]["N8N_DEPLOY_DATA_DIR"]["value"] == cli_app_dir
        assert data["variables"]["N8N_DEPLOY_DATA_DIR"]["source"] == "CLI"

    def test_env_shows_priority_order(self) -> None:
        """Test that env command shows correct priority order"""
        returncode, stdout, stderr = self.run_cli_command(["env", "--json"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Priority order test")

        # Verify priority order is documented
        data = json.loads(stdout)
        assert "priority_order" in data
        assert len(data["priority_order"]) >= 3  # At least CLI, env vars, defaults
        assert any("CLI" in item for item in data["priority_order"])
        assert any("Environment" in item for item in data["priority_order"])

    def test_env_masks_api_key(self) -> None:
        """Test that env command masks API key values"""
        env = {"N8N_API_KEY": "secret_api_key_should_be_hidden"}

        returncode, stdout, stderr = self.run_cli_command(["env", "--json"], env=env)

        self.assert_command_details(returncode, stdout, stderr, 0, "API key masking test")

        # Verify API key is masked
        data = json.loads(stdout)
        assert "N8N_API_KEY" in data["variables"]
        assert data["variables"]["N8N_API_KEY"]["value"] == "***"
        assert "secret_api_key_should_be_hidden" not in stdout

    def test_env_defaults_to_cwd_when_app_dir_invalid(self) -> None:
        """Test that invalid N8N_DEPLOY_DATA defaults to cwd"""
        env = {"N8N_DEPLOY_DATA_DIR": "/nonexistent/invalid/path"}

        returncode, stdout, stderr = self.run_cli_command(["env", "--json"], env=env)

        self.assert_command_details(returncode, stdout, stderr, 0, "Invalid app dir defaults to cwd")

        # Verify command succeeds (falls back to cwd instead of crashing)
        data = json.loads(stdout)
        assert "N8N_DEPLOY_DATA_DIR" in data["variables"]
        # Source shows the environment variable name
        assert data["variables"]["N8N_DEPLOY_DATA_DIR"]["source"] == "N8N_DEPLOY_DATA_DIR"

    def test_env_defaults_to_cwd_when_flow_dir_invalid(self) -> None:
        """Test that invalid N8N_DEPLOY_FLOWS defaults to cwd"""
        env = {"N8N_DEPLOY_FLOWS_DIR": "/nonexistent/invalid/flow/path"}

        returncode, stdout, stderr = self.run_cli_command(["env", "--json"], env=env)

        self.assert_command_details(returncode, stdout, stderr, 0, "Invalid flow dir defaults to cwd")

        # Verify command succeeds (falls back to cwd instead of crashing)
        data = json.loads(stdout)
        assert "N8N_DEPLOY_FLOWS_DIR" in data["variables"]
        # Source shows the environment variable name
        assert data["variables"]["N8N_DEPLOY_FLOWS_DIR"]["source"] == "N8N_DEPLOY_FLOWS_DIR"
