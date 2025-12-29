"""Shared fixtures for workflow unit tests."""

from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock database."""
    return MagicMock()


@pytest.fixture
def mock_config(temp_dir: Path) -> MagicMock:
    """Create a mock config with flow_folder set."""
    mock = MagicMock()
    mock.flow_folder = temp_dir / "workflows"
    mock.flow_folder_explicit = True
    return mock


@pytest.fixture
def mock_api_manager() -> MagicMock:
    """Create a mock API manager."""
    return MagicMock()


@pytest.fixture
def workflows_path(temp_dir: Path) -> Path:
    """Create and return workflows directory."""
    path = temp_dir / "workflows"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def sample_workflow_data() -> Dict[str, Any]:
    """Return sample workflow data for tests."""
    return {
        "id": "test_wf_123",
        "name": "Test Workflow",
        "active": True,
        "nodes": [{"id": "node1", "type": "start"}],
        "connections": {},
    }
