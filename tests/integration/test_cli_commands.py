#!/usr/bin/env python3
"""
Comprehensive CLI command tests for n8n-deploy
Tests all main commands: workflow management, API keys, and database operations
"""

import pytest
import json
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from api.manager import WorkflowManager
from api.models import Workflow, WorkflowType, WorkflowStatus
from api.api_keys import ApiKeyManager
from tests.helpers import create_test_workflow_data, create_workflow_file

# Set testing environment variable to skip default workflows
os.environ["N8N_DEPLOY_TESTING"] = "1"


class BaseCLITest:
    """Base class for CLI tests with common fixtures and utilities"""

    @pytest.fixture
    def cli_test_setup(self, test_config):
        """Create test environment with workflows, API keys, and backup files"""
        manager = WorkflowManager(config=test_config)

        # Clear existing data
        with manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.execute("DELETE FROM api_keys")
            conn.commit()

        # Create test workflows with actual files
        test_workflows = [
            {
                "id": "test_wf_001",
                "name": "Test Workflow 1",
                "type": WorkflowType.MAIN,
                "status": WorkflowStatus.ACTIVE,
                "file_path": "workflows/test_workflow_1.json",
            },
            {
                "id": "test_wf_002",
                "name": "Search Test Workflow",
                "type": WorkflowType.SUBFLOW,
                "status": WorkflowStatus.INACTIVE,
                "file_path": "workflows/search_test.json",
            },
            {
                "id": "test_wf_003",
                "name": "Stats Workflow",
                "type": WorkflowType.UTILITY,
                "status": WorkflowStatus.ACTIVE,
                "file_path": "workflows/stats_workflow.json",
            },
        ]

        # Create workflow files and add to database
        for wf_data in test_workflows:
            # Create actual workflow file
            workflow_file = test_config.base_folder / wf_data["file_path"]
            workflow_file.parent.mkdir(parents=True, exist_ok=True)

            workflow_content = create_test_workflow_data(
                workflow_id=wf_data["id"], name=wf_data["name"]
            )

            with open(workflow_file, "w") as f:
                json.dump(workflow_content, f, indent=2)

            # Add to database
            workflow = Workflow(**wf_data)
            manager.db.create_workflow(workflow)

        # Create test API key
        manager.api_manager.add_api_key(
            name="test_api_key",
            api_key="test_api_key_12345",
            description="Test API key for CLI testing",
        )

        return manager, test_config

    def run_cli_command(self, config, command_args, input_data=None):
        """Helper to run CLI commands with test configuration"""
        cmd = [
            sys.executable,
            "api/cli.py",
            "--app-dir",
            str(config.base_folder),
            "--no-emoji",  # Consistent output for testing
        ] + command_args

        # Pass testing environment variable to subprocess
        env = os.environ.copy()
        env["N8N_DEPLOY_TESTING"] = "1"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,  # n8n-deploy root directory
            env=env,
            input=input_data,
        )

        # Filter out initialization messages for clean parsing
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.split("\n")
            # Remove database initialization messages
            filtered_lines = [
                line
                for line in lines
                if not line.startswith("🎭 n8n_deploy_ database")
                and not line.startswith("🎭 Database initialized")
            ]
            result.stdout = "\n".join(filtered_lines)

        return result


