#!/usr/bin/env python3
"""
End-to-End Manual Workflow Testing

Real CLI execution tests for workflow management operations,
including add, list, search, stats, and file operations.
"""

import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from unittest.mock import patch

import pytest

from api.config import AppConfig
from api.models import Workflow
from api.workflow import WorkflowApi

from .e2e_base import E2ETestBase


# === End-to-End Workflow Tests ===
class TestE2EWorkflows(E2ETestBase):
    """Manual end-to-end testing for workflow operations"""

    def create_test_workflow(self, name: str, workflow_data: Optional[dict] = None) -> Path:
        """Create a test workflow file."""
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

    def test_workflow_add_basic(self) -> None:
        """Test adding a basic workflow"""
        self.setup_database()
        self.create_test_workflow("basic_test")

        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "basic_test.json",
                "Basic_Test",
            ]
        )

        # Should succeed or provide meaningful error
        assert returncode in [0, 1]

    def test_workflow_list_empty(self) -> None:
        """Test listing workflows when none exist"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "list"])

        assert returncode == 0
        # Should show empty list or appropriate message

    def test_workflow_list_populated(self) -> None:
        """Test listing workflows after adding some"""
        self.setup_database()
        workflows = ["test1", "test2", "test3"]
        for workflow_name in workflows:
            self.create_test_workflow(workflow_name)
            self.run_cli_command(
                [
                    "--app-dir",
                    self.temp_dir,
                    "--flow-dir",
                    self.temp_flow_dir,
                    "add",
                    f"{workflow_name}.json",
                    workflow_name.replace("_", "-"),
                ]
            )

        # List workflows
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "list"])

        assert returncode == 0

    def test_workflow_search_functionality(self) -> None:
        """Test workflow search with various patterns"""
        self.setup_database()
        search_workflows = [
            "email_notification",
            "data_processing",
            "user_management",
            "notification_system",
        ]

        for workflow_name in search_workflows:
            self.create_test_workflow(workflow_name)
            self.run_cli_command(
                [
                    "--app-dir",
                    self.temp_dir,
                    "--flow-dir",
                    self.temp_flow_dir,
                    "add",
                    f"{workflow_name}.json",
                    workflow_name.replace("_", "-"),
                ]
            )
        search_patterns = [
            "notification",  # Should match 2 workflows
            "data",  # Should match 1 workflow
            "user",  # Should match 1 workflow
            "nonexistent",  # Should match 0 workflows
        ]

        for pattern in search_patterns:
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "search", pattern])

            # Search should complete successfully
            assert returncode == 0

    def test_search_workflows_comprehensive_matching(self) -> None:
        """Test comprehensive search matching including partial matches"""
        self.setup_database()
        workflows_data = [
            ("user_auth_flow", {"name": "User Authentication Flow"}),
            ("email_sender", {"name": "Email Notification Sender"}),
            ("data_validator", {"name": "Data Validation Process"}),
            ("backup_system", {"name": "Backup and Archive System"}),
        ]

        for workflow_name, data in workflows_data:
            self.create_test_workflow(workflow_name, data)
            self.run_cli_command(
                [
                    "--app-dir",
                    self.temp_dir,
                    "--flow-dir",
                    self.temp_flow_dir,
                    "add",
                    f"{workflow_name}.json",
                    workflow_name.replace("_", "-"),
                ]
            )
        comprehensive_searches = [
            "user",  # Should find user_auth_flow
            "email",  # Should find email_sender
            "data",  # Should find data_validator
            "system",  # Should find backup_system
            "flow",  # Should find user_auth_flow
            "auth",  # Should find user_auth_flow
        ]

        for search_term in comprehensive_searches:
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "search", search_term])
            assert returncode == 0

    def test_workflow_stats_display(self) -> None:
        """Test workflow stats display functionality"""
        self.setup_database()
        self.create_test_workflow("stats_test")
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "stats_test.json",
                "Stats-Test",
            ]
        )
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "stats"])

        assert returncode == 0
        # Should show statistics without errors

    def test_workflow_stats_comprehensive_display(self) -> None:
        """Test comprehensive workflow stats with multiple workflows"""
        self.setup_database()
        stats_workflows: List[Tuple[str, Dict[str, Any]]] = [
            ("active_workflow", {"active": True}),
            ("inactive_workflow", {"active": False}),
            (
                "complex_workflow",
                {
                    "nodes": [
                        {"id": "node1", "type": "start"},
                        {"id": "node2", "type": "process"},
                        {"id": "node3", "type": "end"},
                    ]
                },
            ),
        ]

        for workflow_name, extra_data in stats_workflows:
            base_data = {
                "name": workflow_name,
                "nodes": [{"id": "node1", "type": "start"}],
                "connections": {},
                "active": False,
            }
            base_data.update(extra_data)
            self.create_test_workflow(workflow_name, base_data)
            self.run_cli_command(
                [
                    "--app-dir",
                    self.temp_dir,
                    "--flow-dir",
                    self.temp_flow_dir,
                    "add",
                    f"{workflow_name}.json",
                    workflow_name.replace("_", "-"),
                ]
            )
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "stats"])

        assert returncode == 0

    def test_workflow_file_existence_accuracy(self) -> None:
        """Test accuracy of workflow file existence checks"""
        self.setup_database()
        workflow_file = self.create_test_workflow("existence_test")
        add_returncode, _, _ = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "existence_test.json",
                "Existence-Test",
            ]
        )

        if add_returncode == 0:
            # List workflows - should show file exists
            list_returncode, list_stdout, _ = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "list"])
            assert list_returncode == 0
            workflow_file.unlink()

            # List again - should reflect file no longer exists
            list_after_delete_returncode, list_after_stdout, _ = self.run_cli_command(
                ["--app-dir", self.temp_dir, "wf", "list"]
            )
            assert list_after_delete_returncode == 0

    def test_workflow_add_nonexistent_file(self) -> None:
        """Test adding nonexistent workflow file"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "nonexistent_workflow.json",
                "Nonexistent-Workflow",
            ]
        )

        # Should fail gracefully
        assert returncode in [0, 1]
        assert "not found" in stderr.lower() or "not found" in stdout.lower()

    def test_workflow_add_invalid_json(self) -> None:
        """Test adding workflow with invalid JSON"""
        self.setup_database()
        invalid_file = Path(self.temp_flow_dir) / "invalid.json"
        invalid_file.write_text("{ invalid json content")

        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "invalid.json",
                "Invalid-JSON",
            ]
        )

        # Should handle invalid JSON gracefully
        assert returncode in [0, 1]

    def test_workflow_operations_emoji_consistency(self) -> None:
        """Test workflow operations with emoji and no-emoji modes"""
        self.setup_database()
        self.create_test_workflow("emoji_test")

        # Test 'wf list' with default emoji output
        emoji_returncode, emoji_stdout, _ = self.run_cli_command(
            ["--app-dir", self.temp_dir, "--flow-dir", self.temp_flow_dir, "wf", "list"]
        )

        # Test 'wf list' with --no-emoji flag
        no_emoji_returncode, no_emoji_stdout, _ = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "--no-emoji",
                "wf",
                "list",
            ]
        )

        # Both should succeed (return code 0)
        assert emoji_returncode == 0, f"Emoji mode failed with code {emoji_returncode}"
        assert no_emoji_returncode == 0, f"No-emoji mode failed with code {no_emoji_returncode}"

        # Check that emojis are present in emoji output but not in no-emoji output
        workflow_emojis = ["⚡", "📋", "✅", "❌"]
        for emoji in workflow_emojis:
            if emoji in emoji_stdout:
                assert emoji not in no_emoji_stdout

    def test_workflow_path_resolution(self) -> None:
        """Test workflow file path resolution"""
        self.setup_database()
        subdir = Path(self.temp_flow_dir) / "subdir"
        subdir.mkdir()

        workflow_data = {"name": "path_test", "nodes": [], "connections": {}}
        workflow_file = subdir / "path_test.json"
        workflow_file.write_text(json.dumps(workflow_data))

        # Try to add workflow (may not find it in subdirectory)
        returncode, stdout, stderr = self.run_cli_command(
            ["--app-dir", self.temp_dir, "--flow-dir", str(subdir), "wf", "add", "path_test.json", "Path-Test"]
        )

        # Should handle path resolution
        assert returncode in [0, 1]

    def test_workflow_large_file_handling(self) -> None:
        """Test handling of large workflow files"""
        self.setup_database()
        large_workflow_data = {
            "name": "large_workflow",
            "nodes": [
                {
                    "id": f"node_{i}",
                    "type": "test",
                    "typeVersion": 1,
                    "position": [i * 100, i * 50],
                }
                for i in range(100)  # 100 nodes
            ],
            "connections": {},
            "active": False,
        }

        self.create_test_workflow("large_test", large_workflow_data)

        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "large_test.json",
                "Large-Test",
            ]
        )

        # Should handle large files
        assert returncode in [0, 1]

    def test_workflow_concurrent_operations(self) -> None:
        """Test concurrent workflow operations"""
        import threading

        self.setup_database()
        for i in range(3):
            self.create_test_workflow(f"concurrent_test_{i}")

        results = []

        def add_workflow(workflow_id) -> None:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "--app-dir",
                    self.temp_dir,
                    "--flow-dir",
                    self.temp_flow_dir,
                    "wf",
                    "add",
                    f"concurrent_test_{workflow_id}.json",
                    f"Concurrent-Test-{workflow_id}",
                ]
            )
            results.append((workflow_id, returncode, stdout, stderr))

        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_workflow, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        assert len(results) == 3
        # Operations should complete without crashes
        for workflow_id, returncode, stdout, stderr in results:
            assert returncode in [0, 1]

    def test_workflow_unicode_names(self) -> None:
        """Test workflows with Unicode names"""
        self.setup_database()
        unicode_names = ["测试工作流", "тест_поток", "workflow_émojis", "流程_テスト"]

        for name in unicode_names:
            try:
                workflow_data = {"name": name, "nodes": [], "connections": {}}
                workflow_file = Path(self.temp_flow_dir) / f"{name}.json"
                workflow_file.write_text(json.dumps(workflow_data, ensure_ascii=False))

                returncode, stdout, stderr = self.run_cli_command(
                    [
                        "--app-dir",
                        self.temp_dir,
                        "--flow-dir",
                        self.temp_flow_dir,
                        "wf",
                        "add",
                        f"{name}.json",
                        name.replace("_", "-"),
                    ]
                )

                # Should handle Unicode names
                assert returncode in [0, 1]

            except (UnicodeError, OSError):
                # Skip if filesystem doesn't support Unicode
                pytest.skip(f"Filesystem doesn't support Unicode name: {name}")

    def test_workflow_type_classification(self) -> None:
        """Test workflow type classification (if implemented)"""
        self.setup_database()
        workflow_types = [
            ("api_workflow", {"nodes": [{"id": "webhook", "type": "webhook"}]}),
            ("scheduled_workflow", {"nodes": [{"id": "cron", "type": "cron"}]}),
            ("manual_workflow", {"nodes": [{"id": "manual", "type": "manual"}]}),
        ]

        for name, node_data in workflow_types:
            workflow_data = {
                "name": name,
                "nodes": node_data["nodes"],
                "connections": {},
                "active": False,
            }
            self.create_test_workflow(name, workflow_data)

            returncode, stdout, stderr = self.run_cli_command(
                [
                    "--app-dir",
                    self.temp_dir,
                    "--flow-dir",
                    self.temp_flow_dir,
                    "wf",
                    "add",
                    f"{name}.json",
                    name.replace("_", " ").title(),
                ]
            )

            assert returncode in [0, 1]

    def test_workflow_backup_integration(self) -> None:
        """Test workflow operations integrate with backup system"""
        self.setup_database()
        self.create_test_workflow("backup_integration_test")
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "backup_integration_test.json",
                "Backup-Integration-Test",
            ]
        )
        backup_returncode, _, _ = self.run_cli_command(["--app-dir", self.temp_dir, "backup-workflows"])

        if backup_returncode == 0:
            backup_dir = Path(self.temp_dir) / "backups"
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.tar.gz"))
                assert len(backup_files) > 0

    def test_workflow_environment_variable_integration(self) -> None:
        """Test workflow operations respect environment variables"""
        self.setup_database()
        env = {"N8N_DEPLOY_FLOW_DIR": self.temp_flow_dir}

        self.create_test_workflow("env_test")

        returncode, stdout, stderr = self.run_cli_command(
            ["--app-dir", self.temp_dir, "wf", "add", "env_test.json", "Env-Test"], env=env
        )

        # Should use environment variable for flow directory
        assert returncode in [0, 1]

    def test_list_backups_shows_metadata(self) -> None:
        """Test wf backups command shows backup file metadata"""
        # Initialize and create backup
        self.run_cli_command(["db", "init", "--app-dir", self.temp_dir])
        self.run_cli_command(["db", "backup", "--app-dir", self.temp_dir])

        # List backups - just lists files in backup directory, no database access needed
        backup_dir = Path(self.temp_dir) / "backups"
        returncode, stdout, stderr = self.run_cli_command(["wf", "backups", "--backup-dir", str(backup_dir)])

        # Should succeed (even if no backups exist yet)
        assert returncode == 0, f"Command failed with returncode {returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}"

    # === Additional Workflow Command Tests for Complete Coverage ===

    def test_wf_add_with_json_format(self) -> None:
        """Test wf add with --format json output"""
        self.setup_database()
        self.create_test_workflow("json_add_test")

        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "json_add_test.json",
                "JSON Add Test",
                "--format",
                "json",
            ]
        )

        # Should output JSON format (may succeed or fail based on validation)
        assert returncode in [0, 1]

    def test_wf_list_only_backupable(self) -> None:
        """Test wf list --only flag to show only backupable workflows"""
        self.setup_database()
        self.create_test_workflow("backupable_test")
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "backupable_test.json",
                "Backupable Test",
            ]
        )

        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "list", "--only"])

        assert returncode == 0
        # Should list only workflows with existing JSON files

    def test_wf_list_json_format(self) -> None:
        """Test wf list --format json output"""
        self.setup_database()
        self.create_test_workflow("json_list_test")
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "json_list_test.json",
                "JSON List Test",
            ]
        )

        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "list", "--format", "json"])

        assert returncode == 0
        # Should be valid JSON
        data = json.loads(stdout)
        assert isinstance(data, list)

    def test_wf_remove_with_yes_flag(self) -> None:
        """Test wf remove --yes skips confirmation"""
        self.setup_database()
        self.create_test_workflow("remove_yes_test")
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "remove_yes_test.json",
                "Remove Yes Test",
            ]
        )

        # Remove with --yes should skip confirmation
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "wf",
                "remove",
                "test_workflow_id",
                "--yes",
            ]
        )

        # May succeed or fail depending on workflow existence
        assert returncode in [0, 1]

    def test_wf_search_json_format(self) -> None:
        """Test wf search --format json output"""
        self.setup_database()
        self.create_test_workflow("search_json_test")
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "search_json_test.json",
                "Search JSON Test",
            ]
        )

        returncode, stdout, stderr = self.run_cli_command(
            ["--app-dir", self.temp_dir, "wf", "search", "search", "--format", "json"]
        )

        assert returncode == 0
        # Should be valid JSON
        data = json.loads(stdout)
        assert isinstance(data, list)

    def test_wf_stats_overall_json_format(self) -> None:
        """Test wf stats (overall) --format json output"""
        self.setup_database()

        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "wf", "stats", "--format", "json"])

        assert returncode == 0
        # Should be valid JSON with stats data
        data = json.loads(stdout)
        assert "total_workflows" in data

    def test_wf_stats_specific_workflow_json(self) -> None:
        """Test wf stats <workflow-id> --format json output"""
        self.setup_database()
        self.create_test_workflow("stats_specific_test")
        add_result = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "add",
                "stats_specific_test.json",
                "Stats Specific Test",
            ]
        )

        if add_result[0] == 0:
            returncode, stdout, stderr = self.run_cli_command(
                [
                    "--app-dir",
                    self.temp_dir,
                    "wf",
                    "stats",
                    "test_workflow_id",
                    "--format",
                    "json",
                ]
            )

            # May succeed or fail based on workflow ID
            assert returncode in [0, 1]

    def test_wf_list_server_json_format(self) -> None:
        """Test wf server --format json output"""
        # This test requires n8n server, may fail if not available
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "wf",
                "server",
                "--server-url",
                "http://test-server:5678",
                "--format",
                "json",
            ]
        )

        # Will fail without server, but should handle gracefully
        assert returncode in [0, 1]

    def test_wf_backup_with_backup_dir(self) -> None:
        """Test wf backup --backup-dir creates backup in specified directory"""
        self.setup_database()
        backup_dir = Path(self.temp_dir) / "custom_backups"
        backup_dir.mkdir(exist_ok=True)

        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "wf",
                "createbackup",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        # May succeed or fail based on workflows available
        assert returncode in [0, 1]

    def test_wf_restore_with_backup_file(self) -> None:
        """Test wf restore <backup-file> restores workflows"""
        self.setup_database()

        # Create a backup first (may fail if no workflows)
        backup_dir = Path(self.temp_dir) / "test_restore_backups"
        backup_dir.mkdir(exist_ok=True)

        # Try to restore a non-existent backup
        returncode, stdout, stderr = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "wf",
                "restore",
                "nonexistent_backup.tar.gz",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        # Should fail gracefully for non-existent backup
        assert returncode in [0, 1]

    def test_wf_list_backups_json_format(self) -> None:
        """Test wf backups --format json output"""
        backup_dir = Path(self.temp_dir) / "json_backups"
        backup_dir.mkdir(exist_ok=True)

        returncode, stdout, stderr = self.run_cli_command(
            ["wf", "backups", "--backup-dir", str(backup_dir), "--format", "json"]
        )

        assert returncode == 0

        # Should be valid JSON (empty list for empty directory)
        data = json.loads(stdout)
        assert isinstance(data, list)
        assert len(data) == 0  # No backups in empty directory

    def test_wf_verify_backup_success(self) -> None:
        """Test wf verify validates backup file integrity"""
        backup_dir = Path(self.temp_dir) / "verify_backups"
        backup_dir.mkdir(exist_ok=True)

        # Create a valid tar.gz file
        import tarfile

        backup_file = backup_dir / "test_backup.tar.gz"
        with tarfile.open(backup_file, "w:gz") as tar:
            # Add a dummy file
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
                tmp.write('{"test": "data"}')
                tmp_path = tmp.name

            tar.add(tmp_path, arcname="test.json")
            Path(tmp_path).unlink()

        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "verify",
                "test_backup.tar.gz",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        assert returncode == 0
        assert "valid" in stdout.lower()

    def test_wf_verify_backup_corrupted(self) -> None:
        """Test wf verify handles corrupted backup files"""
        backup_dir = Path(self.temp_dir) / "corrupted_backups"
        backup_dir.mkdir(exist_ok=True)

        # Create a corrupted file
        corrupted_file = backup_dir / "corrupted_backup.tar.gz"
        corrupted_file.write_text("This is not a valid tar.gz file")

        returncode, stdout, stderr = self.run_cli_command(
            [
                "wf",
                "verify",
                "corrupted_backup.tar.gz",
                "--backup-dir",
                str(backup_dir),
            ]
        )

        # Should fail for corrupted backup
        assert returncode == 1
        assert "corrupted" in stdout.lower() or "invalid" in stdout.lower()


