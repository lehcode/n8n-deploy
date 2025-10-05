#!/usr/bin/env python3
"""
Unit tests for n8n_deploy_ data models
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest
from assertpy import assert_that

from api.models import Workflow, WorkflowStatus
from tests.test_utils import TestAssertions, TestDataFactory


# === Workflow Model Tests ===
class TestWorkflowModel:
    """Test Workflow model validation and functionality"""

    def test_workflow_creation_basic(self):
        """Test basic wf creation"""
        wf = Workflow(id="test_workflow", name="Test Workflow")

        assert wf.id == "test_workflow"
        assert wf.name == "Test Workflow"
        assert wf.status == WorkflowStatus.ACTIVE  # Default value
        assert wf.push_count == 0  # Default value
        assert wf.pull_count == 0  # Default value

    def test_workflow_creation_with_all_fields(self):
        """Test wf creation with all optional fields"""
        from datetime import datetime

        wf = Workflow(
            id="full_workflow",
            name="Full Test Workflow",
            status=WorkflowStatus.INACTIVE,
            push_count=5,
            pull_count=3,
            n8n_version_id="test_version_123",
            last_synced=datetime.utcnow(),
        )

        assert wf.id == "full_workflow"
        assert wf.name == "Full Test Workflow"
        assert wf.status == WorkflowStatus.INACTIVE
        assert wf.push_count == 5
        assert wf.pull_count == 3
        assert wf.n8n_version_id == "test_version_123"
        assert wf.last_synced is not None
