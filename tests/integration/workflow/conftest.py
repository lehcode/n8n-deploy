#!/usr/bin/env python3
"""
Workflow test helpers and shared utilities.

Provides WorkflowTestHelpers mixin class with common workflow CLI operations
to reduce code duplication across workflow E2E tests.
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from ..e2e_base import E2ETestBase
from tests.helpers import assert_json_output_valid as _assert_json_valid


class WorkflowTestHelpers(E2ETestBase):
    """Helper methods for workflow E2E testing"""

    def run_wf_add(
        self,
        name: str,
        link_remote: Optional[str] = None,
        flow_dir: Optional[str] = None,
        skip_ssl_verify: bool = False,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'wf add' command with common parameters"""
        args = ["wf", "add", name]

        if link_remote:
            args.extend(["--link-remote", link_remote])
        if flow_dir:
            args.extend(["--flow-dir", flow_dir])
        if skip_ssl_verify:
            args.append("--skip-ssl-verify")
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_wf_list(
        self,
        flow_dir: Optional[str] = None,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'wf list' command with common parameters"""
        args = ["wf", "list"]

        if flow_dir:
            args.extend(["--flow-dir", flow_dir])
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_wf_delete(
        self,
        name: str,
        yes_flag: bool = True,
        flow_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Execute 'wf delete' command with common parameters"""
        args = ["wf", "delete", name]

        if yes_flag:
            args.append("--yes")
        if flow_dir:
            args.extend(["--flow-dir", flow_dir])

        return self.run_cli_command(args)

    def run_wf_search(
        self,
        query: str,
        flow_dir: Optional[str] = None,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'wf search' command with common parameters"""
        args = ["wf", "search", query]

        if flow_dir:
            args.extend(["--flow-dir", flow_dir])
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_wf_stats(
        self,
        workflow_name: Optional[str] = None,
        flow_dir: Optional[str] = None,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'wf stats' command with common parameters"""
        args = ["wf", "stats"]

        if workflow_name:
            args.append(workflow_name)
        if flow_dir:
            args.extend(["--flow-dir", flow_dir])
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_wf_backup(
        self,
        workflow_name: Optional[str] = None,
        backup_dir: Optional[str] = None,
        flow_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Execute 'wf backup' command with common parameters"""
        args = ["wf", "backup"]

        if workflow_name:
            args.append(workflow_name)
        if backup_dir:
            args.extend(["--backup-dir", backup_dir])
        if flow_dir:
            args.extend(["--flow-dir", flow_dir])

        return self.run_cli_command(args)

    def run_wf_restore(
        self,
        backup_file: str,
        flow_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Execute 'wf restore' command with common parameters"""
        args = ["wf", "restore", backup_file]

        if flow_dir:
            args.extend(["--flow-dir", flow_dir])

        return self.run_cli_command(args)

    def run_wf_list_backups(
        self,
        flow_dir: Optional[str] = None,
        output_json: bool = False,
    ) -> Tuple[int, str, str]:
        """Execute 'wf list-backups' command with common parameters"""
        args = ["wf", "list-backups"]

        if flow_dir:
            args.extend(["--flow-dir", flow_dir])
        if output_json:
            args.append("--json")

        return self.run_cli_command(args)

    def run_wf_verify_backup(
        self,
        backup_file: str,
        flow_dir: Optional[str] = None,
    ) -> Tuple[int, str, str]:
        """Execute 'wf verify-backup' command with common parameters"""
        args = ["wf", "verify-backup", backup_file]

        if flow_dir:
            args.extend(["--flow-dir", flow_dir])

        return self.run_cli_command(args)

    def create_test_workflow(self, name: str, workflow_data: Optional[dict] = None) -> Path:
        """Create a test workflow file with standard structure"""
        if workflow_data is None:
            workflow_data = {
                "name": name,
                "nodes": [
                    {
                        "id": "node1",
                        "type": "start",
                        "typeVersion": 1,
                        "position": [240, 300],
                    }
                ],
                "connections": {},
                "active": False,
                "settings": {},
                "meta": {"instanceId": "test-instance"},
            }

        workflow_file = Path(self.temp_flow_dir) / f"{name}.json"
        workflow_file.write_text(json.dumps(workflow_data, indent=2))
        return workflow_file

    def assert_workflow_in_list(self, workflow_name: str, stdout: str, should_exist: bool = True) -> None:
        """Assert whether a workflow appears in list output"""
        if should_exist:
            assert workflow_name in stdout, f"Workflow '{workflow_name}' not found in list output"
        else:
            assert workflow_name not in stdout, f"Workflow '{workflow_name}' should not be in list output"

    def assert_json_output_valid(self, stdout: str) -> dict:
        """Assert stdout contains valid JSON and return parsed data"""
        return _assert_json_valid(stdout)

    def assert_backup_file_exists(self, backup_path: str) -> None:
        """Assert backup file exists at given path"""
        assert Path(backup_path).exists(), f"Backup file not found: {backup_path}"

    def get_workflow_count(self, stdout: str) -> int:
        """Extract workflow count from list output"""
        lines = stdout.strip().split("\n")
        # Count non-header, non-empty lines that look like workflow entries
        count = sum(1 for line in lines if line.strip() and not line.startswith("─") and not line.startswith("│ Name"))
        return count
