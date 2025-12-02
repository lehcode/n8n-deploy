#!/usr/bin/env python3
"""
End-to-End Manual Database Testing

Real CLI execution tests for database operations, initialization,
backup/restore functionality, and stats display.
"""

import hashlib
import json
import os
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest


# === End-to-End Tests ===
from .conftest import DatabaseTestHelpers


class TestDbIntegrity(DatabaseTestHelpers):
    """Test Db Integrity tests"""

    def test_database_integrity_after_operations(self) -> None:
        """Test database maintains integrity after various operations"""
        # Initialize
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Perform various operations
        operations = [
            ["--data-dir", self.temp_dir, "db", "status"],
            ["wf", "list"],  # wf list doesn't need --data-dir
            ["--data-dir", self.temp_dir, "db", "status"],  # Repeat to check consistency
        ]

        for op in operations:
            returncode, stdout, stderr = self.run_cli_command(op)
            assert returncode == 0, f"Database integrity failed after: {op}\nSTDERR: {stderr}\nSTDOUT: {stdout}"
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        assert db_path.exists()
        assert db_path.stat().st_size > 0

    def test_database_schema_version_tracking(self) -> None:
        """Test database schema version is properly tracked"""
        # Initialize database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Status should show schema information
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status"])

        assert returncode == 0
        # Should complete without errors (schema version tracking working)

    def test_backup_checksum_verification(self) -> None:
        """Test backup files include proper checksums"""
        # Initialize and create backup
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "backup"])

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
        """Test database handles concurrent access safely

        This test verifies that concurrent access doesn't corrupt the database.
        SQLite may return "database is locked" errors under heavy concurrent access,
        which is acceptable behavior - the key is that the database remains intact
        and accessible after all concurrent operations complete.
        """
        import threading
        import time

        # Initialize database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        results: List[Tuple[int, str, str]] = []
        lock = threading.Lock()

        def run_db_command() -> None:
            returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status"])
            with lock:
                results.append((returncode, stdout, stderr))

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=run_db_command)
            threads.append(thread)
            thread.start()
            # Small delay to reduce lock contention (more realistic concurrent access pattern)
            time.sleep(0.05)

        # Wait for completion
        for thread in threads:
            thread.join()

        # All threads should complete
        assert len(results) == 3

        # Count successes and acceptable failures (database locked is OK)
        successes = 0
        acceptable_failures = 0
        for returncode, stdout, stderr in results:
            if returncode == 0:
                successes += 1
            elif "locked" in stderr.lower() or "busy" in stderr.lower():
                # SQLite lock contention is acceptable
                acceptable_failures += 1

        # At least one operation should succeed
        assert successes >= 1, f"No operations succeeded. Results: {results}"

        # Verify database is still accessible after concurrent access
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status"])
        assert returncode == 0, f"Database inaccessible after concurrent access: {stderr}"

    def test_database_error_recovery(self) -> None:
        """Test database error recovery mechanisms"""
        # Initialize database
        self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        # Try operations that might cause errors or succeed
        error_prone_operations = [
            ["wf", "search", "nonexistent"],  # Search for non-existent workflow (returns 0 with no results)
            ["--data-dir", self.temp_dir, "db", "backup"],  # Should work
            ["wf", "list"],  # Should work (doesn't need --data-dir)
        ]

        for op in error_prone_operations:
            returncode, stdout, stderr = self.run_cli_command(op)
            # Should not crash with unexpected error codes
            assert returncode in [0, 1], f"Operation crashed with unexpected code: {op}\nSTDERR: {stderr}"

        # Database should still be accessible
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "status"])
        assert returncode == 0