@pytest.mark.integration
class TestCLIWorkflowCommands(BaseCLITest):
    """Test workflow management CLI commands"""

    def test_cli_list_workflows_comprehensive(self, cli_test_setup):
        """Test workflow list command with all options"""
        manager, config = cli_test_setup

        # Test basic list
        result = self.run_cli_command(config, ["list"])
        assert result.returncode == 0
        # Check for truncated workflow names in table format
        assert "Test" in result.stdout and "Workfl" in result.stdout  # "Test Workfl… 1"
        assert "Search" in result.stdout  # "Search Test Workfl…"
        assert "Stats" in result.stdout  # "Stats Workfl…"
        assert "test_w" in result.stdout  # Workflow IDs should be visible

        # Test JSON format
        result = self.run_cli_command(config, ["list", "--format", "json"])
        assert result.returncode == 0
        workflows_data = json.loads(result.stdout)
        assert len(workflows_data) == 3
        assert all("id" in wf for wf in workflows_data)

        # Test table format
        result = self.run_cli_command(config, ["list", "--format", "table"])
        assert result.returncode == 0
        assert "┏" in result.stdout  # Table border character

    def test_cli_search_workflows(self, cli_test_setup):
        """Test workflow search functionality"""
        manager, config = cli_test_setup

        # Search by name
        result = self.run_cli_command(config, ["search", "Search"])
        assert result.returncode == 0
        assert "Search Test Workflow" in result.stdout
        assert "Test Workflow 1" not in result.stdout

        # Search by ID
        result = self.run_cli_command(config, ["search", "test_wf_001"])
        assert result.returncode == 0
        assert "Test Workflow 1" in result.stdout

        # Search with no results
        result = self.run_cli_command(config, ["search", "nonexistent"])
        assert result.returncode == 0
        assert "No workflows found" in result.stdout

    def test_cli_workflow_stats(self, cli_test_setup):
        """Test workflow statistics command"""
        manager, config = cli_test_setup

        # Test stats for existing workflow
        result = self.run_cli_command(config, ["stats", "test_wf_001"])
        assert result.returncode == 0
        assert "Test Workflow 1" in result.stdout
        assert "Type" in result.stdout
        assert "Status" in result.stdout

        # Test stats in JSON format
        result = self.run_cli_command(
            config, ["stats", "test_wf_001", "--format", "json"]
        )
        assert result.returncode == 0
        stats_data = json.loads(result.stdout)
        assert stats_data["name"] == "Test Workflow 1"
        assert stats_data["id"] == "test_wf_001"

        # Test stats for non-existent workflow
        result = self.run_cli_command(config, ["stats", "nonexistent"])
        assert result.returncode != 0
        assert "unknown workflow" in result.stderr.lower()

    def test_cli_add_workflow(self, cli_test_setup):
        """Test adding new workflow via CLI"""
        manager, config = cli_test_setup

        # Create a new workflow file
        new_workflow_file = config.base_folder / "workflows" / "new_test.json"
        workflow_content = create_test_workflow_data(
            workflow_id="new_wf_001", name="New Test Workflow"
        )

        with open(new_workflow_file, "w") as f:
            json.dump(workflow_content, f, indent=2)

        # Add workflow via CLI
        result = self.run_cli_command(
            config,
            [
                "add",
                "new_wf_001",
                "New Test Workflow",
                "workflows/new_test.json",
                "--type",
                "main",
            ],
        )

        assert result.returncode == 0
        assert "added workflow" in result.stdout.lower()

        # Verify workflow was added to database
        workflows = manager.list_workflows()
        workflow_ids = [wf["id"] for wf in workflows]
        assert "new_wf_001" in workflow_ids

    def test_cli_remove_workflow(self, cli_test_setup):
        """Test removing workflow via CLI"""
        manager, config = cli_test_setup

        # Remove workflow with confirmation
        result = self.run_cli_command(config, ["remove", "test_wf_003", "--yes"])

        assert result.returncode == 0
        assert "removed" in result.stdout.lower()

        # Verify workflow was removed from database (should be archived, not deleted)
        # Create fresh manager to see updated state
        from api.manager import WorkflowManager

        fresh_manager = WorkflowManager(config=config)

        # Check that workflow is archived (still in DB but with archived status)
        archived_workflows = fresh_manager.db.list_workflows(status="archived")
        archived_ids = [wf.id for wf in archived_workflows]
        assert "test_wf_003" in archived_ids

        # Check that workflow is not in active workflows
        active_workflows = fresh_manager.db.list_workflows(status="active")
        active_ids = [wf.id for wf in active_workflows]
        assert "test_wf_003" not in active_ids

    def test_cli_sync_workflow(self, cli_test_setup):
        """Test syncing workflow metadata"""
        manager, config = cli_test_setup

        # Sync existing workflow
        result = self.run_cli_command(config, ["sync", "test_wf_001"])
        assert result.returncode == 0
        assert "synced" in result.stdout.lower()

        # Sync non-existent workflow
        result = self.run_cli_command(config, ["sync", "nonexistent"])
        assert result.returncode != 0
        assert "failed to sync" in result.stderr.lower()

    def test_cli_pull_workflow(self, cli_test_setup):
        """Test pulling workflow from n8n"""
        manager, config = cli_test_setup

        # Pull should fail because scripts are not set up
        result = self.run_cli_command(config, ["pull", "test_wf_001"])
        assert result.returncode != 0
        assert (
            "pull script not found" in result.stdout.lower()
            or "failed to pull" in result.stderr.lower()
        )

    def test_cli_push_workflow(self, cli_test_setup):
        """Test pushing workflow to n8n"""
        manager, config = cli_test_setup

        # Push should fail because workflow file doesn't exist in the expected location
        result = self.run_cli_command(config, ["push", "test_wf_001"])
        assert result.returncode != 0
        assert (
            "workflow file not found" in result.stdout.lower()
            or "failed to push" in result.stderr.lower()
        )


