#!/usr/bin/env python3
"""
Integration tests for workflow backup functionality with real files and database
"""

import pytest
import json
import tarfile
import hashlib
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, Mock

from api.manager import WorkflowManager
from api.models import Workflow, WorkflowType, WorkflowStatus

# Set testing environment variable to skip default workflows
os.environ["N8N_DEPLOY_TESTING"] = "1"


@pytest.mark.integration
class TestWorkflowBackupIntegration:
    """Test integration between database, filesystem, and backup operations"""

    @pytest.fixture
    def manager_with_real_workflows(self, test_config):
        """Create manager with real workflow files and database entries"""
        manager = WorkflowManager(config=test_config)

        # Clear existing data
        with manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.commit()

        # Create real workflow files with valid JSON content
        workflows_data = [
            {
                "id": "integration_main_workflow",
                "name": "Main Integration Workflow",
                "type": WorkflowType.MAIN,
                "status": WorkflowStatus.ACTIVE,
                "file_path": "workflows/main_integration.json",
                "node_count": 3,
            },
            {
                "id": "integration_subflow",
                "name": "Integration Subflow",
                "type": WorkflowType.SUBFLOW,
                "status": WorkflowStatus.ACTIVE,
                "file_path": "workflows/subflows/integration_subflow.json",
                "node_count": 2,
            },
        ]

        # Create workflow files and database entries
        for wf_data in workflows_data:
            # Create realistic workflow JSON file
            file_path = manager.base_path / wf_data["file_path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)

            workflow_json = {
                "id": wf_data["id"],
                "name": wf_data["name"],
                "active": wf_data["status"] == WorkflowStatus.ACTIVE,
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
                            "functionCode": "return items.map(item => ({...item, processed: true}));"
                        },
                        "id": "function_node",
                        "name": "Process",
                        "type": "n8n-nodes-base.function",
                        "typeVersion": 1,
                        "position": [460, 300],
                    },
                ][: wf_data["node_count"]],
                "connections": (
                    {
                        "Start": {
                            "main": [[{"node": "Process", "type": "main", "index": 0}]]
                        }
                    }
                    if wf_data["node_count"] > 1
                    else {}
                ),
                "staticData": {},
                "settings": {"executionOrder": "v1"},
                "createdAt": datetime.now(timezone.utc).isoformat() + "Z",
                "updatedAt": datetime.now(timezone.utc).isoformat() + "Z",
            }

            with open(file_path, "w") as f:
                json.dump(workflow_json, f, indent=2)

            # Add to database
            workflow = Workflow(**wf_data)
            workflow_id = manager.db.create_workflow(workflow)

            # Verify workflow was created successfully
            assert (
                workflow_id == wf_data["id"]
            ), f"Failed to create workflow {wf_data['id']}"

        # Verify both workflows were created
        created_workflows = manager.list_workflows()
        assert (
            len(created_workflows) == 2
        ), f"Expected 2 workflows, created {len(created_workflows)}"

        return manager

    def test_backup_with_real_files_and_database(self, manager_with_real_workflows):
        """Test backup creation with real workflow files and database integration"""
        manager = manager_with_real_workflows

        # Verify initial state - workflows exist in database and filesystem
        workflows = manager.list_workflows()

        # Debug: Print workflow details if assertion fails
        if len(workflows) != 2:
            print(f"Expected 2 workflows, found {len(workflows)}")
            for wf in workflows:
                print(f"Workflow: {wf}")

            # Check database directly
            with manager.db.get_connection() as conn:
                cursor = conn.execute("SELECT id, name FROM workflows")
                db_workflows = cursor.fetchall()
                print(f"Database workflows: {[dict(row) for row in db_workflows]}")

        assert (
            len(workflows) >= 1
        ), f"Expected at least 1 workflow, found {len(workflows)}"

        for wf in workflows:
            assert wf["file_exists"] is True
            assert wf["backupable"] is True

        # Test backing up each workflow individually
        backup_results = []
        for wf in workflows:
            backup_result = manager.create_workflow_backup(wf["id"])
            backup_results.append(backup_result)

            # Verify backup was created
            assert backup_result is not None
            assert "backup_id" in backup_result
            assert "filename" in backup_result
            assert backup_result["workflow_id"] == wf["id"]

            # Verify backup file exists
            backup_path = manager.config.backups_path / backup_result["filename"]
            assert backup_path.exists()

            # Verify backup contains the workflow file and metadata
            with tarfile.open(backup_path, "r:gz") as tar:
                members = tar.getnames()
                workflow_files = [
                    m
                    for m in members
                    if m.endswith(".json") and not m.endswith("metadata.json")
                ]
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

    def test_backup_all_workflows_integration(self, manager_with_real_workflows):
        """Test backup_all_workflows convenience method with real integration"""
        manager = manager_with_real_workflows

        # Use the convenience method to backup all workflows
        result = manager.backup_all_workflows()

        # Verify all workflows were backed up
        assert result["total_workflows"] == 2
        assert len(result["successful_backups"]) == 2
        assert len(result["failed_backups"]) == 0

        # Verify each backup file exists and contains correct workflow
        for backup_info in result["successful_backups"]:
            backup_path = manager.config.backups_path / backup_info["filename"]
            assert backup_path.exists()

            with tarfile.open(backup_path, "r:gz") as tar:
                workflow_files = [
                    m
                    for m in tar.getnames()
                    if m.endswith(".json") and not m.endswith("metadata.json")
                ]
                metadata_files = [
                    m for m in tar.getnames() if m.endswith("metadata.json")
                ]
                assert len(workflow_files) == 1  # Should have one workflow file
                assert len(metadata_files) == 1  # Should have one metadata file

    def test_backup_with_missing_file_integration(self, manager_with_real_workflows):
        """Test backup behavior when workflow exists in database but file is missing"""
        manager = manager_with_real_workflows

        # Get a workflow and delete its file
        workflows = manager.list_workflows()
        test_workflow = workflows[0]
        workflow_file = manager.base_path / test_workflow["file"]
        workflow_file.unlink()  # Delete the file

        # Verify workflow shows as not backupable
        updated_workflows = manager.list_workflows()
        missing_file_workflow = next(
            wf for wf in updated_workflows if wf["id"] == test_workflow["id"]
        )
        assert missing_file_workflow["file_exists"] is False
        assert missing_file_workflow["backupable"] is False

        # Attempt to backup should fail
        with pytest.raises(FileNotFoundError, match="Workflow file not found"):
            manager.create_workflow_backup(test_workflow["id"])

        # backup_all_workflows should skip the missing file
        result = manager.backup_all_workflows()
        assert result["total_workflows"] == 1  # Only backupable workflows are counted
        assert len(result["successful_backups"]) == 1  # Only one workflow has a file
        assert (
            len(result["failed_backups"]) == 0
        )  # Non-backupable workflows are filtered out

    def test_backup_integrity_with_real_data(self, manager_with_real_workflows):
        """Test backup integrity verification with real workflow data"""
        manager = manager_with_real_workflows

        workflows = manager.list_workflows()
        test_workflow = workflows[0]

        # Create backup
        backup_result = manager.create_workflow_backup(test_workflow["id"])
        backup_path = manager.config.backups_path / backup_result["filename"]

        # Calculate actual file checksum
        with open(backup_path, "rb") as f:
            actual_checksum = hashlib.sha256(f.read()).hexdigest()

        # Get stored checksum from database
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

    def test_database_and_filesystem_consistency(self, manager_with_real_workflows):
        """Test consistency between database records and filesystem state"""
        manager = manager_with_real_workflows

        # Get workflows and verify consistency
        workflows = manager.list_workflows()

        for wf in workflows:
            # Database record should exist
            db_workflow = manager.db.get_workflow(wf["id"])
            assert db_workflow is not None
            assert db_workflow.id == wf["id"]

            # File should exist at expected location
            expected_file_path = manager.base_path / wf["file"]
            assert expected_file_path.exists()

            # File content should be valid JSON
            with open(expected_file_path, "r") as f:
                workflow_json = json.load(f)
                assert workflow_json["id"] == wf["id"]
                assert workflow_json["name"] == wf["name"]

    def test_concurrent_backup_operations(self, manager_with_real_workflows):
        """Test that multiple backup operations don't interfere with each other"""
        manager = manager_with_real_workflows

        workflows = manager.list_workflows()

        # Create backups of both workflows simultaneously (simulated)
        backup_results = []
        for wf in workflows:
            backup_result = manager.create_workflow_backup(wf["id"])
            backup_results.append(backup_result)

        # Verify both backups were created with unique filenames
        filenames = [result["filename"] for result in backup_results]
        assert len(set(filenames)) == len(filenames)  # All unique

        # Verify both backup files exist
        for result in backup_results:
            backup_path = manager.config.backups_path / result["filename"]
            assert backup_path.exists()

        # Verify database has metadata for both backups
        with manager.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM configurations
                WHERE config_type = 'backup_metadata'
            """
            )
            result = cursor.fetchone()
            assert result["count"] == 2

    def test_list_workflows_filtering_integration(self, manager_with_real_workflows):
        """Test workflow listing with filtering in real integration scenario"""
        manager = manager_with_real_workflows

        # Delete one workflow file to create mixed state
        workflows = manager.list_workflows()
        test_workflow = workflows[0]
        workflow_file = manager.base_path / test_workflow["file"]
        workflow_file.unlink()

        # Test listing all workflows
        all_workflows = manager.list_workflows(only_backupable=False)
        assert len(all_workflows) == 2

        # Test listing only backupable workflows
        backupable_workflows = manager.list_workflows(only_backupable=True)
        assert len(backupable_workflows) == 1

        # Verify the remaining workflow is the one with existing file
        remaining_workflow = backupable_workflows[0]
        remaining_file = manager.base_path / remaining_workflow["file"]
        assert remaining_file.exists()


@pytest.mark.integration
class TestWorkflowManagerIntegration:
    """Test overall workflow manager integration scenarios"""

    @pytest.fixture
    def integrated_manager(self, test_config):
        """Create a fully integrated workflow manager"""
        manager = WorkflowManager(config=test_config)

        # Clear any existing data
        with manager.db.get_connection() as conn:
            conn.execute("DELETE FROM workflows")
            conn.execute("DELETE FROM api_keys")
            conn.execute("DELETE FROM configurations")
            conn.commit()

        return manager

    def test_complete_workflow_management_cycle(self, integrated_manager):
        """Test complete workflow management from creation to deletion"""
        manager = integrated_manager

        # Step 1: Create workflow in database
        workflow = Workflow(
            id="integration_cycle_test",
            name="Integration Cycle Test Workflow",
            type=WorkflowType.MAIN,
            file_path="workflows/cycle_test.json",
            status=WorkflowStatus.ACTIVE,
            node_count=2,
        )

        workflow_id = manager.db.create_workflow(workflow)
        assert workflow_id == workflow.id

        # Step 2: Create corresponding workflow file
        file_path = manager.base_path / workflow.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        workflow_json = {
            "id": workflow.id,
            "name": workflow.name,
            "active": True,
            "nodes": [
                {"id": "node1", "name": "Start", "type": "n8n-nodes-base.start"},
                {"id": "node2", "name": "End", "type": "n8n-nodes-base.noOp"},
            ],
            "connections": {},
        }

        with open(file_path, "w") as f:
            json.dump(workflow_json, f, indent=2)

        # Step 3: Verify workflow appears in listings
        workflows = manager.list_workflows()
        assert len(workflows) == 1
        assert workflows[0]["id"] == workflow.id
        assert workflows[0]["file_exists"] is True

        # Step 4: Create backup
        backup_result = manager.create_workflow_backup(workflow.id)
        assert backup_result is not None

        # Step 5: Verify backup metadata in database
        with manager.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM configurations
                WHERE config_type = 'backup_metadata'
            """
            )
            result = cursor.fetchone()
            assert result["count"] > 0

        # Step 6: Delete workflow (soft delete - archives it)
        success = manager.db.delete_workflow(workflow.id)
        assert success is True

        # Step 7: Verify workflow is archived, not completely gone
        archived_workflow = manager.db.get_workflow(workflow.id)
        assert archived_workflow is not None
        assert archived_workflow.status == WorkflowStatus.ARCHIVED

    def test_api_key_and_workflow_integration(self, integrated_manager):
        """Test integration between API key management and workflow operations"""
        manager = integrated_manager

        # Add API key
        api_key_id = manager.api_manager.add_api_key(
            name="integration_test_key",
            api_key="integration_test_api_key_12345",
            description="API key for integration testing",
        )

        assert api_key_id is not None

        # Verify API key was stored
        api_keys = manager.api_manager.list_api_keys()
        assert len(api_keys) == 1
        assert api_keys[0]["name"] == "integration_test_key"

        # Create workflow
        workflow = Workflow(
            id="api_integration_workflow",
            name="API Integration Workflow",
            type=WorkflowType.MAIN,
            file_path="workflows/api_integration.json",
            status=WorkflowStatus.ACTIVE,
        )

        manager.db.create_workflow(workflow)

        # Create workflow file
        file_path = manager.base_path / workflow.file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump({"id": workflow.id, "name": workflow.name}, f)

        # Both workflow and API key should be manageable
        workflows = manager.list_workflows()
        api_keys = manager.api_manager.list_api_keys()

        assert len(workflows) == 1
        assert len(api_keys) == 1

        # Backup should work with both data types present
        backup_result = manager.create_workflow_backup(workflow.id)
        assert backup_result is not None

        # Clean up API key
        success = manager.api_manager.delete_api_key(api_key_id, confirm=True)
        assert success is True

    def test_configuration_integration(self, test_config):
        """Test configuration integration across different components"""
        # Test manager initialization with custom config
        manager = WorkflowManager(config=test_config)

        # Verify all components use the same configuration
        assert manager.config == test_config
        assert (
            manager.base_path == test_config.workflows_path
        )  # base_path is the workflows directory
        assert manager.db.db_path == test_config.database_path

        # API manager should also use the same config
        assert manager.api_manager.config == test_config

        # Paths should be consistent across components
        assert manager.config.backups_path.parent == test_config.base_folder
        assert manager.config.workflows_path == test_config.workflows_path

    def test_error_recovery_integration(self, integrated_manager):
        """Test error recovery in integrated scenarios"""
        manager = integrated_manager

        # Create workflow
        workflow = Workflow(
            id="error_recovery_test",
            name="Error Recovery Test",
            type=WorkflowType.MAIN,
            file_path="workflows/error_recovery.json",
            status=WorkflowStatus.ACTIVE,
        )

        manager.db.create_workflow(workflow)

        # Test graceful handling when file operations fail
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Manager should handle file operation errors gracefully
            workflows = manager.list_workflows()
            assert len(workflows) == 1
            assert workflows[0]["file_exists"] is False  # Should detect file issue

            # Backup should fail gracefully
            with pytest.raises(FileNotFoundError):
                manager.create_workflow_backup(workflow.id)

        # Manager should recover after error
        workflows = manager.list_workflows()
        assert len(workflows) == 1
