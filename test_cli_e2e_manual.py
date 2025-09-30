#!/usr/bin/env python3
"""
n8n-deploy Manual E2E CLI Testing Script
Using specialized libraries for comprehensive testing

This script provides comprehensive End-to-End testing of the n8n-deploy CLI tool
using specialized testing libraries including click.testing, pytest, subprocess,
and other testing utilities for authentic CLI validation.

REQUIRED ENVIRONMENT VARIABLE:
    N8N_DEPLOY_TEST_SERVER - URL of test n8n server for server integration tests
                             Example: export N8N_DEPLOY_TEST_SERVER=http://localhost:5678

USAGE:
    # Set test server URL
    export N8N_DEPLOY_TEST_SERVER=http://localhost:5678

    # Run all tests
    python test_cli_e2e_manual.py

    # Run specific category
    python test_cli_e2e_manual.py --category server_integration
"""

import pytest
import tempfile
import subprocess
import json
import sys
import os
import shutil
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from click.testing import CliRunner
from dataclasses import dataclass
from enum import Enum
import hashlib


class TestCategory(Enum):
    """Test categories for selective execution"""

    CLI_STRUCTURE = "cli_structure"
    DATABASE = "database"
    API_KEYS = "api_keys"
    WORKFLOWS = "workflows"
    BACKUPS = "backups"
    SERVER = "server"
    OUTPUT_FORMAT = "output_format"
    ERROR_HANDLING = "error_handling"


@dataclass
class TestResult:
    """Test result container"""

    name: str
    category: TestCategory
    passed: bool
    duration: float
    error_message: Optional[str] = None
    output: Optional[str] = None


class WorkflowGenerator:
    """Generate realistic n8n workflow data for testing"""

    @staticmethod
    def create_basic_workflow(name: str, workflow_type: str = "main") -> Dict[str, Any]:
        """Create a basic n8n workflow structure"""
        return {
            "id": f"workflow_{hashlib.md5(name.encode()).hexdigest()[:8]}",
            "name": name,
            "active": True,
            "nodes": [
                {
                    "parameters": {},
                    "id": "start_node",
                    "name": "Start",
                    "type": "n8n-nodes-base.start",
                    "typeVersion": 1,
                    "position": [240, 300],
                },
                {
                    "parameters": {
                        "functionCode": f"// {name} processing\nreturn items.map(item => ({{\n  ...item,\n  processed: true,\n  workflow: '{name}'\n}}));"
                    },
                    "id": "function_node",
                    "name": "Process",
                    "type": "n8n-nodes-base.function",
                    "typeVersion": 1,
                    "position": [460, 300],
                },
            ],
            "connections": {"Start": {"main": [[{"node": "Process", "type": "main", "index": 0}]]}},
            "staticData": {
                "global": {
                    "version": "1.0.0",
                    "type": workflow_type,
                    "generator": "n8n-deploy-e2e-test",
                }
            },
            "settings": {
                "executionOrder": "v1",
                "saveManualExecutions": True,
                "callerPolicy": "workflowsFromSameOwner",
            },
            "createdAt": "2024-01-01T10:00:00.000Z",
            "updatedAt": "2024-01-01T12:00:00.000Z",
            "tags": [{"id": "test", "name": "test"}],
        }

    @staticmethod
    def create_complex_workflow(name: str) -> Dict[str, Any]:
        """Create a more complex workflow for testing"""
        workflow = WorkflowGenerator.create_basic_workflow(name, "complex")

        # Add more nodes
        workflow["nodes"].extend(
            [
                {
                    "parameters": {
                        "conditions": {
                            "string": [
                                {
                                    "value1": "={{$json.processed}}",
                                    "operation": "equal",
                                    "value2": "true",
                                }
                            ]
                        }
                    },
                    "id": "if_node",
                    "name": "Check Status",
                    "type": "n8n-nodes-base.if",
                    "typeVersion": 1,
                    "position": [680, 300],
                },
                {
                    "parameters": {"message": "Success!"},
                    "id": "success_node",
                    "name": "Success",
                    "type": "n8n-nodes-base.noOp",
                    "typeVersion": 1,
                    "position": [900, 200],
                },
            ]
        )

        # Add more connections
        workflow["connections"]["Process"] = {"main": [[{"node": "Check Status", "type": "main", "index": 0}]]}
        workflow["connections"]["Check Status"] = {"main": [[{"node": "Success", "type": "main", "index": 0}], []]}

        return workflow


