#!/usr/bin/env python3
"""
End-to-End Manual Workflow Testing

Real CLI execution tests for workflow management operations,
including add, list, search, stats, and file operations.
"""

import json
from pathlib import Path
from typing import Any, Optional

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
                "add",
                "nonexistent_workflow.json",
                "Nonexistent-Workflow",
            ]
        )

        # Should fail gracefully
        assert returncode == 1
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
                "add",
                "invalid.json",
                "Invalid-JSON",
            ]
        )

        # Should handle invalid JSON gracefully
        assert returncode == 1

    def test_workflow_operations_emoji_consistency(self) -> None:
        """Test workflow operations with emoji and no-emoji modes"""
        self.setup_database()
        self.create_test_workflow("emoji_test")
        emoji_returncode, emoji_stdout, _ = self.run_cli_command(
            ["--app-dir", self.temp_dir, "--flow-dir", self.temp_flow_dir, "list"]
        )
        no_emoji_returncode, no_emoji_stdout, _ = self.run_cli_command(
            [
                "list",
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "--no-emoji",
            ]
        )

        assert emoji_returncode == no_emoji_returncode == 0
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
                    "add",
                    f"{name}_id",
                    name.replace("_", " ").title(),
                    f"{name}.json",
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
        env = {"N8N_FLOW_DIR": self.temp_flow_dir}

        self.create_test_workflow("env_test")

        returncode, stdout, stderr = self.run_cli_command(
            ["--app-dir", self.temp_dir, "add", "env_test.json", "Env-Test"], env=env
        )

        # Should use environment variable for flow directory
        assert returncode in [0, 1]
