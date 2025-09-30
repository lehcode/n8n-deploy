#!/usr/bin/env python3
"""
Integration tests for workflow backup functionality with real files and database
"""

import hashlib
import json
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from api.config import AppConfig
from api.models import Workflow
from api.workflow import WorkflowApi

os.environ["N8N_DEPLOY_TESTING"] = "1"


@pytest.mark.integration
# === Workflow Backup Integration Tests ===
class TestWorkflowBackupIntegration:
    """Test integration between database, filesystem, and backup operations"""

    @pytest.fixture
    def manager_with_real_workflows(self, test_config: AppConfig) -> WorkflowApi:
        """Create manager with real workflow files and database entries"""
        manager = WorkflowApi(config=test_config)
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
            workflow_id = manager.db.create_workflow(workflow)
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
        workflow_file = manager.config.workflows_path / test_workflow["file"]
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
        assert result["total_workflows"] == 1  # Only backupable workflows are counted
        assert len(result["successful_backups"]) == 1  # Only one workflow has a file
        assert len(result["failed_backups"]) == 0  # Non-backupable workflows are filtered out

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
                SELECT config_data FROM configurations
                WHERE config_type = 'backup_metadata'
                ORDER BY created_at DESC LIMIT 1
            """
            )
            result = cursor.fetchone()

        assert result is not None
        stored_metadata = json.loads(result["config_data"])
        assert actual_checksum == stored_metadata["sha256_hash"]

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
                WHERE config_type = 'backup_metadata'
            """
            )
            result = cursor.fetchone()
            assert result["count"] == 2

    def test_list_workflows_filtering_integration(self, manager_with_real_workflows: WorkflowApi) -> None:
        """Test workflow listing with filtering in real integration scenario"""
        manager = manager_with_real_workflows
        workflows = manager.list_workflows()
        test_workflow = workflows[0]
        workflow_file = manager.config.workflows_path / test_workflow["file"]
        workflow_file.unlink()
        all_workflows = manager.list_workflows(only_backupable=False)
        assert len(all_workflows) == 2
        backupable_workflows = manager.list_workflows(only_backupable=True)
        assert len(backupable_workflows) == 1
        remaining_workflow = backupable_workflows[0]
        remaining_file = manager.config.workflows_path / remaining_workflow["file"]
        assert remaining_file.exists()


@pytest.mark.integration
# === Workflow Manager Integration Tests ===
class TestWorkflowManagerIntegration:
    """Test overall workflow manager integration scenarios"""

    @pytest.fixture
    def integrated_manager(self, test_config: AppConfig) -> WorkflowApi:
        """Create a fully integrated workflow manager"""
        manager = WorkflowApi(config=test_config)
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
        workflow = Workflow(
            id="api_integration_workflow",
            name="API Integration Workflow",
        )

        manager.db.create_workflow(workflow)
        # Create the file in test_workflows subdirectory
        test_workflows_dir = manager.config.workflows_path / "test_workflows"
        test_workflows_dir.mkdir(parents=True, exist_ok=True)
        # Use a fixed filename for this test
        filename = "api_integration.json"
        file_path = test_workflows_dir / filename

        with open(file_path, "w") as f:
            json.dump({"id": workflow.id, "name": workflow.name}, f)

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
        assert manager.config.backups_path.parent == test_config.base_folder
        assert manager.config.workflows_path == test_config.workflows_path

    def test_error_recovery_integration(self, integrated_manager: WorkflowApi) -> None:
        """Test error recovery in integrated scenarios"""
        manager = integrated_manager
        workflow = Workflow(
            id="error_recovery_test",
            name="Error Recovery Test",
        )

        manager.db.create_workflow(workflow)
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
