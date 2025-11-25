"""Unit tests for api/db/backup.py module

Tests for BackupApi class methods.
"""

import time
from pathlib import Path
from typing import Any, Dict

import pytest
from assertpy import assert_that

from api.config import AppConfig
from api.db.backup import BackupApi


class TestBackupApi:
    """Tests for BackupApi class methods"""

    def test_create_backup_record(self, temp_dir: Path) -> None:
        """Test create_backup_record creates a record in the database"""
        # Setup
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create backup metadata
        metadata: Dict[str, Any] = {
            "name": "test_backup_20231201",
            "backup_path": "/tmp/backups/test_backup.tar.gz",
            "checksum": "sha256_abc123",
        }

        # Execute
        result = backup_api.create_backup_record(metadata)

        # Verify
        assert_that(result).is_true()

        # Verify record exists
        history = backup_api.get_backup_history()
        assert_that(len(history)).is_equal_to(1)
        assert_that(history[0]["name"]).is_equal_to("test_backup_20231201")
        assert_that(history[0]["backup_path"]).is_equal_to("/tmp/backups/test_backup.tar.gz")
        assert_that(history[0]["checksum"]).is_equal_to("sha256_abc123")
        assert_that(history[0]["is_active"]).is_true()

    def test_create_backup_record_auto_name(self, temp_dir: Path) -> None:
        """Test create_backup_record generates auto name when not provided"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create metadata without name
        metadata: Dict[str, Any] = {
            "backup_path": "/tmp/backups/auto_backup.tar.gz",
            "checksum": "sha256_def456",
        }

        result = backup_api.create_backup_record(metadata)
        assert_that(result).is_true()

        history = backup_api.get_backup_history()
        assert_that(history[0]["name"]).starts_with("backup_")

    def test_get_backup_history(self, temp_dir: Path) -> None:
        """Test get_backup_history returns records in DESC order by created_at"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create multiple backups
        for i in range(3):
            metadata = {
                "name": f"backup_{i}",
                "backup_path": f"/tmp/backups/backup_{i}.tar.gz",
                "checksum": f"checksum_{i}",
            }
            backup_api.create_backup_record(metadata)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Get history
        history = backup_api.get_backup_history()

        # Verify order (most recent first)
        assert_that(len(history)).is_equal_to(3)
        assert_that(history[0]["name"]).is_equal_to("backup_2")
        assert_that(history[1]["name"]).is_equal_to("backup_1")
        assert_that(history[2]["name"]).is_equal_to("backup_0")

    def test_get_backup_history_empty(self, temp_dir: Path) -> None:
        """Test get_backup_history returns empty list when no backups"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        history = backup_api.get_backup_history()
        assert_that(history).is_empty()

    def test_get_backup_by_filename(self, temp_dir: Path) -> None:
        """Test get_backup_by_filename finds backup by partial filename match"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create backups
        backup_api.create_backup_record(
            {
                "name": "daily_backup",
                "backup_path": "/backups/daily_20231201_120000.tar.gz",
                "checksum": "abc123",
            }
        )
        backup_api.create_backup_record(
            {
                "name": "weekly_backup",
                "backup_path": "/backups/weekly_20231201_120000.tar.gz",
                "checksum": "def456",
            }
        )

        # Find by partial filename
        result = backup_api.get_backup_by_filename("daily")
        assert_that(result).is_not_none()
        assert_that(result["name"]).is_equal_to("daily_backup")

        # Find by date pattern
        result = backup_api.get_backup_by_filename("20231201")
        assert_that(result).is_not_none()

    def test_get_backup_by_filename_not_found(self, temp_dir: Path) -> None:
        """Test get_backup_by_filename returns None when not found"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        result = backup_api.get_backup_by_filename("nonexistent")
        assert_that(result).is_none()

    def test_update_backup_status(self, temp_dir: Path) -> None:
        """Test update_backup_status toggles is_active flag"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create backup
        backup_api.create_backup_record(
            {
                "name": "test_backup",
                "backup_path": "/backups/test.tar.gz",
                "checksum": "checksum123",
            }
        )

        # Get backup ID
        history = backup_api.get_backup_history()
        backup_id = history[0]["id"]
        assert_that(history[0]["is_active"]).is_true()

        # Deactivate
        result = backup_api.update_backup_status(backup_id, is_active=False)
        assert_that(result).is_true()

        # Verify deactivated
        history = backup_api.get_backup_history()
        assert_that(history[0]["is_active"]).is_false()

        # Reactivate
        result = backup_api.update_backup_status(backup_id, is_active=True)
        assert_that(result).is_true()

        history = backup_api.get_backup_history()
        assert_that(history[0]["is_active"]).is_true()

    def test_update_backup_status_nonexistent(self, temp_dir: Path) -> None:
        """Test update_backup_status returns False for nonexistent backup"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        result = backup_api.update_backup_status(99999, is_active=False)
        assert_that(result).is_false()

    def test_delete_backup_record(self, temp_dir: Path) -> None:
        """Test delete_backup_record removes record from database"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create backup
        backup_api.create_backup_record(
            {
                "name": "to_delete",
                "backup_path": "/backups/delete_me.tar.gz",
                "checksum": "delete123",
            }
        )

        # Verify exists
        history = backup_api.get_backup_history()
        assert_that(len(history)).is_equal_to(1)
        backup_id = history[0]["id"]

        # Delete
        result = backup_api.delete_backup_record(backup_id)
        assert_that(result).is_true()

        # Verify deleted
        history = backup_api.get_backup_history()
        assert_that(history).is_empty()

    def test_delete_backup_record_nonexistent(self, temp_dir: Path) -> None:
        """Test delete_backup_record returns False for nonexistent backup"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        result = backup_api.delete_backup_record(99999)
        assert_that(result).is_false()

    def test_cleanup_old_backups(self, temp_dir: Path) -> None:
        """Test cleanup_old_backups keeps only the most recent keep_count records"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create 5 backups
        for i in range(5):
            backup_api.create_backup_record(
                {
                    "name": f"backup_{i}",
                    "backup_path": f"/backups/backup_{i}.tar.gz",
                    "checksum": f"checksum_{i}",
                }
            )
            time.sleep(0.01)  # Ensure different timestamps

        # Verify 5 backups exist
        history = backup_api.get_backup_history()
        assert_that(len(history)).is_equal_to(5)

        # Keep only 2 most recent
        deleted_count = backup_api.cleanup_old_backups(keep_count=2)

        # Verify 3 were deleted
        assert_that(deleted_count).is_equal_to(3)

        # Verify only 2 remain (most recent)
        history = backup_api.get_backup_history()
        assert_that(len(history)).is_equal_to(2)
        assert_that(history[0]["name"]).is_equal_to("backup_4")
        assert_that(history[1]["name"]).is_equal_to("backup_3")

    def test_cleanup_old_backups_no_cleanup_needed(self, temp_dir: Path) -> None:
        """Test cleanup_old_backups returns 0 when no cleanup needed"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        # Create 2 backups
        for i in range(2):
            backup_api.create_backup_record(
                {
                    "name": f"backup_{i}",
                    "backup_path": f"/backups/backup_{i}.tar.gz",
                    "checksum": f"checksum_{i}",
                }
            )

        # Try to keep 10 (more than exist)
        deleted_count = backup_api.cleanup_old_backups(keep_count=10)

        assert_that(deleted_count).is_equal_to(0)
        history = backup_api.get_backup_history()
        assert_that(len(history)).is_equal_to(2)

    def test_cleanup_old_backups_empty_database(self, temp_dir: Path) -> None:
        """Test cleanup_old_backups handles empty database"""
        config = AppConfig(base_folder=temp_dir)
        config.ensure_directories()
        backup_api = BackupApi(config=config)
        backup_api.schema.initialize_database()

        deleted_count = backup_api.cleanup_old_backups(keep_count=5)
        assert_that(deleted_count).is_equal_to(0)
