#!/usr/bin/env python3
"""
Unit tests for n8n_deploy_ data models
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from assertpy import assert_that

from api.models import (
    Workflow,
    WorkflowDependency,
    WorkflowConfiguration,
    DatabaseStats,
    WorkflowType,
    WorkflowStatus,
    DependencyType,
)

from tests.test_utils import TestAssertions, TestDataFactory, UtilityPatterns


class TestEnums:
    """Test enum classes and their values"""

    def test_workflow_type_enum_values(self):
        """Test WorkflowType enum has correct values"""
        UtilityPatterns.test_enum_values(WorkflowType, ["main", "subflow", "utility"])

    def test_workflow_status_enum_values(self):
        """Test WorkflowStatus enum has correct values"""
        UtilityPatterns.test_enum_values(
            WorkflowStatus, ["active", "inactive", "archived"]
        )


class TestWorkflowModel:
    """Test Workflow model validation and functionality"""

    @pytest.mark.parametrize(
        "workflow_type", [WorkflowType.MAIN, WorkflowType.SUBFLOW, WorkflowType.UTILITY]
    )
    def test_workflow_types(self, workflow_type):
        """Test workflow creation with different types"""
        workflow = Workflow(
            id=f"type_test_{workflow_type.value}",
            name=f"Test {workflow_type.value} Workflow",
            file_path="test.json",
            type=workflow_type,
        )

        assert workflow.type == workflow_type

    @pytest.mark.parametrize(
        "workflow_status", [WorkflowStatus.ACTIVE, WorkflowStatus.INACTIVE]
    )
    def test_workflow_statuses(self, workflow_status):
        """Test workflow creation with different statuses"""
        workflow = Workflow(
            id=f"status_test_{workflow_status.value}",
            name=f"Test {workflow_status.value} Workflow",
            file_path="test.json",
            status=workflow_status,
        )

        assert workflow.status == workflow_status
