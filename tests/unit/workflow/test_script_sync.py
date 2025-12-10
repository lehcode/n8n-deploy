"""Unit tests for api/workflow/script_sync.py module

Tests for ScriptSyncManager class methods.
"""

from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest
from assertpy import assert_that

from api.workflow.script_sync import ScriptSyncConfig, ScriptSyncManager, ScriptSyncResult


@pytest.fixture
def mock_key_file(temp_dir: Path) -> Path:
    """Create a mock SSH key file for tests."""
    key_file = temp_dir / "test_key"
    key_file.write_text("mock key content")
    return key_file


class TestScriptSyncConfig:
    """Tests for ScriptSyncConfig dataclass"""

    def test_config_creation_minimal(self, temp_dir: Path) -> None:
        """Test ScriptSyncConfig creation with minimal parameters"""
        config = ScriptSyncConfig(
            scripts_dir=temp_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test Workflow",
        )
        assert_that(config.scripts_dir).is_equal_to(temp_dir)
        assert_that(config.host).is_equal_to("remote.example.com")
        assert_that(config.username).is_equal_to("testuser")
        assert_that(config.port).is_equal_to(22)  # default
        assert_that(config.changed_only).is_true()  # default
        assert_that(config.dry_run).is_false()  # default

    def test_config_creation_full(self, temp_dir: Path) -> None:
        """Test ScriptSyncConfig creation with all parameters"""
        config = ScriptSyncConfig(
            scripts_dir=temp_dir,
            host="remote.example.com",
            username="testuser",
            port=2222,
            key_file=Path("/home/user/.ssh/id_rsa"),
            remote_base_path="/opt/n8n/scripts",
            workflow_name="My Workflow",
            transport="scp",
            changed_only=False,
            dry_run=True,
        )
        assert_that(config.port).is_equal_to(2222)
        assert_that(config.key_file).is_equal_to(Path("/home/user/.ssh/id_rsa"))
        assert_that(config.changed_only).is_false()
        assert_that(config.dry_run).is_true()


