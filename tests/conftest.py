#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for n8n_deploy_ tests
"""

import pytest
import tempfile
import shutil
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Generator, Optional, List
from unittest.mock import Mock, patch
from click.testing import CliRunner

# Add the project root to Python path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.config import n8n_deploy_Config, get_config
from api.n8n_deploy_db import n8n_deploy_DB
from api.manager import WorkflowManager
from api.api_keys import ApiKeyManager
from api.models import Workflow, WorkflowType, WorkflowStatus
from tests.helpers import (
    now_utc,
    create_test_workflow_data,
    create_test_workflow_json,
    create_test_api_key_data,
    create_workflow_file,
)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test isolation"""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config(temp_dir: Path) -> n8n_deploy_Config:
    """Create a test configuration with temporary directories"""
    config = n8n_deploy_Config(base_folder=temp_dir)
    config.ensure_directories()
    return config


@pytest.fixture
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """Create an in-memory SQLite database for testing"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def test_db(test_config: n8n_deploy_Config) -> n8n_deploy_DB:
    """Create a test database instance"""
    return n8n_deploy_DB(config=test_config)


@pytest.fixture
def test_manager(test_config: n8n_deploy_Config) -> WorkflowManager:
    """Create a test workflow manager instance"""
    return WorkflowManager(config=test_config)


@pytest.fixture
def test_api_key_manager(test_config: n8n_deploy_Config) -> ApiKeyManager:
    """Create a test API key manager instance"""
    return ApiKeyManager(config=test_config)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def mock_workflow_data() -> Dict[str, Any]:
    """Mock workflow data for testing"""
    return create_test_workflow_data(
        workflow_id="test_workflow_123",
        name="Test Workflow",
        description="A test workflow",
        file_path="workflows/test_workflow.json",
        node_count=5,
        tags=["test", "automation"],
    )


@pytest.fixture
def sample_workflow_json() -> Dict[str, Any]:
    """Sample n8n workflow JSON structure"""
    return create_test_workflow_json(
        workflow_id="test_workflow_123", name="Test Workflow", versionId="abc123"
    )


@pytest.fixture
def mock_n8n_response() -> Dict[str, Any]:
    """Mock n8n API response for workflow operations"""
    return {
        "data": {
            "id": "test_workflow_123",
            "name": "Test Workflow",
            "active": True,
            "nodes": [],
            "connections": {},
            "versionId": "abc123",
        }
    }


@pytest.fixture
def test_workflow_file(
    test_config: n8n_deploy_Config, sample_workflow_json: Dict[str, Any]
) -> Path:
    """Create a test workflow file"""
    return create_workflow_file(
        test_config,
        "test_workflow_123",
        "Test Workflow",
        "workflows/test_workflow.json",
    )


@pytest.fixture
def populated_test_db(
    test_db: n8n_deploy_DB, mock_workflow_data: Dict[str, Any]
) -> n8n_deploy_DB:
    """Database populated with test workflows"""
    workflow = Workflow(**mock_workflow_data)
    test_db.create_workflow(workflow)
    return test_db


@pytest.fixture
def mock_requests():
    """Mock requests module for external API calls"""
    with patch("api.manager.requests") as mock_req:
        # Configure default successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "123", "name": "Test"}}
        mock_req.get.return_value = mock_response
        mock_req.post.return_value = mock_response
        mock_req.put.return_value = mock_response
        mock_req.delete.return_value = mock_response
        yield mock_req


@pytest.fixture
def environment_vars() -> Generator[Dict[str, str], None, None]:
    """Fixture to safely modify environment variables during tests"""
    original_env = os.environ.copy()
    yield os.environ
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def no_emoji_env(
    environment_vars: Dict[str, str],
) -> Generator[Dict[str, str], None, None]:
    """Set up environment for no-emoji testing"""
    environment_vars["n8n_deploy__NO_EMOJI"] = "1"
    yield environment_vars


@pytest.fixture
def test_api_key_data() -> Dict[str, Any]:
    """Sample API key data for testing"""
    return create_test_api_key_data(
        name="test_key",
        api_key="test_api_key_12345",
        description="Test API key",
        expires_days=30,
    )


@pytest.fixture
def expired_api_key_data() -> Dict[str, Any]:
    """Expired API key data for testing"""
    return create_test_api_key_data(
        name="expired_key",
        api_key="expired_key_12345",
        description="Expired test key",
        expires_at=now_utc() - timedelta(days=1),
    )


@pytest.fixture
def mock_backup_file(test_config: n8n_deploy_Config) -> Path:
    """Create a mock backup file for testing"""
    backup_path = test_config.backups_path / "test_backup_20231201_120000.tar.gz"
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a simple tar.gz file for testing
    import tarfile

    with tarfile.open(backup_path, "w:gz") as tar:
        # Add a simple text file to the archive
        info = tarfile.TarInfo(name="test.txt")
        info.size = 12
        tar.addfile(info, fileobj=None)

    return backup_path


@pytest.fixture
def test_workflows_list() -> List[Dict[str, Any]]:
    """List of test workflows for bulk operations"""
    return [
        create_test_workflow_data(
            workflow_id="workflow_1",
            name="First Workflow",
            type="main",
            file_path="workflows/first.json",
            status="active",
        ),
        create_test_workflow_data(
            workflow_id="workflow_2",
            name="Second Workflow",
            type="subflow",
            file_path="workflows/second.json",
            status="inactive",
        ),
        create_test_workflow_data(
            workflow_id="workflow_3",
            name="Third Workflow",
            type="utility",
            file_path="workflows/third.json",
            status="archived",
        ),
    ]


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Pytest configuration setup"""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line(
        "markers", "filesystem: mark test as requiring filesystem operations"
    )


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test() -> Generator[None, None, None]:
    """Automatic cleanup after each test"""
    yield
    # Any global cleanup can go here
    pass