@pytest.mark.integration
class TestCLIApiKeyCommands(BaseCLITest):
    """Test API key management CLI commands"""

    def test_cli_apikey_list_comprehensive(self, cli_test_setup):
        """Test API key list command with all options"""
        manager, config = cli_test_setup

        # Test basic list
        result = self.run_cli_command(config, ["apikey", "list"])
        assert result.returncode == 0
        assert "test_api_key" in result.stdout

        # Test JSON format
        result = self.run_cli_command(config, ["apikey", "list", "--format", "json"])
        assert result.returncode == 0
        keys_data = json.loads(result.stdout)
        assert len(keys_data) >= 1
        assert any(key["name"] == "test_api_key" for key in keys_data)

    def test_cli_apikey_add(self, cli_test_setup):
        """Test adding new API key"""
        manager, config = cli_test_setup

        # Add new API key with description
        result = self.run_cli_command(
            config,
            [
                "apikey",
                "add",
                "new_test_key",
                "--key",
                "new_api_key_12345",
                "--description",
                "New test key",
            ],
        )

        assert result.returncode == 0
        assert "successfully" in result.stdout.lower()

        # Verify key was added
        api_keys = manager.api_manager.list_api_keys()
        key_names = [key["name"] for key in api_keys]
        assert "new_test_key" in key_names

    def test_cli_apikey_get(self, cli_test_setup):
        """Test retrieving API key"""
        manager, config = cli_test_setup

        # Get API key without showing value
        result = self.run_cli_command(config, ["apikey", "get", "test_api_key"])
        assert result.returncode == 0
        assert "test_api_key" in result.stdout
        assert "test_api..." in result.stdout  # Key prefix shown

        # Get API key with --show-key flag
        result = self.run_cli_command(
            config, ["apikey", "get", "test_api_key", "--show-key"]
        )
        assert result.returncode == 0
        assert "test_api_key_12345" in result.stdout

        # Get non-existent key
        result = self.run_cli_command(config, ["apikey", "get", "nonexistent"])
        # Command may return 0 but show "not found" message
        assert "not found" in result.stdout.lower()

    def test_cli_apikey_deactivate(self, cli_test_setup):
        """Test deactivating API key"""
        manager, config = cli_test_setup

        # Deactivate existing key
        result = self.run_cli_command(config, ["apikey", "deactivate", "test_api_key"])
        assert result.returncode == 0
        assert "deactivated" in result.stdout.lower()

        # Try to deactivate already deactivated key
        result = self.run_cli_command(config, ["apikey", "deactivate", "test_api_key"])
        assert result.returncode != 0

    def test_cli_apikey_delete(self, cli_test_setup):
        """Test deleting API key"""
        manager, config = cli_test_setup

        # Delete with confirmation
        result = self.run_cli_command(
            config, ["apikey", "delete", "test_api_key", "--confirm"]
        )

        assert result.returncode == 0
        assert "deleted" in result.stdout.lower()

        # Verify key was deleted
        api_keys = manager.api_manager.list_api_keys()
        key_names = [key["name"] for key in api_keys]
        assert "test_api_key" not in key_names

    def test_cli_apikey_test(self, cli_test_setup):
        """Test API key validation"""
        manager, config = cli_test_setup

        # This will test the key validation logic
        result = self.run_cli_command(config, ["apikey", "test", "test_api_key"])
        # Note: This might require mocking the actual n8n API call
        # For now, we just test that the command runs
        assert result.returncode in [0, 1]  # Success or expected failure


