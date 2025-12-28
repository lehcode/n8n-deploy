#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for n8n_deploy_ tests
"""

import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import Mock, patch

import pytest
from api.workflow import WorkflowApi
from click.testing import CliRunner

from api.api_keys import KeyApi
from api.config import AppConfig
from api.db import DBApi
from api.models import Workflow
from tests.helpers import (
    create_test_api_key_data,
    create_test_workflow_data,
    create_test_workflow_json,
    create_workflow_file,
    now_utc,
)

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test isolation"""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config(temp_dir: Path) -> AppConfig:
    """Create a test configuration with temporary directories"""
    config = AppConfig(base_folder=temp_dir)
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
def test_db(test_config: AppConfig) -> DBApi:
    """Create a test database instance"""
    db = DBApi(config=test_config)
    db.schema_api.initialize_database()
    return db


@pytest.fixture
def test_manager(test_config: AppConfig) -> WorkflowApi:
    """Create a test workflow manager instance"""
    manager = WorkflowApi(config=test_config)
    manager.db.schema_api.initialize_database()
    return manager


@pytest.fixture
def test_api_key_manager(test_config: AppConfig) -> KeyApi:
    """Create a test API key manager instance"""
    db = DBApi(config=test_config)
    db.schema_api.initialize_database()
    return KeyApi(db=db, config=test_config)


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
        tags=["test", "automation"],
    )


@pytest.fixture
def sample_workflow_json() -> Dict[str, Any]:
    """Sample n8n workflow JSON structure"""
    return create_test_workflow_json(workflow_id="test_workflow_123", name="Test Workflow", versionId="abc123")


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
def test_workflow_file(test_config: AppConfig) -> Path:
    """Create a test workflow file"""
    return create_workflow_file(
        test_config,
        "test_workflow_123",
        "Test Workflow",
        "workflows/test_workflow.json",
    )


@pytest.fixture
def populated_test_db(test_db: DBApi, mock_workflow_data: Dict[str, Any]) -> DBApi:
    """Database populated with test workflows"""
    wf = Workflow(**mock_workflow_data)
    test_db.add_workflow(wf)
    return test_db


@pytest.fixture
def mock_requests() -> Generator[Mock, None, None]:
    """Mock requests module for external API calls"""
    with patch("api.manager.requests") as mock_req:
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
def mock_backup_file(test_config: AppConfig) -> Path:
    """Create a mock backup file for testing"""
    backup_path = test_config.backups_path / "test_backup_20231201_120000.tar.gz"
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    import tarfile

    with tarfile.open(backup_path, "w:gz") as tar:
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
            file_path="workflows/first.json",
            status="active",
        ),
        create_test_workflow_data(
            workflow_id="workflow_2",
            name="Second Workflow",
            file_path="workflows/second.json",
            status="inactive",
        ),
        create_test_workflow_data(
            workflow_id="workflow_3",
            name="Third Workflow",
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
    config.addinivalue_line("markers", "filesystem: mark test as requiring filesystem operations")


@pytest.fixture(autouse=True)
def cleanup_after_test() -> Generator[None, None, None]:
    """Automatic cleanup after each test"""
    yield
