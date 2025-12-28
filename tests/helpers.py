#!/usr/bin/env python3
"""
Test helpers and utilities for consistent testing patterns
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

import pytest

from api.models import Workflow
from api.config import AppConfig


def now_utc() -> datetime:
    """Get current UTC datetime using modern timezone-aware approach."""
    return datetime.now(timezone.utc)


def create_test_workflow(
    workflow_id: str = "test_workflow",
    name: str = "Test Workflow",
    file_path: str = "workflows/test.json",
    **kwargs: Any,
) -> Workflow:
    """Create a test workflow with sensible defaults."""
    return Workflow(
        id=workflow_id,
        name=name,
        file_path=file_path,
        created_at=now_utc(),
        updated_at=now_utc(),
        **kwargs,
    )


def create_test_workflow_data(
    workflow_id: str = "test_workflow", name: str = "Test Workflow", **kwargs: Any
) -> Dict[str, Any]:
    """Create test workflow data as dictionary."""
    return {
        "id": workflow_id,
        "name": name,
        "file_path": "workflows/test.json",
        "tags": [],
        "created_at": now_utc().isoformat(),
        "updated_at": now_utc().isoformat(),
        "last_synced": None,
        "n8n_version_id": None,
        **kwargs,
    }


def create_test_workflow_json(
    workflow_id: str = "test_workflow",
    name: str = "Test Workflow",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create test n8n workflow JSON structure."""
    # Simple test workflow with one start node
    nodes = [
        {
            "parameters": {},
            "id": "start_node",
            "name": "Start",
            "type": "n8n-nodes-base.start",
            "typeVersion": 1,
            "position": [250, 300],
        }
    ]

    connections = {}

    return {
        "id": workflow_id,
        "name": name,
        "active": True,
        "nodes": nodes,
        "connections": connections,
        "staticData": {},
        "settings": {"executionOrder": "v1"},
        "createdAt": now_utc().isoformat() + "Z",
        "updatedAt": now_utc().isoformat() + "Z",
        "versionId": f"version_{workflow_id}",
        **kwargs,
    }


def create_test_api_key_data(
    name: str = "test_key",
    api_key: str = "test_api_key_12345",
    **kwargs: Any,
) -> Dict[str, Any]:
    """Create test API key data."""
    return {
        "name": name,
        "api_key": api_key,
        "description": "Test API key",
        **kwargs,
    }


def create_workflow_file(
    config: AppConfig,
    workflow_id: str,
    name: str = "Test Workflow",
    file_path: Optional[str] = None,
) -> Path:
    """Create a test workflow JSON file."""
    if file_path is None:
        file_path = f"workflows/{workflow_id}.json"

    full_path = config.workflows_path / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    workflow_json = create_test_workflow_json(workflow_id, name)
    with open(full_path, "w") as f:
        json.dump(workflow_json, f, indent=2)

    return full_path


def assert_workflow_equals(actual: Workflow, expected: Workflow, ignore_timestamps: bool = True) -> None:
    """Assert two workflows are equal, optionally ignoring timestamps."""
    assert actual.id == expected.id
    assert actual.name == expected.name
    assert actual.file_path == expected.file_path
    assert actual.tags == expected.tags
    assert actual.description == expected.description
    assert actual.last_synced == expected.last_synced
    assert actual.n8n_version_id == expected.n8n_version_id

    if not ignore_timestamps:
        assert actual.created_at == expected.created_at
        assert actual.updated_at == expected.updated_at


def assert_datetime_recent(dt: datetime, tolerance_seconds: int = 5) -> None:
    """Assert that a datetime is recent (within tolerance)."""
    now = now_utc()
    diff = abs((now - dt).total_seconds())
    assert diff <= tolerance_seconds, f"Datetime {dt} is not recent (diff: {diff}s)"


def assert_list_contains_ids(items: List[Dict[str, Any]], expected_ids: List[str]) -> None:
    """Assert that a list of dictionaries contains specific IDs."""
    actual_ids = [item["id"] for item in items]
    for expected_id in expected_ids:
        assert expected_id in actual_ids, f"ID '{expected_id}' not found in {actual_ids}"


def assert_json_schema_valid(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Assert that JSON data has required fields."""
    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from {list(data.keys())}"


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, status_code: int = 200, json_data: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self) -> Dict[str, Any]:
        return self._json_data


def create_mock_n8n_response(workflow_id: str = "test_workflow", name: str = "Test Workflow") -> MockResponse:
    """Create mock n8n API response."""
    return MockResponse(
        200,
        {
            "data": {
                "id": workflow_id,
                "name": name,
                "active": True,
                "nodes": [],
                "connections": {},
                "versionId": f"version_{workflow_id}",
            }
        },
    )


def time_range(start: datetime, end: datetime) -> bool:
    """Check if two datetimes are within reasonable range."""
    return (end - start).total_seconds() <= 5


def workflow_ids_from_list(workflows: List[Dict[str, Any]]) -> List[str]:
    """Extract IDs from list of workflow dictionaries."""
    return [wf["id"] for wf in workflows]


def clear_database_table(db, table_name: str) -> None:
    """Clear a specific database table for testing."""
    with db.get_connection() as conn:
        conn.execute(f"DELETE FROM {table_name}")
        conn.commit()


def create_test_backup_metadata(
    backup_filename: str, workflow_count: int = 0, checksum: str = "test_checksum_123"
) -> List[Dict[str, Any]]:
    """Create test backup metadata entries."""
    timestamp = now_utc().isoformat()
    return [
        {
            "config_key": f"backup_{timestamp}_filename",
            "config_value": backup_filename,
            "created_at": now_utc().isoformat(),
        },
        {
            "config_key": f"backup_{timestamp}_workflow_count",
            "config_value": str(workflow_count),
            "created_at": now_utc().isoformat(),
        },
        {
            "config_key": f"backup_{timestamp}_checksum",
            "config_value": checksum,
            "created_at": now_utc().isoformat(),
        },
    ]


COMMON_SERVICES = ["n8n", "openai", "anthropic", "custom"]


def generate_test_workflows(count: int = 3) -> List[Dict[str, Any]]:
    """Generate multiple test workflows."""
    workflows = []
    for i in range(count):
        workflows.append(
            create_test_workflow_data(
                workflow_id=f"test_workflow_{i}",
                name=f"Test Workflow {i}",
                file_path=f"workflows/test_{i}.json",
            )
        )
    return workflows


def generate_test_api_keys(count: int = 3) -> List[Dict[str, Any]]:
    """Generate multiple test API keys."""
    api_keys = []
    for i in range(count):
        api_keys.append(
            create_test_api_key_data(
                name=f"test_key_{i}",
                api_key=f"test_api_key_{i}_12345",
            )
        )
    return api_keys


def assert_json_output_valid(stdout: str) -> Dict[str, Any]:
    """Assert stdout contains valid JSON and return parsed data.

    Centralized from multiple conftest.py files.

    Args:
        stdout: The string output to parse as JSON

    Returns:
        Parsed JSON data as dictionary

    Raises:
        pytest.fail: If stdout is not valid JSON
    """
    try:
        data = json.loads(stdout)
        return data
    except json.JSONDecodeError as e:
        pytest.fail(f"Output is not valid JSON: {e}\nOutput: {stdout}")