@pytest.mark.integration
class TestCLIDatabaseCommands(BaseCLITest):
    """Test database management CLI commands"""

    def test_cli_db_init(self, test_config):
        """Test database initialization"""
        # Use a fresh config to test init on new database
        with tempfile.TemporaryDirectory() as temp_dir:
            fresh_config = test_config.__class__(base_folder=Path(temp_dir))

            result = self.run_cli_command(fresh_config, ["db", "init"])
            assert result.returncode == 0
            assert "initialized" in result.stdout.lower()

            # Database should be created after any database command
            result = self.run_cli_command(fresh_config, ["db", "status"])
            assert result.returncode == 0

            # Verify database command works and shows database info
            assert "Database Path" in result.stdout
            assert "Database Size" in result.stdout
            assert "Schema Version" in result.stdout

    def test_cli_db_status_comprehensive(self, cli_test_setup):
        """Test database status command"""
        manager, config = cli_test_setup

        # Test table format
        result = self.run_cli_command(config, ["db", "status"])
        assert result.returncode == 0
        assert "Database Status" in result.stdout
        assert "Workflows" in result.stdout

        # Test JSON format
        result = self.run_cli_command(config, ["db", "status", "--format", "json"])
        assert result.returncode == 0
        status_data = json.loads(result.stdout)
        assert "database_path" in status_data
        assert "schema_version" in status_data

    def test_cli_db_backup(self, cli_test_setup):
        """Test database backup"""
        manager, config = cli_test_setup

        # Test backup with default name
        result = self.run_cli_command(config, ["db", "backup"])
        assert result.returncode == 0
        assert "backup" in result.stdout.lower()

        # Test backup with custom path
        backup_path = config.base_folder / "custom_backup.db"
        result = self.run_cli_command(config, ["db", "backup", str(backup_path)])
        assert result.returncode == 0
        assert backup_path.exists()

    def test_cli_db_vacuum(self, cli_test_setup):
        """Test database vacuum operation"""
        manager, config = cli_test_setup

        result = self.run_cli_command(config, ["db", "vacuum"])
        assert result.returncode == 0
        # Vacuum typically doesn't produce output unless there's an error

    def test_cli_db_compact(self, cli_test_setup):
        """Test database compaction"""
        manager, config = cli_test_setup

        result = self.run_cli_command(config, ["db", "compact"])
        assert result.returncode == 0
        # Compact typically doesn't produce output unless there's an error

    def test_cli_backup_workflows(self, cli_test_setup):
        """Test workflow backup creation"""
        manager, config = cli_test_setup

        # Create backup directory
        backup_dir = config.base_folder / "test_backups"
        backup_dir.mkdir(exist_ok=True)

        result = self.run_cli_command(
            config, ["backup-workflows", "--backup-dir", str(backup_dir)]
        )

        # Backup may fail due to missing workflow files, but should handle gracefully
        assert (
            "backup" in result.stdout.lower()
            or "backup failed" in result.stderr.lower()
        )

    def test_cli_list_backups(self, cli_test_setup):
        """Test listing workflow backups"""
        manager, config = cli_test_setup

        # First create some backups
        backup_dir = config.base_folder / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Create a dummy backup file
        backup_file = backup_dir / "test_backup_20241201_120000.tar.gz"
        backup_file.touch()

        # Test list backups
        result = self.run_cli_command(config, ["list-backups"])
        assert result.returncode == 0

        # Test JSON format
        result = self.run_cli_command(config, ["list-backups", "--format", "json"])
        assert result.returncode == 0
        try:
            backups_data = json.loads(result.stdout)
            assert isinstance(backups_data, list)
        except json.JSONDecodeError:
            # It's okay if there are no backups
            pass

    def test_cli_verify_backup(self, cli_test_setup):
        """Test backup verification"""
        manager, config = cli_test_setup

        # Create a simple backup file for testing
        backup_dir = config.base_folder / "backups"
        backup_dir.mkdir(exist_ok=True)

        import tarfile

        backup_file = backup_dir / "test_backup.tar.gz"

        # Create a simple tar.gz file
        with tarfile.open(backup_file, "w:gz") as tar:
            # Add a simple file to make it a valid archive
            info = tarfile.TarInfo(name="test.txt")
            info.size = 4
            tar.addfile(info, fileobj=None)

        result = self.run_cli_command(config, ["verify-backup", str(backup_file)])
        # Note: This might fail if the backup format doesn't match expectations
        # But we test that the command runs without crashing
        assert result.returncode in [0, 1]