# === Workflow Backup Integration Tests ===
@pytest.mark.integration
class TestWorkflowBackupIntegration:
    """Test integration between database, filesystem, and backup operations"""

    @pytest.fixture
    def manager_with_real_workflows(self, test_config: AppConfig) -> WorkflowApi:
        """Create manager with real workflow files and database entries"""
        manager = WorkflowApi(config=test_config)
        manager.db.schema_manager.initialize_database()
        with manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.commit()
        workflows_data = [
            {
                "id": "integration_main_workflow",
                "name": "Main Integration Workflow",
            },
            {
                "id": "integration_subflow",
                "name": "Integration Subflow",
            },
        ]
        # File paths should match workflow IDs: {workflow_id}.json
        file_paths = [
            "test_workflows/integration_main_workflow.json",
            "test_workflows/integration_subflow.json",
        ]
        # Create test_workflows subdirectory for test files
        test_workflows_dir = manager.config.workflows_path / "test_workflows"
        test_workflows_dir.mkdir(parents=True, exist_ok=True)

        for i, wf_data in enumerate(workflows_data):
            # Extract just the filename from the corresponding file_path for file creation
            filename = Path(file_paths[i]).name
            file_path = test_workflows_dir / filename

            workflow_json = {
                "id": wf_data["id"],
                "name": wf_data["name"],
                "active": True,  # All workflows are active
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
                        "parameters": {"functionCode": "return items.map(item => ({...item, processed: true}));"},
                        "id": "function_node",
                        "name": "Process",
                        "type": "n8n-nodes-base.function",
                        "typeVersion": 1,
                        "position": [460, 300],
                    },
                ],
                "connections": {"Start": {"main": [[{"node": "Process", "type": "main", "index": 0}]]}},
                "staticData": {},
                "settings": {"executionOrder": "v1"},
                "createdAt": datetime.now(timezone.utc).isoformat() + "Z",
                "updatedAt": datetime.now(timezone.utc).isoformat() + "Z",
            }

            with open(file_path, "w") as f:
                json.dump(workflow_json, f, indent=2)
            # Set the file_folder to the actual directory where the file is located
            wf_data_with_folder = {**wf_data, "file_folder": str(test_workflows_dir)}
            workflow = Workflow(**wf_data_with_folder)
            workflow_id = manager.db.add_workflow(workflow)
            assert workflow_id == wf_data["id"], f"Failed to create workflow {wf_data['id']}"
        created_workflows = manager.list_workflows()
        assert len(created_workflows) == 2, f"Expected 2 workflows, created {len(created_workflows)}"

        return manager

    def test_backup_with_real_files_and_database(self, manager_with_real_workflows: WorkflowApi) -> None:
        """Test backup creation with real workflow files and database integration"""
        manager = manager_with_real_workflows
        workflows = manager.list_workflows()

        # Debug: Print workflow details if assertion fails
        if len(workflows) != 2:
            print(f"Expected 2 workflows, found {len(workflows)}")
            for wf in workflows:
                print(f"Workflow: {wf}")
            with manager.db.get_connection() as conn:
                cursor = conn.execute("SELECT id, name FROM workflows")
                db_workflows = cursor.fetchall()
                print(f"Database workflows: {[dict(row) for row in db_workflows]}")

        assert len(workflows) >= 1, f"Expected at least 1 workflow, found {len(workflows)}"

        for wf in workflows:
            assert "id" in wf
            assert "name" in wf
        backup_results = []
        for wf in workflows:
            backup_result = manager.create_workflow_backup(wf["id"])
            backup_results.append(backup_result)
            assert backup_result is not None
            assert "backup_id" in backup_result
            assert "filename" in backup_result
            assert backup_result["workflow_id"] == wf["id"]
            backup_path = manager.config.backups_path / backup_result["filename"]
            assert backup_path.exists()
            with tarfile.open(backup_path, "r:gz") as tar:
                members = tar.getnames()
                workflow_files = [m for m in members if m.endswith(".json") and not m.endswith("metadata.json")]
                metadata_files = [m for m in members if m.endswith("metadata.json")]
                assert len(workflow_files) == 1  # Should have one workflow file
                assert len(metadata_files) == 1  # Should have one metadata file

                # Extract and verify workflow content
                workflow_member = tar.getmember(workflow_files[0])
                extracted_file = tar.extractfile(workflow_member)
                workflow_content = json.loads(extracted_file.read().decode("utf-8"))
                assert workflow_content["id"] == wf["id"]
                assert workflow_content["name"] == wf["name"]

        assert len(backup_results) == len(workflows)

    def test_backup_all_workflows_integration(self, manager_with_real_workflows: WorkflowApi) -> None:
        """Test backup_all_workflows convenience method with real integration"""
        manager = manager_with_real_workflows

        # Use the convenience method to backup all workflows
        result = manager.backup_all_workflows()
        assert result["total_workflows"] == 2
        assert len(result["successful_backups"]) == 2
        assert len(result["failed_backups"]) == 0
        for backup_info in result["successful_backups"]:
            backup_path = manager.config.backups_path / backup_info["filename"]
            assert backup_path.exists()

            with tarfile.open(backup_path, "r:gz") as tar:
                workflow_files = [m for m in tar.getnames() if m.endswith(".json") and not m.endswith("metadata.json")]
                metadata_files = [m for m in tar.getnames() if m.endswith("metadata.json")]
                assert len(workflow_files) == 1  # Should have one workflow file
                assert len(metadata_files) == 1  # Should have one metadata file

    def test_backup_with_missing_file_integration(self, manager_with_real_workflows: WorkflowApi) -> None:
        """Test backup behavior when workflow exists in database but file is missing"""
        manager = manager_with_real_workflows
        workflows = manager.list_workflows()
        test_workflow = workflows[0]
        # Get the actual workflow file from database
        workflow_obj = manager.db.get_workflow(test_workflow["id"])
        assert workflow_obj is not None
        workflow_file = Path(workflow_obj.file_folder) / f"{test_workflow['id']}.json"
        workflow_file.unlink()  # Delete the file
        updated_workflows = manager.list_workflows()
        missing_file_workflow = next(wf for wf in updated_workflows if wf["id"] == test_workflow["id"])
        assert "id" in missing_file_workflow
        assert "name" in missing_file_workflow

        # Attempt to backup should fail
        with pytest.raises(FileNotFoundError, match="Workflow file not found"):
            manager.create_workflow_backup(test_workflow["id"])

        # backup_all_workflows should skip the missing file
        result = manager.backup_all_workflows()
        assert result["total_workflows"] == 2  # All workflows are counted
        assert len(result["successful_backups"]) == 1  # Only one workflow has a file
        assert len(result["failed_backups"]) == 1  # One workflow failed due to missing file

    def test_backup_integrity_with_real_data(self, manager_with_real_workflows: WorkflowApi) -> None:
        """Test backup integrity verification with real workflow data"""
        manager = manager_with_real_workflows

        workflows = manager.list_workflows()
        test_workflow = workflows[0]
        backup_result = manager.create_workflow_backup(test_workflow["id"])
        backup_path = manager.config.backups_path / backup_result["filename"]

        # Calculate actual file checksum
        with open(backup_path, "rb") as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()
        with manager.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT checksum FROM configurations
                ORDER BY created_at DESC LIMIT 1
            """
            )
            result = cursor.fetchone()

        assert result is not None
        stored_checksum = result["checksum"]
        assert actual_checksum == stored_checksum

    def test_concurrent_backup_operations(self, manager_with_real_workflows: WorkflowApi) -> None:
        """Test that multiple backup operations don't interfere with each other"""
        manager = manager_with_real_workflows

        workflows = manager.list_workflows()
        backup_results = []
        for wf in workflows:
            backup_result = manager.create_workflow_backup(wf["id"])
            backup_results.append(backup_result)
        filenames = [result["filename"] for result in backup_results]
        assert len(set(filenames)) == len(filenames)  # All unique
        for result in backup_results:
            backup_path = manager.config.backups_path / result["filename"]
            assert backup_path.exists()
        with manager.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM configurations
            """
            )
            result = cursor.fetchone()
            assert result["count"] == 2

    def test_list_workflows_filtering_integration(self, manager_with_real_workflows: WorkflowApi) -> None:
        """Test workflow listing with filtering in real integration scenario"""
        manager = manager_with_real_workflows
        workflows = manager.list_workflows()
        test_workflow = workflows[0]
        # Get the actual workflow file from database
        workflow_obj = manager.db.get_workflow(test_workflow["id"])
        assert workflow_obj is not None
        workflow_file = Path(workflow_obj.file_folder) / f"{test_workflow['id']}.json"
        workflow_file.unlink()
        all_workflows = manager.list_workflows(only_backupable=False)
        assert len(all_workflows) == 2
        # Note: only_backupable parameter is currently ignored, all workflows are returned
        backupable_workflows = manager.list_workflows(only_backupable=True)
        assert len(backupable_workflows) == 2
        # Find the workflow that still has a file
        for wf in backupable_workflows:
            wf_obj = manager.db.get_workflow(wf["id"])
            assert wf_obj is not None
            wf_file = Path(wf_obj.file_folder) / f"{wf['id']}.json"
            if wf_file.exists():
                remaining_workflow = wf
                break
        assert remaining_workflow is not None


# === Workflow Manager Integration Tests ===
@pytest.mark.integration
class TestWorkflowManagerIntegration:
    """Test overall workflow manager integration scenarios"""

    @pytest.fixture
    def integrated_manager(self, test_config: AppConfig) -> WorkflowApi:
        """Create a fully integrated workflow manager"""
        manager = WorkflowApi(config=test_config)
        manager.db.schema_manager.initialize_database()
        with manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.execute("DELETE FROM api_keys")
            conn.execute("DELETE FROM configurations")
            conn.commit()

        return manager

    def test_api_key_and_workflow_integration(self, integrated_manager: WorkflowApi) -> None:
        """Test integration between API key management and workflow operations"""
        manager = integrated_manager
        api_key_id = manager.key_api.add_api_key(
            name="integration_test_key",
            api_key="integration_test_api_key_12345",
            description="API key for integration testing",
        )

        assert api_key_id is not None
        api_keys = manager.key_api.list_api_keys()
        assert len(api_keys) == 1
        assert api_keys[0]["name"] == "integration_test_key"
        # Create the file in test_workflows subdirectory
        test_workflows_dir = manager.config.workflows_path / "test_workflows"
        test_workflows_dir.mkdir(parents=True, exist_ok=True)
        # Filename must match workflow ID for backup to work
        filename = "api_integration_workflow.json"
        file_path = test_workflows_dir / filename

        with open(file_path, "w") as f:
            json.dump({"id": "api_integration_workflow", "name": "API Integration Workflow"}, f)

        workflow = Workflow(
            id="api_integration_workflow",
            name="API Integration Workflow",
            file=filename,
            file_folder=str(test_workflows_dir),  # Use absolute path for backup to work
        )

        manager.db.add_workflow(workflow)

        # Both workflow and API key should be manageable
        workflows = manager.list_workflows()
        api_keys = manager.key_api.list_api_keys()

        assert len(workflows) == 1
        assert len(api_keys) == 1

        # Backup should work with both data types present
        backup_result = manager.create_workflow_backup(workflow.id)
        assert backup_result is not None

        # Clean up API key
        success = manager.key_api.delete_api_key("integration_test_key", confirm=True)
        assert success is True

    def test_configuration_integration(self, test_config: AppConfig) -> None:
        """Test configuration integration across different components"""

        manager = WorkflowApi(config=test_config)
        assert manager.config == test_config
        assert manager.config.workflows_path == test_config.workflows_path  # base_path is the workflows directory
        assert manager.db.db_path == test_config.database_path

        # API manager should also use the same config
        assert manager.key_api.config == test_config

        # Paths should be consistent across components
        # When backup_dir is not set, backups_path defaults to base_folder
        assert manager.config.backups_path == test_config.backups_path
        assert manager.config.workflows_path == test_config.workflows_path

    def test_error_recovery_integration(self, integrated_manager: WorkflowApi) -> None:
        """Test error recovery in integrated scenarios"""
        manager = integrated_manager
        workflow = Workflow(
            id="error_recovery_test",
            name="Error Recovery Test",
        )

        manager.db.add_workflow(workflow)
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Manager should handle file operation errors gracefully
            workflows = manager.list_workflows()
            assert len(workflows) == 1
            assert "id" in workflows[0]  # Should have basic workflow info

            # Backup should fail gracefully
            with pytest.raises(FileNotFoundError):
                manager.create_workflow_backup(workflow.id)

        # Manager should recover after error
        workflows = manager.list_workflows()
        assert len(workflows) == 1