class TestScriptSyncManager:
    """Tests for ScriptSyncManager class"""

    def test_init(self, temp_dir: Path, mock_key_file: Path) -> None:
        """Test ScriptSyncManager initialization"""
        config = ScriptSyncConfig(
            scripts_dir=temp_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test",
            key_file=mock_key_file,
        )
        manager = ScriptSyncManager(config)
        assert_that(manager.config).is_equal_to(config)

    def test_sanitize_workflow_name_spaces(self) -> None:
        """Test workflow name sanitization with spaces"""
        result = ScriptSyncManager.sanitize_workflow_name("My Test Workflow")
        assert_that(result).is_equal_to("My_Test_Workflow")

    def test_sanitize_workflow_name_special_chars(self) -> None:
        """Test workflow name sanitization with special characters"""
        result = ScriptSyncManager.sanitize_workflow_name("Test-Workflow!@#$%")
        assert_that(result).is_equal_to("Test-Workflow")

    def test_sanitize_workflow_name_multiple_underscores(self) -> None:
        """Test workflow name sanitization collapses multiple spaces to single underscore"""
        result = ScriptSyncManager.sanitize_workflow_name("Test   Multiple   Spaces")
        assert_that(result).is_equal_to("Test_Multiple_Spaces")

    def test_sanitize_workflow_name_numbers(self) -> None:
        """Test workflow name sanitization preserves numbers"""
        result = ScriptSyncManager.sanitize_workflow_name("Workflow 123 Test")
        assert_that(result).is_equal_to("Workflow_123_Test")

    def test_sanitize_workflow_name_already_clean(self) -> None:
        """Test workflow name that's already clean"""
        result = ScriptSyncManager.sanitize_workflow_name("clean_workflow_name")
        assert_that(result).is_equal_to("clean_workflow_name")

    def test_find_local_scripts(self, temp_dir: Path, mock_key_file: Path) -> None:
        """Test finding local script files"""
        # Create scripts directory with files
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.py").write_text("# python script")
        (scripts_dir / "helper.js").write_text("// js script")
        (scripts_dir / "readme.md").write_text("# readme")  # not a script

        config = ScriptSyncConfig(
            scripts_dir=scripts_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test",
            key_file=mock_key_file,
        )
        manager = ScriptSyncManager(config)

        # Search for these script filenames
        script_filenames = {"test.py", "helper.js", "missing.py"}
        found = manager.find_local_scripts(script_filenames)

        assert_that(found).is_length(2)
        found_names = [p.name for p in found]
        assert_that(found_names).contains("test.py", "helper.js")
        assert_that(found_names).does_not_contain("missing.py", "readme.md")

    def test_find_local_scripts_nested(self, temp_dir: Path, mock_key_file: Path) -> None:
        """Test finding local scripts in nested directories"""
        # Create nested structure
        scripts_dir = temp_dir / "scripts"
        nested_dir = scripts_dir / "nested"
        nested_dir.mkdir(parents=True)
        (nested_dir / "deep.py").write_text("# deep script")

        config = ScriptSyncConfig(
            scripts_dir=scripts_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test",
            key_file=mock_key_file,
        )
        manager = ScriptSyncManager(config)

        script_filenames = {"deep.py"}
        found = manager.find_local_scripts(script_filenames)

        assert_that(found).is_length(1)
        assert_that(found[0].name).is_equal_to("deep.py")

    def test_sync_scripts_dry_run(self, temp_dir: Path, mock_key_file: Path) -> None:
        """Test sync_scripts in dry run mode"""
        # Create scripts
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.py").write_text("# script")

        config = ScriptSyncConfig(
            scripts_dir=scripts_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test Workflow",
            dry_run=True,
            changed_only=False,  # sync all
            key_file=mock_key_file,
        )
        manager = ScriptSyncManager(config)

        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Script",
                    "parameters": {"command": "python /opt/scripts/test.py"},
                },
            ],
        }

        result = manager.sync_scripts(workflow_data)

        # In dry run, no actual upload happens but synced_files shows what would be synced
        assert_that(result.success).is_true()
        assert_that(result.synced_files).is_not_empty()
        # Dry run marks files with [DRY RUN] prefix
        assert_that(result.synced_files[0]).starts_with("[DRY RUN]")

    def test_sync_scripts_no_scripts_found(self, temp_dir: Path, mock_key_file: Path) -> None:
        """Test sync_scripts when no scripts are found in workflow"""
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()

        config = ScriptSyncConfig(
            scripts_dir=scripts_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test",
            key_file=mock_key_file,
        )
        manager = ScriptSyncManager(config)

        # Workflow without execute command nodes
        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test",
            "nodes": [
                {"id": "node1", "type": "n8n-nodes-base.start", "name": "Start"},
            ],
        }

        result = manager.sync_scripts(workflow_data)

        assert_that(result.success).is_true()
        assert_that(result.scripts_synced).is_equal_to(0)

    def test_sync_scripts_with_transport(self, temp_dir: Path, mock_key_file: Path) -> None:
        """Test sync_scripts calls transport correctly"""
        # Create scripts
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "processor.py").write_text("# processor")

        config = ScriptSyncConfig(
            scripts_dir=scripts_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test Workflow",
            changed_only=False,  # sync all
            dry_run=False,
            key_file=mock_key_file,
        )
        manager = ScriptSyncManager(config)

        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Process",
                    "parameters": {"command": "python processor.py"},
                },
            ],
        }

        # Mock transport's upload_files method
        with patch.object(manager._transport, "upload_files") as mock_upload:
            mock_upload.return_value = MagicMock(
                success=True,
                files_transferred=1,
                bytes_transferred=100,
            )

            result = manager.sync_scripts(workflow_data)

        # Transport should be called
        mock_upload.assert_called_once()
        assert_that(result.success).is_true()

    def test_sync_scripts_changed_only(self, temp_dir: Path, mock_key_file: Path) -> None:
        """Test sync_scripts with changed_only=True uses git detection"""
        scripts_dir = temp_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "changed.py").write_text("# changed")
        (scripts_dir / "unchanged.py").write_text("# unchanged")

        config = ScriptSyncConfig(
            scripts_dir=scripts_dir,
            host="remote.example.com",
            username="testuser",
            remote_base_path="/opt/scripts",
            workflow_name="Test",
            changed_only=True,
            dry_run=False,
            key_file=mock_key_file,
        )
        manager = ScriptSyncManager(config)

        workflow_data: Dict[str, Any] = {
            "id": "test_wf",
            "name": "Test",
            "nodes": [
                {
                    "id": "node1",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Changed",
                    "parameters": {"command": "python changed.py"},
                },
                {
                    "id": "node2",
                    "type": "n8n-nodes-base.executeCommand",
                    "name": "Run Unchanged",
                    "parameters": {"command": "python unchanged.py"},
                },
            ],
        }

        # Mock git detector to return only changed.py
        with patch("api.workflow.script_sync.GitScriptDetector") as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector.get_modified_scripts.return_value = [
                MagicMock(
                    filename="changed.py",
                    path=scripts_dir / "changed.py",
                    needs_upload=True,
                )
            ]
            mock_detector.filter_by_workflow_scripts.return_value = [
                MagicMock(
                    filename="changed.py",
                    path=scripts_dir / "changed.py",
                    needs_upload=True,
                )
            ]
            mock_detector_class.return_value = mock_detector

            with patch.object(manager._transport, "upload_files") as mock_upload:
                mock_upload.return_value = MagicMock(
                    success=True,
                    files_transferred=1,
                    bytes_transferred=50,
                )

                result = manager.sync_scripts(workflow_data)

        # Only 1 file should be synced (changed.py), 1 skipped (unchanged.py)
        assert_that(result.success).is_true()


class TestScriptSyncResult:
    """Tests for ScriptSyncResult dataclass"""

    def test_result_creation_success(self) -> None:
        """Test ScriptSyncResult creation for success"""
        result = ScriptSyncResult(
            success=True,
            scripts_synced=3,
            scripts_skipped=2,
            synced_files=["a.py", "b.js", "c.cjs"],
        )
        assert_that(result.success).is_true()
        assert_that(result.scripts_synced).is_equal_to(3)
        assert_that(result.scripts_skipped).is_equal_to(2)
        assert_that(result.synced_files).is_length(3)

    def test_result_creation_failure(self) -> None:
        """Test ScriptSyncResult creation for failure"""
        result = ScriptSyncResult(
            success=False,
            scripts_synced=0,
            errors=["Connection refused"],
        )
        assert_that(result.success).is_false()
        assert_that(result.scripts_synced).is_equal_to(0)
        assert_that(result.errors).contains("Connection refused")

    def test_result_with_synced_files(self) -> None:
        """Test ScriptSyncResult with synced files list"""
        result = ScriptSyncResult(
            success=True,
            scripts_synced=1,
            synced_files=["script.py"],
        )
        assert_that(result.synced_files).is_length(1)
        assert_that(result.synced_files[0]).is_equal_to("script.py")

    def test_result_warnings(self) -> None:
        """Test ScriptSyncResult with warnings"""
        result = ScriptSyncResult(
            success=True,
            scripts_synced=2,
            warnings=["Script x.py not found locally"],
        )
        assert_that(result.warnings).is_length(1)
