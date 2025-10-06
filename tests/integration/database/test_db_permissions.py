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


class TestDbPermissions(DatabaseTestHelpers):
    """Test Db Permissions tests"""

    def test_database_permissions_handling(self) -> None:
        """Test database creation with proper permissions"""
        # Initialize database
        returncode, stdout, stderr = self.run_cli_command(["--data-dir", self.temp_dir, "db", "init"])

        assert returncode == 0
        db_path = Path(self.temp_dir) / "n8n-deploy.db"
        if db_path.exists():
            # Should be readable and writable by owner
            assert os.access(db_path, os.R_OK)
            assert os.access(db_path, os.W_OK)
