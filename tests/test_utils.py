#!/usr/bin/env python3
"""
Standardized test utilities and patterns for n8n_deploy_
"""

from datetime import datetime
from typing import Any, Dict, List, Type

import pytest
from assertpy import assert_that

from api.models import Workflow, WorkflowConfiguration, WorkflowVersion


class TestAssertions:
    """Standardized assertion patterns for n8n_deploy_ tests"""

    @staticmethod
    def assert_workflow_valid(wf: Workflow) -> None:
        """Assert that a wf object is valid"""
        assert_that(wf).is_not_none()
        assert_that(wf.id).is_not_empty()
        assert_that(wf.name).is_not_empty()
        assert_that(wf.file_path).is_not_empty()
        assert_that(wf.tags).is_instance_of(list)
        assert_that(wf.created_at).is_instance_of(datetime)
        assert_that(wf.updated_at).is_instance_of(datetime)

    @staticmethod
    def assert_workflow_equals(actual: Workflow, expected: Dict[str, Any]) -> None:
        """Assert that a wf matches expected values"""
        if "id" in expected:
            assert_that(actual.id).is_equal_to(expected["id"])
        if "name" in expected:
            assert_that(actual.name).is_equal_to(expected["name"])
        if "status" in expected:
            assert_that(actual.status).is_equal_to(expected["status"])
        if "file_path" in expected:
            assert_that(actual.file_path).is_equal_to(expected["file_path"])
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
        file_path: str = "workflows/test.json",
        **kwargs: Any,
    ) -> Workflow:
        """Create a test wf with sensible defaults"""
        defaults = {
            "id": id,
            "name": name,
            "file_path": file_path,
            "tags": ["test"],
            "description": "Test wf for unit testing",
        }
        defaults.update(kwargs)
        return Workflow(**defaults)

    @staticmethod
    def create_workflow_version(
        workflow_id: str = "test_workflow_001",
        version: str = "1.0.0",
        **kwargs: Any,
    ) -> WorkflowVersion:
        """Create a test wf version with sensible defaults"""
        defaults = {
            "workflow_id": workflow_id,
            "version": version,
            "changes_summary": "Initial version",
            "created_by": "test_user",
        }
        defaults.update(kwargs)
        return WorkflowVersion(**defaults)


class UtilityPatterns:
    """Common test patterns and decorators"""

    @staticmethod
    def test_model_creation(model_class: Type[Any], valid_data: Dict[str, Any]) -> Any:
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
    def test_enum_values(enum_class: Type[Any], expected_values: List[str]) -> None:
        """Standard pattern for testing enum values"""
        actual_values = [item.value for item in enum_class]
        assert_that(actual_values).is_length(len(expected_values))
        for expected_value in expected_values:
            assert_that(actual_values).contains(expected_value)


# Pytest fixtures for common test objects
@pytest.fixture
def sample_workflow() -> Workflow:
    """Fixture providing a standard test wf"""
    return TestDataFactory.add_workflow()


@pytest.fixture
def sample_workflow_version() -> WorkflowVersion:
    """Fixture providing a standard test wf version"""
    return TestDataFactory.create_workflow_version()


# @pytest.fixture
# def sample_workflow_dependency():
#     """Fixture providing a standard test wf dependency"""
#     return TestDataFactory.create_workflow_dependency()


@pytest.fixture
def sample_workflow_configuration() -> WorkflowConfiguration:
    """Fixture providing a standard test wf configuration"""
    return TestDataFactory.create_workflow_configuration()


@pytest.fixture
def test_assertions() -> TestAssertions:
    """Fixture providing test assertion utilities"""
    return TestAssertions()


@pytest.fixture
def test_factory() -> TestDataFactory:
    """Fixture providing test data factory"""
    return TestDataFactory()
