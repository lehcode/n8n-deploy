#!/usr/bin/env python3
"""
Standardized test utilities and patterns for n8n_deploy_
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from assertpy import assert_that
import pytest

from api.models import (
    Workflow,
    WorkflowVersion,
    WorkflowDependency,
    WorkflowConfiguration,
    WorkflowType,
    WorkflowStatus,
    DependencyType,
)


class TestAssertions:
    """Standardized assertion patterns for n8n_deploy_ tests"""

    @staticmethod
    def assert_workflow_valid(workflow: Workflow) -> None:
        """Assert that a workflow object is valid"""
        assert_that(workflow).is_not_none()
        assert_that(workflow.id).is_not_empty()
        assert_that(workflow.name).is_not_empty()
        assert_that(workflow.file_path).is_not_empty()
        # Enum fields store their values, not enum objects
        valid_types = [item.value for item in WorkflowType]
        valid_statuses = [item.value for item in WorkflowStatus]
        assert_that(workflow.type).is_in(*valid_types)
        assert_that(workflow.status).is_in(*valid_statuses)
        assert_that(workflow.node_count).is_greater_than_or_equal_to(0)
        assert_that(workflow.tags).is_instance_of(list)
        assert_that(workflow.created_at).is_instance_of(datetime)
        assert_that(workflow.updated_at).is_instance_of(datetime)

    @staticmethod
    def assert_workflow_equals(actual: Workflow, expected: Dict[str, Any]) -> None:
        """Assert that a workflow matches expected values"""
        if "id" in expected:
            assert_that(actual.id).is_equal_to(expected["id"])
        if "name" in expected:
            assert_that(actual.name).is_equal_to(expected["name"])
        if "type" in expected:
            assert_that(actual.type).is_equal_to(expected["type"])
        if "status" in expected:
            assert_that(actual.status).is_equal_to(expected["status"])
        if "file_path" in expected:
            assert_that(actual.file_path).is_equal_to(expected["file_path"])
        if "node_count" in expected:
            assert_that(actual.node_count).is_equal_to(expected["node_count"])
        if "tags" in expected:
            assert_that(actual.tags).is_equal_to(expected["tags"])

    @staticmethod
    def assert_datetime_recent(dt: datetime, tolerance_seconds: int = 10) -> None:
        """Assert that a datetime is recent (within tolerance)"""
        now = datetime.utcnow()
        diff = abs((now - dt).total_seconds())
        assert_that(diff).is_less_than_or_equal_to(tolerance_seconds)

    @staticmethod
    def assert_json_serializable(obj: Any) -> None:
        """Assert that an object can be serialized to JSON via Pydantic"""
        json_str = obj.model_dump_json()
        assert_that(json_str).is_not_empty()
        assert_that(json_str).contains('"')

    @staticmethod
    def assert_contains_keys(data: Dict[str, Any], keys: List[str]) -> None:
        """Assert that a dictionary contains all specified keys"""
        for key in keys:
            assert_that(data).contains_key(key)


class TestDataFactory:
    """Factory for creating test data objects"""

    @staticmethod
    def create_workflow(
        id: str = "test_workflow_001",
        name: str = "Test Workflow",
        workflow_type: WorkflowType = WorkflowType.MAIN,
        status: WorkflowStatus = WorkflowStatus.ACTIVE,
        file_path: str = "workflows/test.json",
        **kwargs,
    ) -> Workflow:
        """Create a test workflow with sensible defaults"""
        defaults = {
            "id": id,
            "name": name,
            "type": workflow_type,
            "status": status,
            "file_path": file_path,
            "node_count": 5,
            "tags": ["test"],
            "description": "Test workflow for unit testing",
        }
        defaults.update(kwargs)
        return Workflow(**defaults)

    @staticmethod
    def create_workflow_version(
        workflow_id: str = "test_workflow_001", version: str = "1.0.0", **kwargs
    ) -> WorkflowVersion:
        """Create a test workflow version with sensible defaults"""
        defaults = {
            "workflow_id": workflow_id,
            "version": version,
            "changes_summary": "Test version",
            "changes_detail": {"nodes": ["added_node_1"]},
            "created_by": "test_user",
        }
        defaults.update(kwargs)
        return WorkflowVersion(**defaults)

    @staticmethod
    def create_workflow_dependency(
        parent_id: str = "parent_workflow",
        child_id: str = "child_workflow",
        dep_type: DependencyType = DependencyType.SUBFLOW,
        **kwargs,
    ) -> WorkflowDependency:
        """Create a test workflow dependency with sensible defaults"""
        defaults = {
            "parent_workflow_id": parent_id,
            "child_workflow_id": child_id,
            "dependency_type": dep_type,
        }
        defaults.update(kwargs)
        return WorkflowDependency(**defaults)

    @staticmethod
    def create_workflow_configuration(
        workflow_id: str = "test_workflow_001", config_type: str = "settings", **kwargs
    ) -> WorkflowConfiguration:
        """Create a test workflow configuration with sensible defaults"""
        defaults = {
            "workflow_id": workflow_id,
            "config_type": config_type,
            "config_data": {"timeout": 30, "retries": 3},
            "is_active": True,
        }
        defaults.update(kwargs)
        return WorkflowConfiguration(**defaults)


class UtilityPatterns:
    """Common test patterns and decorators"""

    @staticmethod
    def test_model_creation(model_class, valid_data: Dict[str, Any]) -> Any:
        """Standard pattern for testing model creation"""
        instance = model_class(**valid_data)
        assert_that(instance).is_not_none()
        for key, expected_value in valid_data.items():
            actual_value = getattr(instance, key)
            assert_that(actual_value).is_equal_to(expected_value)
        return instance

    @staticmethod
    def test_model_serialization(instance: Any) -> Dict[str, Any]:
        """Standard pattern for testing model serialization"""
        # Test dict conversion
        data_dict = instance.model_dump()
        assert_that(data_dict).is_instance_of(dict)
        assert_that(data_dict).is_not_empty()

        # Test JSON conversion
        json_str = instance.model_dump_json()
        assert_that(json_str).is_instance_of(str)
        assert_that(json_str).is_not_empty()

        return data_dict

    @staticmethod
    def test_enum_values(enum_class, expected_values: List[str]) -> None:
        """Standard pattern for testing enum values"""
        actual_values = [item.value for item in enum_class]
        assert_that(actual_values).is_length(len(expected_values))
        for expected_value in expected_values:
            assert_that(actual_values).contains(expected_value)


# Pytest fixtures for common test objects
@pytest.fixture
def sample_workflow():
    """Fixture providing a standard test workflow"""
    return TestDataFactory.create_workflow()


@pytest.fixture
def sample_workflow_version():
    """Fixture providing a standard test workflow version"""
    return TestDataFactory.create_workflow_version()


@pytest.fixture
def sample_workflow_dependency():
    """Fixture providing a standard test workflow dependency"""
    return TestDataFactory.create_workflow_dependency()


@pytest.fixture
def sample_workflow_configuration():
    """Fixture providing a standard test workflow configuration"""
    return TestDataFactory.create_workflow_configuration()


@pytest.fixture
def test_assertions():
    """Fixture providing test assertion utilities"""
    return TestAssertions()


@pytest.fixture
def test_factory():
    """Fixture providing test data factory"""
    return TestDataFactory()
