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
    WorkflowStatus,
)

from tests.test_utils import TestAssertions, TestDataFactory


# === Workflow Model Tests ===
class TestWorkflowModel:
    """Test Workflow model validation and functionality"""

    def test_workflow_creation_basic(self):
        """Test basic workflow creation"""
        workflow = Workflow(id="test_workflow", name="Test Workflow")

        assert workflow.id == "test_workflow"
        assert workflow.name == "Test Workflow"
        assert workflow.status == WorkflowStatus.ACTIVE  # Default value
        assert workflow.push_count == 0  # Default value
        assert workflow.pull_count == 0  # Default value

    def test_workflow_creation_with_all_fields(self):
        """Test workflow creation with all optional fields"""
        from datetime import datetime

        workflow = Workflow(
            id="full_workflow",
            name="Full Test Workflow",
            status=WorkflowStatus.INACTIVE,
            push_count=5,
            pull_count=3,
            n8n_version_id="test_version_123",
            last_synced=datetime.utcnow(),
        )

        assert workflow.id == "full_workflow"
        assert workflow.name == "Full Test Workflow"
        assert workflow.status == WorkflowStatus.INACTIVE
        assert workflow.push_count == 5
        assert workflow.pull_count == 3
        assert workflow.n8n_version_id == "test_version_123"
        assert workflow.last_synced is not None
