#!/usr/bin/env python3
"""
API Key test helpers and shared utilities.

Provides ApikeyTestHelpers mixin class with common API key CLI operations
to reduce code duplication across API key E2E tests.
"""

import json
from typing import Optional, Tuple

import pytest

from ..e2e_base import E2ETestBase


class ApikeyTestHelpers(E2ETestBase):
    """Helper methods for API key E2E testing"""

    def run_apikey_add(
        self,
        name: str,
        api_key: str = "",
        data_dir: Optional[str] = None,
        stdin_input: Optional[str] = None,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'apikey add' command with common parameters"""
        args = ["apikey", "add", name]

        if data_dir:
            args.extend(["--data-dir", data_dir])
        if output_json:
            args.append("--json")

        # Use provided stdin_input or construct from api_key
        input_data = stdin_input if stdin_input is not None else f"{api_key}\n"
        return self.run_cli_command(args, stdin_input=input_data)

    def run_apikey_list(
        self,
        data_dir: Optional[str] = None,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'apikey list' command with common parameters"""
        args = ["apikey", "list"]

        if data_dir:
            args.extend(["--data-dir", data_dir])
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_apikey_get(
        self,
        name: str,
        data_dir: Optional[str] = None,
        show_key: bool = False,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'apikey get' command with common parameters"""
        args = ["apikey", "get", name]

        if data_dir:
            args.extend(["--data-dir", data_dir])
        if show_key:
            args.append("--show-key")
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_apikey_delete(
        self,
        name: str,
        data_dir: Optional[str] = None,
        confirm: bool = True,
    ) -> Tuple[int, str, str]:
        """Execute 'apikey delete' command with common parameters"""
        args = ["apikey", "delete", name]

        if data_dir:
            args.extend(["--data-dir", data_dir])
        if confirm:
            args.append("--confirm")

        return self.run_cli_command(args)

    def run_apikey_deactivate(
        self,
        name: str,
        data_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Execute 'apikey deactivate' command with common parameters"""
        args = ["apikey", "deactivate", name]

        if data_dir:
            args.extend(["--data-dir", data_dir])

        return self.run_cli_command(args)

    def assert_apikey_in_list(self, api_key_name: str, stdout: str, should_exist: bool = True) -> None:
        """Assert whether an API key appears in list output"""
        if should_exist:
            assert api_key_name in stdout, f"API key '{api_key_name}' not found in list output"
        else:
            assert api_key_name not in stdout, f"API key '{api_key_name}' should not be in list output"

    def assert_json_output_valid(self, stdout: str) -> dict:
        """Assert stdout contains valid JSON and return parsed data"""
        try:
            data = json.loads(stdout)
            return data
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput: {stdout}")

    def create_test_api_key(self, name: str = "test_key", api_key: str = "test-api-key-12345") -> Tuple[int, str, str]:
        """Helper to create a test API key"""
        return self.run_apikey_add(name, api_key, data_dir=self.temp_dir)
