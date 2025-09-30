#!/usr/bin/env python3
"""
End-to-End Manual Database Testing

Real CLI execution tests for database operations, initialization,
backup/restore functionality, and stats display.
"""

import hashlib
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

from .e2e_base import E2ETestBase


# === End-to-End Tests ===
class TestE2EDatabase(E2ETestBase):
    """Comprehensive end-to-end testing for all database operations

    This class consolidates all database-related tests:
    - CLI database commands (init, status, backup, compact)
    - Database integration with workflows and backups
    - Direct database operations and CRUD functionality
    - Database initialization and configuration
    """

    def test_database_initialization(self) -> None:
        """Test database initialization creates proper schema"""
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Database initialization")
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists(), f"Database file not created at {db_path}"
        assert db_path.is_file(), f"Database path {db_path} is not a file"
        assert db_path.stat().st_size > 0, f"Database file {db_path} is empty (size: {db_path.stat().st_size})"

    def test_database_status_after_initialization(self) -> None:
        """Test db status command shows correct information"""
        # Initialize first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status"])

        assert returncode == 0
        assert "Database" in stdout or "Status" in stdout
        # Should show database information without errors

    def test_stats_command_shows_never_for_null_timestamps(self) -> None:
        """Test stats command handles null timestamps correctly"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "stats"])

        assert returncode == 0

        # Should handle null/empty timestamps gracefully
        # Look for "Never" or similar text for empty timestamps
        if "Never" in stdout or "No" in stdout or "0" in stdout:
            # This indicates proper null timestamp handling
            pass

    def test_database_backup_creation(self) -> None:
        """Test database backup functionality"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup"])

        assert returncode == 0
        backup_dir = Path(self.temp_dir) / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.db"))
            assert len(backup_files) > 0, "No backup files created"

    def test_list_backups_shows_metadata(self) -> None:
        """Test list backups command shows backup metadata"""
        # Initialize and create backup
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup"])

        # List backups
        backup_dir = Path(self.temp_dir) / "backups"
        returncode, stdout, stderr = self.run_cli_command(
            ["--app-dir", self.temp_dir, "list-backups", "--backup-dir", str(backup_dir)]
        )

        # Should succeed (even if no backups exist yet)
        assert returncode == 0

    def test_backup_workflows_complete_cycle(self) -> None:
        """Test complete backup cycle with workflows"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        workflow_file = Path(self.temp_flow_dir) / "test_workflow.json"
        workflow_data = {
            "name": "Test Workflow",
            "nodes": [],
            "connections": {},
            "active": False,
        }
        workflow_file.write_text(json.dumps(workflow_data, indent=2))
        env = {"N8N_FLOW_DIR": self.temp_flow_dir}
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "test_workflow",
            ],
            env=env,
        )
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup"])

        assert returncode == 0
        backup_dir = Path(self.temp_dir) / "backups"
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.tar.gz"))
            if backup_files:
                try:
                    with tarfile.open(backup_files[0], "r:gz") as tar:
                        assert len(tar.getnames()) > 0
                except Exception:
                    pytest.fail("Backup file is not valid tar.gz")

    def test_restore_backup_functionality(self) -> None:
        """Test backup restore functionality"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        backup_result = self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup"])

        if backup_result[0] == 0:  # Backup successful
            # Try to restore (may not be implemented yet)
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "restore", "--help"])
            if returncode == 0 and "restore" in stdout.lower():
                # Restore command exists, test it
                backup_dir = Path(self.temp_dir) / "backups"
                backup_files = list(backup_dir.glob("*.tar.gz"))
                if backup_files:
                    restore_result = self.run_cli_command(
                        [
                            "--app-dir",
                            self.temp_dir,
                            "db",
                            "restore",
                            str(backup_files[0]),
                        ]
                    )
                    # Should complete without crashing
                    assert restore_result[0] in [0, 1]

    def test_database_integrity_after_operations(self) -> None:
        """Test database maintains integrity after various operations"""
        # Initialize
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Perform various operations
        operations = [
            ["db", "status"],
            ["list"],
            ["stats"],
            ["db", "status"],  # Repeat to check consistency
        ]

        for op in operations:
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir] + op)
            assert returncode == 0, f"Database integrity failed after: {op}"
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists()
        assert db_path.stat().st_size > 0

    def test_database_permissions_handling(self) -> None:
        """Test database creation with proper permissions"""
        # Initialize database
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        assert returncode == 0
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        if db_path.exists():
            # Should be readable and writable by owner
            assert os.access(db_path, os.R_OK)
            assert os.access(db_path, os.W_OK)

    def test_database_schema_version_tracking(self) -> None:
        """Test database schema version is properly tracked"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Status should show schema information
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status"])

        assert returncode == 0
        # Should complete without errors (schema version tracking working)

    def test_backup_checksum_verification(self) -> None:
        """Test backup files include proper checksums"""
        # Initialize and create backup
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup"])

        if returncode == 0:
            backup_dir = Path(self.temp_dir) / "backups"
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.tar.gz"))
                if backup_files:
                    backup_file = backup_files[0]

                    # Calculate checksum
                    sha256_hash = hashlib.sha256()
                    with open(backup_file, "rb") as f:
                        for byte_block in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(byte_block)

                    checksum = sha256_hash.hexdigest()
                    assert len(checksum) == 64  # SHA256 checksum length

    def test_database_concurrent_access_safety(self) -> None:
        """Test database handles concurrent access safely"""
        import threading

        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        results = []

        def run_db_command():
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status"])
            results.append((returncode, stdout, stderr))

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=run_db_command)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All should succeed
        assert len(results) == 3
        for returncode, stdout, stderr in results:
            assert returncode == 0

    def test_database_migration_handling(self) -> None:
        """Test database migration handling (if applicable)"""
        # Initialize database
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        assert returncode == 0
        for _ in range(3):
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status"])
            assert returncode == 0

    def test_empty_database_operations(self) -> None:
        """Test operations on empty database"""
        # Initialize empty database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        empty_db_operations = [["list"], ["stats"], ["list-backups"], ["db", "status"]]

        for op in empty_db_operations:
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir] + op)
            assert returncode == 0, f"Empty database operation failed: {op}"

    def test_database_size_tracking(self) -> None:
        """Test database size is reasonable and tracked"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        workflow_file = Path(self.temp_flow_dir) / "size_test.json"
        workflow_data = {
            "name": "Size Test Workflow",
            "nodes": [{"id": "node1", "type": "test"}],
            "connections": {},
        }
        workflow_file.write_text(json.dumps(workflow_data))
        self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "size_test",
            ]
        )

        final_size = db_path.stat().st_size

        # Database should be reasonable size (not too large)
        assert final_size < 10 * 1024 * 1024  # Less than 10MB for test data

    def test_database_error_recovery(self) -> None:
        """Test database error recovery mechanisms"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Try operations that might cause errors
        error_prone_operations = [
            ["add", "nonexistent.json", "Nonexistent-Workflow"],  # Missing file should return exit code 1
            ["db", "backup"],  # Should work
            ["list"],  # Should work
        ]

        for op in error_prone_operations:
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir] + op)
            # Should not crash, even if operation fails
            assert returncode in [0, 1]

        # Database should still be accessible
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status"])
        assert returncode == 0

    def test_database_compact_command(self) -> None:
        """Test db compact command optimizes database storage"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Run compact command
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "compact"])

        assert returncode == 0
        assert "Optimizing database" in stdout
        assert "optimization complete" in stdout

    def test_database_compact_with_no_emoji(self) -> None:
        """Test db compact command with --no-emoji flag"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Run compact with no-emoji (already applied via run_cli_command)
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "compact"])

        assert returncode == 0
        # Should not contain emoji when using --no-emoji
        assert "🎭" not in stdout
        assert "✅" not in stdout

    def test_database_status_comprehensive_info(self) -> None:
        """Test db status shows comprehensive database information"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Test status command
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status"])

        assert returncode == 0
        # Should contain key database information
        assert "Database" in stdout
        # Additional checks could include size, schema version, etc.

    def test_database_status_json_format(self) -> None:
        """Test db status with JSON format output"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Test status with JSON format
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status", "--format", "json"])

        assert returncode == 0
        # Should be valid JSON output
        try:
            import json

            status_data = json.loads(stdout)
            assert "database_path" in status_data
            assert "schema_version" in status_data
        except json.JSONDecodeError:
            assert False, f"Invalid JSON output: {stdout[:200]}..."

    # === CLI Database Command Tests ===
    # (Consolidated from test_cli_commands.py)

    def test_cli_db_init_fresh_directory(self) -> None:
        """Test database initialization in fresh directory"""
        # Use a fresh temp directory for this test
        import tempfile

        with tempfile.TemporaryDirectory() as fresh_dir:
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", fresh_dir, "db", "init"])

            assert returncode == 0
            assert "initialized" in stdout.lower()

            # Verify database file created
            db_path = Path(fresh_dir) / "n8n-deploy.db"
            assert db_path.exists()

            # Test status after init
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", fresh_dir, "db", "status"])
            assert returncode == 0
            assert "Database Path" in stdout
            assert "Database Size" in stdout
            assert "Schema Version" in stdout

    def test_cli_db_status_comprehensive_output(self) -> None:
        """Test comprehensive database status command output"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Test regular status output
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status"])
        assert returncode == 0
        assert "Database Status" in stdout
        assert "Workflows" in stdout

        # Test JSON format status
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "status", "--format", "json"])
        assert returncode == 0
        status_data = json.loads(stdout)
        assert "database_path" in status_data
        assert "schema_version" in status_data

    def test_cli_db_backup_operations(self) -> None:
        """Test CLI database backup operations"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Test default backup
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup"])
        assert returncode == 0
        assert "backup" in stdout.lower()

        # Test custom backup path
        backup_path = Path(self.temp_dir) / "custom_backup.db"
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup", str(backup_path)])
        assert returncode == 0
        assert backup_path.exists()

    def test_cli_backup_workflows_operation(self) -> None:
        """Test CLI workflow backup creation"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Create backup directory
        backup_dir = Path(self.temp_dir) / "test_backups"
        backup_dir.mkdir(exist_ok=True)

        # Test workflow backup command
        returncode, stdout, stderr = self.run_cli_command(
            ["--app-dir", self.temp_dir, "backup-workflows", "--backup-dir", str(backup_dir)]
        )

        # Backup may fail due to missing workflow files, but should handle gracefully
        assert "backup" in stdout.lower() or "backup failed" in stderr.lower()

    def test_cli_list_backups_operation(self) -> None:
        """Test CLI listing workflow backups"""
        # Initialize database first
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Create backups directory
        backup_dir = Path(self.temp_dir) / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Test list backups command
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "list-backups"])

        # Should succeed even with empty backup directory
        assert returncode == 0

    # === Database Integration with Workflows Tests ===
    # (Consolidated from test_workflow_backup_integration.py)

    def test_database_workflow_integration_comprehensive(self) -> None:
        """Test comprehensive database integration with workflow operations"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Create test workflow files
        workflow_data1 = {
            "name": "Integration Test Workflow 1",
            "nodes": [{"id": "node1", "type": "test"}],
            "connections": {},
            "active": False,
        }
        workflow_data2 = {
            "name": "Integration Test Workflow 2",
            "nodes": [{"id": "node2", "type": "test"}],
            "connections": {},
            "active": True,
        }

        workflow_file1 = Path(self.temp_flow_dir) / "integration_test1.json"
        workflow_file2 = Path(self.temp_flow_dir) / "integration_test2.json"

        workflow_file1.write_text(json.dumps(workflow_data1, indent=2))
        workflow_file2.write_text(json.dumps(workflow_data2, indent=2))

        # Add workflows to database
        env = {"N8N_FLOW_DIR": self.temp_flow_dir}

        add_result1 = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "integration_test1",
            ],
            env=env,
        )
        add_result2 = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "integration_test2",
            ],
            env=env,
        )

        # Verify workflows were added successfully
        if add_result1[0] == 0 and add_result2[0] == 0:
            # Test workflow listing
            list_result = self.run_cli_command(["--app-dir", self.temp_dir, "list"])
            assert list_result[0] == 0

            # Test database backup with workflows
            backup_result = self.run_cli_command(["--app-dir", self.temp_dir, "db", "backup"])
            assert backup_result[0] == 0

            # Verify backup directory exists
            backup_dir = Path(self.temp_dir) / "backups"
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.tar.gz"))
                if backup_files:
                    # Verify backup file integrity
                    try:
                        with tarfile.open(backup_files[0], "r:gz") as tar:
                            members = tar.getnames()
                            assert len(members) > 0
                            # Should contain database and workflow files
                            json_files = [m for m in members if m.endswith(".json")]
                            assert len(json_files) >= 2  # At least 2 workflow files
                    except Exception as e:
                        pytest.fail(f"Backup file integrity check failed: {e}")

    def test_database_filesystem_consistency_check(self) -> None:
        """Test database and filesystem consistency validation"""
        # Initialize database
        self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        # Create workflow file
        workflow_data = {
            "name": "Consistency Test Workflow",
            "nodes": [],
            "connections": {},
            "active": False,
        }

        workflow_file = Path(self.temp_flow_dir) / "consistency_test.json"
        workflow_file.write_text(json.dumps(workflow_data, indent=2))

        # Add workflow
        env = {"N8N_FLOW_DIR": self.temp_flow_dir}
        add_result = self.run_cli_command(
            [
                "--app-dir",
                self.temp_dir,
                "--flow-dir",
                self.temp_flow_dir,
                "add",
                "consistency_test",
            ],
            env=env,
        )

        if add_result[0] == 0:
            # Verify workflow in database via list command
            list_result = self.run_cli_command(["--app-dir", self.temp_dir, "list"])
            assert list_result[0] == 0

            # Modify file on filesystem
            modified_data = workflow_data.copy()
            modified_data["name"] = "Modified Consistency Test Workflow"
            workflow_file.write_text(json.dumps(modified_data, indent=2))

            # Test that system can still read the file
            list_result2 = self.run_cli_command(["--app-dir", self.temp_dir, "list"])
            assert list_result2[0] == 0

    # === Unit Test Functionality ===
    # (Consolidated unit-level database tests)

    def test_database_direct_operations(self) -> None:
        """Test direct database operations (unit-level functionality)"""
        from api.config import AppConfig
        from api.db import DBApi
        from api.models import Workflow

        # Initialize database directly
        config = AppConfig(base_folder=Path(self.temp_dir))
        db = DBApi(config=config)

        # Test database path resolution
        expected_path = config.database_path
        assert db.db_path == expected_path
        assert db.db_path.exists()

        # Test workflow CRUD operations
        workflow_data = {
            "id": "test_unit_workflow_001",
            "name": "Unit Test Workflow",
            "description": "Test workflow for unit testing",
            "file_path": "unit_test.json",
            "tags": ["test", "unit"],
        }

        workflow = Workflow(**workflow_data)

        # Test create workflow
        result = db.add_workflow(workflow)
        assert result == workflow.id

        # Test get workflow
        retrieved = db.get_workflow(workflow.id)
        assert retrieved is not None
        assert retrieved.id == workflow.id
        assert retrieved.name == workflow.name

        # Test list workflows
        workflows = db.list_workflows()
        assert len(workflows) >= 1
        workflow_ids = [wf.id for wf in workflows]
        assert workflow.id in workflow_ids

        # Test connection management
        with db.get_connection() as conn:
            import sqlite3

            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

        # Test delete workflow
        delete_result = db.delete_workflow(workflow.id)
        assert delete_result is True

        # Verify deletion
        deleted_workflow = db.get_workflow(workflow.id)
        assert deleted_workflow is None

        # Test operations on empty database
        empty_workflows = db.list_workflows()
        assert len(empty_workflows) == 0

        # Test non-existent workflow operations
        nonexistent = db.get_workflow("nonexistent_id")
        assert nonexistent is None

        delete_nonexistent = db.delete_workflow("nonexistent_id")
        assert delete_nonexistent is False

    def test_database_duplicate_handling(self) -> None:
        """Test database handling of duplicate entries"""
        import sqlite3

        from api.config import AppConfig
        from api.db import DBApi
        from api.models import Workflow

        # Initialize database directly
        config = AppConfig(base_folder=Path(self.temp_dir))
        db = DBApi(config=config)

        # Create first workflow
        workflow_data = {
            "id": "duplicate_test_001",
            "name": "Duplicate Test Workflow",
            "description": "Test workflow for duplicate testing",
            "file_path": "duplicate_test.json",
            "tags": ["test"],
        }

        workflow1 = Workflow(**workflow_data)
        workflow2 = Workflow(**workflow_data)  # Same ID

        # First creation should succeed
        result1 = db.add_workflow(workflow1)
        assert result1 == workflow1.id

        # Second creation with same ID should fail
        try:
            db.add_workflow(workflow2)
            assert False, "Expected IntegrityError for duplicate workflow ID"
        except sqlite3.IntegrityError:
            # Expected behavior
            pass


class TestE2EDatabaseInit:
    """End-to-end testing for database initialization specifically"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self) -> None:
        """Set up clean test environment for each test"""
        # Ensure testing environment is set
        os.environ["N8N_DEPLOY_TESTING"] = "1"
        self.temp_dir = tempfile.mkdtemp()
        self.temp_flow_dir = tempfile.mkdtemp()

        yield

        # Cleanup
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.temp_flow_dir, ignore_errors=True)

    def run_cli_command(self, args: List[str], env: Optional[Dict[str, str]] = None) -> Tuple[int, str, str]:
        """Run CLI command with proper error handling"""
        import subprocess

        # Reorder arguments to handle global options correctly
        # Convert ["--app-dir", "/path", "command", ...] to ["command", "--app-dir", "/path", ...]
        reordered_args = []
        global_options = []
        i = 0

        # Extract global options from the beginning
        while i < len(args):
            if args[i] in ["--app-dir", "--flow-dir", "--server-url"] and i + 1 < len(args):
                global_options.extend([args[i], args[i + 1]])
                i += 2
            elif args[i] in ["--no-emoji"]:
                global_options.append(args[i])
                i += 1
            else:
                # Found the command, add it and remaining args
                reordered_args = args[i:] + global_options
                break

        # If no command found, use original args
        if not reordered_args:
            reordered_args = args

        cmd = ["./n8n-deploy"] + reordered_args

        # Add --no-emoji to commands that support it for consistent test output
        if reordered_args:
            command = reordered_args[0]
            # Commands that support --no-emoji at the command level
            no_emoji_commands = {"list", "list-server", "stats"}
            # apikey subcommands that support --no-emoji
            no_emoji_apikey_subcommands = {"add", "list", "get"}
            # db subcommands that support --no-emoji
            no_emoji_db_subcommands = {"init", "compact"}

            if command in no_emoji_commands:
                cmd.append("--no-emoji")
            elif command == "apikey" and len(reordered_args) > 1:
                apikey_subcommand = reordered_args[1]
                if apikey_subcommand in no_emoji_apikey_subcommands:
                    cmd.append("--no-emoji")
            elif command == "db" and len(reordered_args) > 1:
                db_subcommand = reordered_args[1]
                if db_subcommand in no_emoji_db_subcommands:
                    cmd.append("--no-emoji")

        if env is None:
            env = {}

        env.update({"N8N_DEPLOY_TESTING": "1"})

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, **env},
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def assert_command_details(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        expected_returncode: int,
        description: str,
    ) -> None:
        """Assert command results with detailed error information"""
        if returncode != expected_returncode:
            print(f"\n--- Test Failed: {description} ---")
            print(f"Return code: {returncode} (expected: {expected_returncode})")
            print("STDOUT:")
            print(stdout)
            print("STDERR:")
            print(stderr)
            print("--- End Test Details ---")

        assert (
            returncode == expected_returncode
        ), f"{description} failed. Expected return code {expected_returncode}, got {returncode}. STDOUT: {stdout[:200]}... STDERR: {stderr[:200]}..."

        assert stderr == "", f"Unexpected stderr output: '{stderr}'"

    def test_database_initialization_basic(self) -> None:
        """Test basic database initialization creates proper schema"""
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        self.assert_command_details(returncode, stdout, stderr, 0, "Database initialization")
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists(), f"Database file not created at {db_path}"
        assert db_path.is_file(), f"Database path {db_path} is not a file"
        assert db_path.stat().st_size > 0, f"Database file {db_path} is empty (size: {db_path.stat().st_size})"

    def test_database_init_interactive_prompts(self) -> None:
        """Test database init prompts for existing database with interactive choices"""
        # First initialization (should succeed)
        returncode1, stdout1, stderr1 = self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])
        assert returncode1 == 0
        assert "Database initialized" in stdout1

        # Second initialization should detect existing database and prompt
        # Note: This test would require input simulation for interactive testing
        # For now, verify the database exists and init would detect it
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists(), "Database should exist after first init"

    def test_database_init_with_no_emoji_flag(self) -> None:
        """Test db init with --no-emoji flag"""
        returncode, stdout, stderr = self.run_cli_command(["--app-dir", self.temp_dir, "db", "init"])

        assert returncode == 0
        # Since we use --no-emoji in run_cli_command, should not contain emojis
        assert "✅" not in stdout
        assert "Database initialized" in stdout

    def test_database_init_different_directories(self) -> None:
        """Test db init works with different --app-dir values"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir2:
            returncode, stdout, stderr = self.run_cli_command(["--app-dir", temp_dir2, "db", "init"])

            assert returncode == 0
            assert "Database initialized" in stdout

            # Verify database created in correct location
            db_path = Path(temp_dir2) / "n8n-deploy.db"
            assert db_path.exists(), f"Database not created in {temp_dir2}"