class N8nDeployE2ETester:
    """Main E2E testing class using specialized libraries"""

    def __init__(self, project_root: str = None):
        """Initialize the tester"""
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self.cli_path = self.project_root / "n8n-deploy"
        self.results: List[TestResult] = []
        self.temp_dirs: List[str] = []

        # Test server configuration - required for server integration tests
        self.test_server_url = os.environ.get("N8N_DEPLOY_TEST_SERVER")
        if not self.test_server_url:
            print(
                f"{Colors.RED}ERROR: N8N_DEPLOY_TEST_SERVER environment variable is required for server integration tests{Colors.RESET}"
            )
            print(
                f"{Colors.YELLOW}Set it to your test n8n server URL, e.g.: export N8N_DEPLOY_TEST_SERVER=http://localhost:5678{Colors.RESET}"
            )
            sys.exit(1)

        # Verify CLI exists
        if not self.cli_path.exists():
            raise FileNotFoundError(f"CLI script not found at {self.cli_path}")

    def setup_test_environment(self) -> Tuple[str, str]:
        """Create temporary test environment"""
        app_dir = tempfile.mkdtemp(prefix="n8n_e2e_app_")
        flow_dir = tempfile.mkdtemp(prefix="n8n_e2e_flow_")

        self.temp_dirs.extend([app_dir, flow_dir])

        return app_dir, flow_dir

    def cleanup_environment(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        self.temp_dirs.clear()

    def run_cli_command(
        self,
        args: List[str],
        cwd: str = None,
        env: Dict[str, str] = None,
        input_data: str = None,
        timeout: int = 30,
    ) -> Tuple[int, str, str]:
        """Execute n8n-deploy CLI command using subprocess"""
        cmd = [str(self.cli_path)] + args

        # Set up environment
        test_env = os.environ.copy()
        test_env["N8N_DEPLOY_TESTING"] = "1"
        if env:
            test_env.update(env)

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or str(self.project_root),
                env=test_env,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 124, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return 1, "", str(e)

    def run_cli_with_click_runner(self, args: List[str]) -> Tuple[int, str]:
        """Execute CLI using Click's CliRunner for isolated testing"""
        try:
            # Import the CLI module
            sys.path.insert(0, str(self.project_root))
            from api.cli.app import cli

            runner = CliRunner()
            result = runner.invoke(cli, args, catch_exceptions=False)
            return result.exit_code, result.output
        except Exception as e:
            return 1, str(e)

    def create_sample_workflow_file(self, directory: str, name: str, workflow_type: str = "main") -> str:
        """Create a sample workflow JSON file"""
        workflow_data = WorkflowGenerator.create_basic_workflow(name, workflow_type)
        workflow_path = Path(directory) / f"{name}.json"

        with open(workflow_path, "w") as f:
            json.dump(workflow_data, f, indent=2)

        return str(workflow_path)

    def validate_json_output(self, output: str) -> bool:
        """Validate that output is valid JSON"""
        try:
            json.loads(output)
            return True
        except json.JSONDecodeError:
            return False

    def validate_table_output(self, output: str) -> bool:
        """Validate table format output"""
        lines = output.strip().split("\n")
        return len(lines) >= 2 and ("┌" in lines[0] or "│" in output or "Name" in output)

    def run_test(self, test_func, category: TestCategory) -> TestResult:
        """Run a single test function and capture results"""
        start_time = time.time()
        test_name = test_func.__name__

        try:
            test_func()
            duration = time.time() - start_time
            result = TestResult(test_name, category, True, duration)
            print(f"✅ {test_name} ({duration:.2f}s)")
            return result
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(test_name, category, False, duration, str(e))
            print(f"❌ {test_name} ({duration:.2f}s): {e}")
            return result

    # === CLI Structure Tests ===

    def test_help_command(self):
        """Test help command display"""
        exit_code, output, stderr = self.run_cli_command(["--help"])
        assert exit_code == 0, f"Help command failed: {stderr}"
        assert "n8n-deploy" in output, "Help output missing program name"
        assert "COMMAND" in output, "Help output missing command structure"
        assert "workflow deployment tool" in output.lower(), "Help missing description"

    def test_version_command(self):
        """Test version command"""
        exit_code, output, stderr = self.run_cli_command(["--version"])
        assert exit_code == 0, f"Version command failed: {stderr}"
        assert "2.0.0" in output, f"Version output incorrect: {output}"

    def test_invalid_command(self):
        """Test invalid command handling"""
        exit_code, output, stderr = self.run_cli_command(["invalid-command"])
        assert exit_code != 0, "Invalid command should fail"
        assert "No such command" in stderr or "Usage:" in output, "Missing error message"

    def test_command_help_consistency(self):
        """Test individual command help messages"""
        commands = ["list", "add", "remove", "sync", "search", "stats"]
        for command in commands:
            exit_code, output, stderr = self.run_cli_command([command, "--help"])
            assert exit_code == 0, f"Help for {command} failed: {stderr}"
            assert "Usage:" in output, f"Help for {command} missing usage"

    def test_subcommand_help(self):
        """Test subcommand group help"""
        subcommands = ["db", "apikey"]
        for subcommand in subcommands:
            exit_code, output, stderr = self.run_cli_command([subcommand, "--help"])
            assert exit_code == 0, f"Help for {subcommand} failed: {stderr}"
            assert "Commands:" in output, f"Help for {subcommand} missing commands list"

    # === Database Operation Tests ===

    def test_database_initialization(self):
        """Test database initialization"""
        app_dir, _ = self.setup_test_environment()

        exit_code, output, stderr = self.run_cli_command(["db", "init", "--app-dir", app_dir])
        assert exit_code == 0, f"Database init failed: {stderr}"

        db_path = Path(app_dir) / "n8n-deploy.db"
        assert db_path.exists(), "Database file not created"

    def test_database_status(self):
        """Test database status command"""
        app_dir, _ = self.setup_test_environment()

        # Initialize database first
        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        exit_code, output, stderr = self.run_cli_command(["db", "status", "--app-dir", app_dir])
        assert exit_code == 0, f"Database status failed: {stderr}"
        assert "Schema Version" in output, "Status missing schema version"
        assert app_dir in output, "Status missing database location"

    def test_database_backup(self):
        """Test database backup functionality"""
        app_dir, _ = self.setup_test_environment()

        # Initialize database
        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        exit_code, output, stderr = self.run_cli_command(["db", "backup", "--app-dir", app_dir])
        assert exit_code == 0, f"Database backup failed: {stderr}"

        backup_dir = Path(app_dir) / "backups"
        assert backup_dir.exists(), "Backup directory not created"
        backup_files = list(backup_dir.glob("*.tar.gz"))
        assert len(backup_files) > 0, "No backup files created"

    def test_database_compact(self):
        """Test database maintenance operations"""
        app_dir, _ = self.setup_test_environment()

        # Initialize database
        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        # Test compact
        exit_code, output, stderr = self.run_cli_command(["db", "compact", "--app-dir", app_dir])
        assert exit_code == 0, f"Database compact failed: {stderr}"

    # === API Key Management Tests ===

    def test_apikey_add_jwt(self):
        """Test adding JWT API key"""
        app_dir, _ = self.setup_test_environment()

        # Initialize database
        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        # Valid JWT token for testing
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjE2MjM5MDIyfQ.test"

        exit_code, output, stderr = self.run_cli_command(["apikey", "add", jwt_token, "--name", "test_key"])
        assert exit_code == 0, f"API key add failed: {stderr}"
        assert "successfully added" in output.lower() or "added" in output.lower(), "Missing success message"

    def test_apikey_list_formats(self):
        """Test API key listing in different formats"""
        app_dir, _ = self.setup_test_environment()

        # Initialize and add a key
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjE2MjM5MDIyfQ.test"
        self.run_cli_command(["apikey", "add", jwt_token, "--name", "test_key"])

        # Test table format
        exit_code, output, stderr = self.run_cli_command(["apikey", "list", "--no-emoji"])
        assert exit_code == 0, f"API key list failed: {stderr}"
        assert self.validate_table_output(output), "Invalid table format"

        # Test JSON format
        exit_code, output, stderr = self.run_cli_command(["apikey", "list", "--format", "json"])
        assert exit_code == 0, f"API key list JSON failed: {stderr}"
        assert self.validate_json_output(output), "Invalid JSON format"

    def test_apikey_get_show_key(self):
        """Test retrieving specific API key"""
        app_dir, _ = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjE2MjM5MDIyfQ.test"
        self.run_cli_command(["apikey", "add", jwt_token, "--name", "test_key"])

        # Test get without showing key
        exit_code, output, stderr = self.run_cli_command(["apikey", "get", "test_key"])
        assert exit_code == 0, f"API key get failed: {stderr}"
        assert "test_key" in output, "Key name not in output"
        assert jwt_token not in output, "Key value should be hidden"

        # Test get with showing key
        exit_code, output, stderr = self.run_cli_command(["apikey", "get", "test_key", "--show-key"])
        assert exit_code == 0, f"API key get with show failed: {stderr}"
        assert jwt_token in output, "Key value should be shown"

    def test_apikey_lifecycle(self):
        """Test complete API key lifecycle"""
        app_dir, _ = self.setup_test_environment()

        # Initialize
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjE2MjM5MDIyfQ.test"

        # Add key
        self.run_cli_command(["apikey", "add", jwt_token, "--name", "lifecycle_key"])

        # Deactivate key
        exit_code, output, stderr = self.run_cli_command(["apikey", "deactivate", "lifecycle_key"])
        assert exit_code == 0, f"API key deactivate failed: {stderr}"

        # Delete key
        exit_code, output, stderr = self.run_cli_command(["apikey", "delete", "lifecycle_key", "--confirm"])
        assert exit_code == 0, f"API key delete failed: {stderr}"

        # Verify deletion
        exit_code, output, stderr = self.run_cli_command(["apikey", "get", "lifecycle_key"])
        assert exit_code != 0, "Deleted key should not be found"

    def test_apikey_test_connection(self):
        """Test API key connection testing"""
        app_dir, _ = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjE2MjM5MDIyfQ.test"
        self.run_cli_command(["apikey", "add", jwt_token, "--name", "test_connection_key"])

        # Test connection (will fail without real server, but should handle gracefully)
        exit_code, output, stderr = self.run_cli_command(
            ["apikey", "test", "test_connection_key"],
            env={"N8N_SERVER_URL": self.test_server_url},
        )
        # Don't assert exit code as connection will fail, just ensure it doesn't crash
        assert "test_connection_key" in output or "connection" in output.lower(), "Missing test output"

    # === Workflow Operation Tests ===

    def test_workflow_add_and_list(self):
        """Test adding and listing workflows"""
        app_dir, flow_dir = self.setup_test_environment()

        # Initialize database
        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        # Create sample workflow file
        workflow_path = self.create_sample_workflow_file(flow_dir, "test_workflow")

        # Add workflow
        exit_code, output, stderr = self.run_cli_command(
            [
                "add",
                "test_workflow",
                "test_workflow",
                "test_workflow.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )
        assert exit_code == 0, f"Workflow add failed: {stderr}"

        # List workflows
        exit_code, output, stderr = self.run_cli_command(["list", "--app-dir", app_dir, "--flow-dir", flow_dir, "--no-emoji"])
        assert exit_code == 0, f"Workflow list failed: {stderr}"
        assert "test_workflow" in output, "Added workflow not in list"

    def test_workflow_search_and_stats(self):
        """Test workflow search and statistics"""
        app_dir, flow_dir = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "search_test", "main")
        self.create_sample_workflow_file(flow_dir, "search_automation", "automation")

        # Add workflows
        self.run_cli_command(
            [
                "add",
                "search_test",
                "search_test",
                "search_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )
        self.run_cli_command(
            [
                "add",
                "search_automation",
                "search_automation",
                "search_automation.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # Test search
        exit_code, output, stderr = self.run_cli_command(["search", "search", "--app-dir", app_dir, "--flow-dir", flow_dir])
        assert exit_code == 0, f"Workflow search failed: {stderr}"
        assert "search_test" in output or "search_automation" in output, "Search results missing"

        # Test stats
        exit_code, output, stderr = self.run_cli_command(
            ["stats", "search_test", "--app-dir", app_dir, "--flow-dir", flow_dir]
        )
        assert exit_code == 0, f"Workflow stats failed: {stderr}"
        assert "Total" in output and "2" in output, "Stats missing workflow count"

    def test_workflow_sync_operation(self):
        """Test workflow synchronization"""
        app_dir, flow_dir = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "sync_test")
        self.run_cli_command(
            [
                "add",
                "sync_test",
                "sync_test",
                "sync_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        exit_code, output, stderr = self.run_cli_command(["sync", "sync_test", "--app-dir", app_dir, "--flow-dir", flow_dir])
        assert exit_code == 0, f"Workflow sync failed: {stderr}"
        assert "sync_test" in output or "Synchronized" in output, "Sync results missing"

    def test_workflow_remove(self):
        """Test workflow removal"""
        app_dir, flow_dir = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "remove_test")
        self.run_cli_command(
            [
                "add",
                "remove_test",
                "remove_test",
                "remove_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # Remove workflow
        exit_code, output, stderr = self.run_cli_command(
            ["remove", "remove_test", "--app-dir", app_dir, "--flow-dir", flow_dir]
        )
        assert exit_code == 0, f"Workflow remove failed: {stderr}"

        # Verify removal
        exit_code, output, stderr = self.run_cli_command(["list", "--app-dir", app_dir, "--flow-dir", flow_dir, "--no-emoji"])
        assert "remove_test" not in output, "Removed workflow still in list"

    # === Backup Operation Tests ===

    def test_backup_workflows(self):
        """Test workflow backup creation"""
        app_dir, flow_dir = self.setup_test_environment()
        backup_dir = tempfile.mkdtemp(prefix="n8n_backup_")
        self.temp_dirs.append(backup_dir)

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "backup_test")
        self.run_cli_command(
            [
                "add",
                "backup_test",
                "backup_test",
                "backup_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # Create backup
        exit_code, output, stderr = self.run_cli_command(
            [
                "backup-workflows",
                "--backup-dir",
                backup_dir,
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )
        assert exit_code == 0, f"Backup creation failed: {stderr}"

        # Verify backup files
        backup_files = list(Path(backup_dir).glob("*.tar.gz"))
        assert len(backup_files) > 0, "No backup files created"

    def test_list_backups(self):
        """Test backup listing"""
        app_dir, flow_dir = self.setup_test_environment()
        backup_dir = tempfile.mkdtemp(prefix="n8n_backup_")
        self.temp_dirs.append(backup_dir)

        # Setup and create backup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "list_backup_test")
        self.run_cli_command(
            [
                "add",
                "list_backup_test",
                "list_backup_test",
                "list_backup_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )
        self.run_cli_command(
            [
                "backup-workflows",
                "--backup-dir",
                backup_dir,
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # List backups
        exit_code, output, stderr = self.run_cli_command(["list-backups", "--backup-dir", backup_dir, "--app-dir", app_dir])
        assert exit_code == 0, f"List backups failed: {stderr}"
        assert ".tar.gz" in output, "Backup files not listed"

    def test_verify_backup(self):
        """Test backup verification"""
        app_dir, flow_dir = self.setup_test_environment()
        backup_dir = tempfile.mkdtemp(prefix="n8n_backup_")
        self.temp_dirs.append(backup_dir)

        # Setup and create backup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "verify_test")
        self.run_cli_command(
            [
                "add",
                "verify_test",
                "verify_test",
                "verify_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )
        self.run_cli_command(
            [
                "backup-workflows",
                "--backup-dir",
                backup_dir,
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # Get backup file
        backup_files = list(Path(backup_dir).glob("*.tar.gz"))
        assert len(backup_files) > 0, "No backup file to verify"

        # Verify backup
        exit_code, output, stderr = self.run_cli_command(["verify-backup", str(backup_files[0]), "--app-dir", app_dir])
        assert exit_code == 0, f"Backup verification failed: {stderr}"
        assert "verified" in output.lower() or "valid" in output.lower(), "Missing verification confirmation"

    # === Server Integration Tests (Mock) ===

    def test_list_server_no_connection(self):
        """Test server listing without connection"""
        app_dir, _ = self.setup_test_environment()

        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        exit_code, output, stderr = self.run_cli_command(
            ["list-server", "--app-dir", app_dir, "--server-url", "http://nonexistent-server:5678"]
        )
        # Should fail gracefully
        assert (
            "connection" in output.lower() or "error" in output.lower() or "failed" in stderr.lower()
        ), "Missing connection error message"

    def test_pull_push_server_operations(self):
        """Test pull/push operations with server URL"""
        app_dir, flow_dir = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiaWF0IjoxNjE2MjM5MDIyfQ.test"
        self.run_cli_command(["apikey", "add", jwt_token, "--name", "server_test_key"])

        # Test pull (will fail without real server)
        exit_code, output, stderr = self.run_cli_command(
            [
                "pull",
                "test_workflow",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
                "--server-url",
                self.test_server_url,
            ]
        )
        # Should handle connection failure gracefully
        assert exit_code != 0 or "connection" in output.lower(), "Pull should fail or show connection info"

        # Test push (will fail without real server)
        self.create_sample_workflow_file(flow_dir, "push_test")
        self.run_cli_command(
            [
                "add",
                "push_test",
                "push_test",
                "push_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        exit_code, output, stderr = self.run_cli_command(
            [
                "push",
                "push_test",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
                "--server-url",
                self.test_server_url,
            ]
        )
        # Should handle connection failure gracefully
        assert exit_code != 0 or "connection" in output.lower(), "Push should fail or show connection info"

    # === Output Format Tests ===

    def test_emoji_vs_no_emoji_modes(self):
        """Test emoji and no-emoji output modes"""
        app_dir, flow_dir = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "emoji_test")
        self.run_cli_command(
            [
                "add",
                "emoji_test",
                "emoji_test",
                "emoji_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # Test with emoji (default)
        exit_code, output_emoji, stderr = self.run_cli_command(["list", "--app-dir", app_dir, "--flow-dir", flow_dir])
        assert exit_code == 0, f"List with emoji failed: {stderr}"

        # Test without emoji
        exit_code, output_no_emoji, stderr = self.run_cli_command(
            ["list", "--app-dir", app_dir, "--flow-dir", flow_dir, "--no-emoji"]
        )
        assert exit_code == 0, f"List without emoji failed: {stderr}"

        # Both should contain the workflow name
        assert "emoji_test" in output_emoji and "emoji_test" in output_no_emoji, "Workflow missing from outputs"

    def test_json_format_output(self):
        """Test JSON format output"""
        app_dir, flow_dir = self.setup_test_environment()

        # Setup
        self.run_cli_command(["db", "init", "--app-dir", app_dir])
        self.create_sample_workflow_file(flow_dir, "json_test")
        self.run_cli_command(
            [
                "add",
                "json_test",
                "json_test",
                "json_test.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # Test JSON output for list
        exit_code, output, stderr = self.run_cli_command(
            ["list", "--app-dir", app_dir, "--flow-dir", flow_dir, "--format", "json"]
        )
        assert exit_code == 0, f"JSON list failed: {stderr}"
        assert self.validate_json_output(output), "Invalid JSON output format"

        # Parse and verify JSON content
        data = json.loads(output)
        assert isinstance(data, list), "JSON output should be a list"
        assert any(item.get("name") == "json_test" for item in data), "Workflow not in JSON output"

    # === Error Handling Tests ===

    def test_invalid_directory_paths(self):
        """Test handling of invalid directory paths"""
        # Test invalid app directory
        exit_code, output, stderr = self.run_cli_command(["db", "status", "--app-dir", "/dev/null/invalid_path"])
        assert exit_code != 0, "Should fail with invalid app directory"

        # Test invalid flow directory
        app_dir, _ = self.setup_test_environment()
        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        exit_code, output, stderr = self.run_cli_command(
            ["list", "--app-dir", app_dir, "--flow-dir", "/dev/null/invalid_path"]
        )
        # May succeed with empty list or fail gracefully
        assert exit_code == 0 or "error" in stderr.lower(), "Should handle invalid flow directory"

    def test_missing_workflow_file(self):
        """Test handling of missing workflow files"""
        app_dir, flow_dir = self.setup_test_environment()

        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        exit_code, output, stderr = self.run_cli_command(
            [
                "add",
                "nonexistent_workflow",
                "nonexistent_workflow",
                "nonexistent_workflow.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )
        assert exit_code != 0, "Should fail when adding nonexistent workflow"
        assert "not found" in stderr.lower() or "error" in stderr.lower(), "Missing error message"

    def test_invalid_api_key_operations(self):
        """Test invalid API key operations"""
        app_dir, _ = self.setup_test_environment()

        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        # Test getting nonexistent key
        exit_code, output, stderr = self.run_cli_command(["apikey", "get", "nonexistent_key"])
        assert exit_code != 0, "Should fail when getting nonexistent key"

        # Test deleting nonexistent key
        exit_code, output, stderr = self.run_cli_command(["apikey", "delete", "nonexistent_key", "--confirm"])
        assert exit_code != 0, "Should fail when deleting nonexistent key"

    def test_malformed_workflow_json(self):
        """Test handling of malformed workflow JSON"""
        app_dir, flow_dir = self.setup_test_environment()

        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        # Create malformed JSON file
        malformed_path = Path(flow_dir) / "malformed.json"
        with open(malformed_path, "w") as f:
            f.write('{"invalid": json}')

        exit_code, output, stderr = self.run_cli_command(
            [
                "add",
                "malformed",
                "malformed",
                "malformed.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )
        assert exit_code != 0, "Should fail with malformed JSON"
        assert "json" in stderr.lower() or "parse" in stderr.lower(), "Missing JSON error message"

    # === Environment and Configuration Tests ===

    def test_environment_variable_precedence(self):
        """Test environment variable vs CLI option precedence"""
        app_dir, flow_dir = self.setup_test_environment()
        env_flow_dir = tempfile.mkdtemp(prefix="n8n_env_flow_")
        self.temp_dirs.append(env_flow_dir)

        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        # Create workflows in both directories
        self.create_sample_workflow_file(flow_dir, "cli_dir_workflow")
        self.create_sample_workflow_file(env_flow_dir, "env_dir_workflow")

        # Add workflows first to the database
        self.run_cli_command(
            [
                "add",
                "env_dir_workflow",
                "env_dir_workflow",
                "env_dir_workflow.json",
                "--app-dir",
                app_dir,
            ],
            env={"N8N_FLOW_DIR": env_flow_dir},
        )
        self.run_cli_command(
            [
                "add",
                "cli_dir_workflow",
                "cli_dir_workflow",
                "cli_dir_workflow.json",
                "--app-dir",
                app_dir,
                "--flow-dir",
                flow_dir,
            ]
        )

        # Test with environment variable
        exit_code, output, stderr = self.run_cli_command(
            ["sync", "env_dir_workflow", "--app-dir", app_dir], env={"N8N_FLOW_DIR": env_flow_dir}
        )
        assert exit_code == 0, f"Sync with env var failed: {stderr}"

        # Test CLI override of environment variable
        exit_code, output, stderr = self.run_cli_command(
            ["sync", "cli_dir_workflow", "--app-dir", app_dir, "--flow-dir", flow_dir],
            env={"N8N_FLOW_DIR": env_flow_dir},
        )
        assert exit_code == 0, f"Sync with CLI override failed: {stderr}"

    def test_server_url_configuration(self):
        """Test server URL configuration methods"""
        app_dir, _ = self.setup_test_environment()

        self.run_cli_command(["db", "init", "--app-dir", app_dir])

        # Test with environment variable
        exit_code, output, stderr = self.run_cli_command(
            ["list-server", "--app-dir", app_dir], env={"N8N_SERVER_URL": self.test_server_url}
        )
        # Will fail to connect but should show server URL
        assert (
            self.test_server_url in output or "connection" in output.lower()
        ), f"Test server URL {self.test_server_url} not used"

        # Test CLI override
        test_cli_url = "http://cli-override:5678"
        exit_code, output, stderr = self.run_cli_command(
            ["list-server", "--app-dir", app_dir, "--server-url", test_cli_url],
            env={"N8N_SERVER_URL": self.test_server_url},
        )
        # CLI option should take precedence
        assert test_cli_url in output or "connection" in output.lower(), "CLI server URL override not working"

    # === Main Test Execution ===

    def run_category_tests(self, category: TestCategory) -> List[TestResult]:
        """Run all tests for a specific category"""
        test_methods = {
            TestCategory.CLI_STRUCTURE: [
                self.test_help_command,
                self.test_version_command,
                self.test_invalid_command,
                self.test_command_help_consistency,
                self.test_subcommand_help,
            ],
            TestCategory.DATABASE: [
                self.test_database_initialization,
                self.test_database_status,
                self.test_database_backup,
                self.test_database_compact,
            ],
            TestCategory.API_KEYS: [
                self.test_apikey_add_jwt,
                self.test_apikey_list_formats,
                self.test_apikey_get_show_key,
                self.test_apikey_lifecycle,
                self.test_apikey_test_connection,
            ],
            TestCategory.WORKFLOWS: [
                self.test_workflow_add_and_list,
                self.test_workflow_search_and_stats,
                self.test_workflow_sync_operation,
                self.test_workflow_remove,
            ],
            TestCategory.BACKUPS: [
                self.test_backup_workflows,
                self.test_list_backups,
                self.test_verify_backup,
            ],
            TestCategory.SERVER: [
                self.test_list_server_no_connection,
                self.test_pull_push_server_operations,
            ],
            TestCategory.OUTPUT_FORMAT: [
                self.test_emoji_vs_no_emoji_modes,
                self.test_json_format_output,
            ],
            TestCategory.ERROR_HANDLING: [
                self.test_invalid_directory_paths,
                self.test_missing_workflow_file,
                self.test_invalid_api_key_operations,
                self.test_malformed_workflow_json,
                self.test_environment_variable_precedence,
                self.test_server_url_configuration,
            ],
        }

        results = []
        test_methods_list = test_methods.get(category, [])

        print(f"\n🧪 Running {category.value} tests ({len(test_methods_list)} tests)...")

        for test_method in test_methods_list:
            try:
                # Clean environment for each test
                self.cleanup_environment()
                result = self.run_test(test_method, category)
                results.append(result)
                self.results.append(result)
            except Exception as e:
                print(f"❌ {test_method.__name__} (ERROR): {e}")
                result = TestResult(test_method.__name__, category, False, 0.0, str(e))
                results.append(result)
                self.results.append(result)

        return results

    def run_all_tests(self, categories: List[TestCategory] = None) -> Dict[TestCategory, List[TestResult]]:
        """Run all tests or specific categories"""
        if categories is None:
            categories = list(TestCategory)

        all_results = {}

        print("🚀 Starting n8n-deploy E2E Manual CLI Testing")
        print(f"📍 Project root: {self.project_root}")
        print(f"🎯 CLI path: {self.cli_path}")

        start_time = time.time()

        try:
            for category in categories:
                category_results = self.run_category_tests(category)
                all_results[category] = category_results
        finally:
            self.cleanup_environment()

        total_time = time.time() - start_time
        self.print_summary(all_results, total_time)

        return all_results

    def print_summary(self, results: Dict[TestCategory, List[TestResult]], total_time: float):
        """Print test execution summary"""
        total_tests = sum(len(category_results) for category_results in results.values())
        passed_tests = sum(len([r for r in category_results if r.passed]) for category_results in results.values())
        failed_tests = total_tests - passed_tests

        print(f"\n{'='*60}")
        print(f"🎯 n8n-deploy E2E Test Summary")
        print(f"{'='*60}")
        print(f"⏱️  Total time: {total_time:.2f}s")
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success rate: {(passed_tests/total_tests*100):.1f}%")

        # Category breakdown
        print(f"\n📋 Category Breakdown:")
        for category, category_results in results.items():
            category_passed = len([r for r in category_results if r.passed])
            category_total = len(category_results)
            print(f"  {category.value}: {category_passed}/{category_total} passed")

        # Failed tests details
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for category_results in results.values():
                for result in category_results:
                    if not result.passed:
                        print(f"  • {result.name}: {result.error_message}")

        print(f"\n{'='*60}")


def main():
    """Main entry point for the E2E testing script"""
    parser = argparse.ArgumentParser(description="n8n-deploy E2E Manual CLI Testing")
    parser.add_argument(
        "--category",
        choices=[c.value for c in TestCategory],
        help="Run tests for specific category only",
    )
    parser.add_argument("--project-root", help="Path to project root directory")
    parser.add_argument("--list-categories", action="store_true", help="List available test categories")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.list_categories:
        print("Available test categories:")
        for category in TestCategory:
            print(f"  • {category.value}")
        return 0

    try:
        tester = N8nDeployE2ETester(args.project_root)

        if args.category:
            category = TestCategory(args.category)
            results = tester.run_all_tests([category])
        else:
            results = tester.run_all_tests()

        # Determine exit code based on results
        total_passed = sum(len([r for r in category_results if r.passed]) for category_results in results.values())
        total_tests = sum(len(category_results) for category_results in results.values())

        return 0 if total_passed == total_tests else 1

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