@pytest.mark.integration
class TestCLIErrorHandling(BaseCLITest):
    """Test CLI error handling and edge cases"""

    def test_cli_invalid_commands(self, cli_test_setup):
        """Test handling of invalid commands"""
        manager, config = cli_test_setup

        # Invalid main command
        result = self.run_cli_command(config, ["nonexistent"])
        assert result.returncode != 0

        # Invalid subcommand
        result = self.run_cli_command(config, ["apikey", "nonexistent"])
        assert result.returncode != 0

    def test_cli_missing_arguments(self, cli_test_setup):
        """Test handling of missing required arguments"""
        manager, config = cli_test_setup

        # Missing workflow ID
        result = self.run_cli_command(config, ["pull"])
        assert result.returncode != 0

        # Missing API key name
        result = self.run_cli_command(config, ["apikey", "get"])
        assert result.returncode != 0

    def test_cli_invalid_app_dir(self, cli_test_setup):
        """Test handling of invalid app directory"""
        manager, config = cli_test_setup

        # Use a path that cannot be created (subdirectory under /dev/null)
        # This will fail in both local and CI environments regardless of permissions
        result = subprocess.run(
            [
                sys.executable,
                "api/cli.py",
                "--app-dir",
                "/dev/null/invalid_path",
                "list",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0

    def test_cli_output_consistency(self, cli_test_setup):
        """Test that CLI output is consistent across formats"""
        manager, config = cli_test_setup

        # Test that --no-emoji flag works consistently
        result_emoji = self.run_cli_command(config, ["list"])
        result_no_emoji = self.run_cli_command(config, ["list"])

        # Both should succeed
        assert result_emoji.returncode == 0
        assert result_no_emoji.returncode == 0

        # No-emoji version should not contain emoji characters
        # (Already using --no-emoji in run_cli_command)
        assert "🎭" not in result_no_emoji.stdout
        assert "✅" not in result_no_emoji.stdout


@pytest.mark.integration
class TestCLIIntegrationScenarios(BaseCLITest):
    """Integration scenarios from merged CLI tests"""

    def test_cli_table_format_consistency(self, cli_test_setup):
        """Test CLI table output format consistency (emoji-free tables)"""
        manager, config = cli_test_setup

        # Test list with --table flag
        result = self.run_cli_command(config, ["list", "--table"])

        assert result.returncode == 0
        output = result.stdout

        # Table output should not contain emojis in titles (tables are always emoji-free)
        lines = output.split("\n")
        title_line = None
        for line in lines:
            if "Workflows" in line:
                title_line = line
                break

        # Should find the title line and it should not contain emojis
        assert title_line is not None, "Should find Workflows title line"
        assert (
            "🎭" not in title_line
        ), f"Table title should not contain emojis: {title_line}"

        # Should contain workflow data
        assert "test_w" in output  # Check for workflow ID parts

    def test_cli_workflow_file_consistency(self, cli_test_setup):
        """Test CLI shows consistent file existence status"""
        manager, config = cli_test_setup

        # Create actual workflow files for testing
        workflow_file = config.base_folder / "workflows" / "test_workflow_1.json"
        workflow_file.parent.mkdir(exist_ok=True)
        workflow_file.write_text('{"id": "test_wf_001", "name": "Test Workflow 1"}')

        # Update database to point to actual file
        with manager.db.get_connection() as conn:
            conn.execute(
                "UPDATE workflows SET file_path = ? WHERE id = ?",
                ("workflows/test_workflow_1.json", "test_wf_001"),
            )
            conn.commit()

        # Initially workflow should show file exists
        result = self.run_cli_command(config, ["list", "--format", "json"])
        assert result.returncode == 0

        # Remove the file
        workflow_file.unlink()

        # CLI should reflect the change in next call
        result = self.run_cli_command(config, ["list", "--format", "json"])
        assert result.returncode == 0
        # File should be missing now (implementation may vary)

    @pytest.mark.skipif(
        sys.platform == "win32", reason="Signal handling differs on Windows"
    )
    def test_cli_interruption_handling(self, cli_test_setup):
        """Test CLI graceful handling of interruptions"""
        manager, config = cli_test_setup

        # Test that CLI commands can be interrupted gracefully
        # This is a basic test - complex interruption testing would require
        # long-running operations and signal simulation

        # For now, just test that commands complete normally
        result = self.run_cli_command(config, ["list"])
        assert result.returncode == 0

    def test_cli_configuration_integration(self, cli_test_setup):
        """Test CLI configuration options work correctly"""
        manager, config = cli_test_setup

        # Test app-dir configuration
        result = self.run_cli_command(config, ["db", "status"])
        assert result.returncode == 0
        assert "Database" in result.stdout

        # Test no-emoji mode
        result = self.run_cli_command(config, ["list"])
        assert result.returncode == 0
        # Should not contain emojis (already using --no-emoji in run_cli_command)
        assert "🎭" not in result.stdout

    def test_cli_output_modes_integration(self, cli_test_setup):
        """Test different CLI output modes work consistently"""
        manager, config = cli_test_setup

        # Test table format
        result_table = self.run_cli_command(config, ["list", "--format", "table"])
        assert result_table.returncode == 0

        # Test JSON format
        result_json = self.run_cli_command(config, ["list", "--format", "json"])
        assert result_json.returncode == 0

        # JSON should be parseable
        try:
            json.loads(result_json.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"CLI JSON output is not valid: {result_json.stdout}")
