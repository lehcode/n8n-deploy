#!/usr/bin/env python3
"""
Unit tests for n8n_deploy_ database management
"""

import pytest
import sqlite3
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, Mock

from assertpy import assert_that

from api.n8n_deploy_db import n8n_deploy_DB
from api.models import Workflow, WorkflowType, WorkflowStatus, DatabaseStats
from api.config import n8n_deploy_Config


class Testn8n_deploy_DBInitialization:
    """Test database initialization and setup"""

    @pytest.mark.parametrize("init_method", ["config", "db_path"])
    def test_db_initialization_methods(self, temp_dir, test_config, init_method):
        """Test database initialization with different methods"""
        if init_method == "config":
            db = n8n_deploy_DB(config=test_config)
            expected_path = test_config.database_path
        else:  # db_path
            db_path = temp_dir / "test.db"
            db = n8n_deploy_DB(db_path=db_path)
            expected_path = db_path

        assert_that(db.db_path).is_equal_to(expected_path)
        assert_that(db.db_path.exists()).is_true()
        if init_method == "config":
            assert_that(db.db_path.is_file()).is_true()


class TestWorkflowCRUDOperations:
    """Test Create, Read, Update, Delete operations for workflows"""

    def test_create_workflow_basic(self, test_db, mock_workflow_data):
        """Test adding a basic workflow"""
        workflow = Workflow(**mock_workflow_data)
        result = test_db.create_workflow(workflow)

        assert_that(result).is_true()

        # Verify workflow was added
        retrieved = test_db.get_workflow(workflow.id)
        assert_that(retrieved).is_not_none()
        assert_that(retrieved.id).is_equal_to(workflow.id)
        assert_that(retrieved.name).is_equal_to(workflow.name)

    def test_create_workflow_duplicate_id_fails(self, test_db, mock_workflow_data):
        """Test adding workflow with duplicate ID fails"""
        workflow1 = Workflow(**mock_workflow_data)
        workflow2 = Workflow(**mock_workflow_data)  # Same ID

        # First addition should succeed
        workflow_id = test_db.create_workflow(workflow1)
        assert_that(workflow_id).is_equal_to(workflow1.id)

        # Second addition should fail with IntegrityError
        with pytest.raises(sqlite3.IntegrityError):
            test_db.create_workflow(workflow2)

    def test_get_workflow_existing(self, populated_test_db, mock_workflow_data):
        """Test retrieving an existing workflow"""
        workflow_id = mock_workflow_data["id"]
        workflow = populated_test_db.get_workflow(workflow_id)

        assert_that(workflow).is_not_none()
        assert_that(workflow.id).is_equal_to(workflow_id)
        assert_that(workflow.name).is_equal_to(mock_workflow_data["name"])
        assert_that(workflow).is_instance_of(Workflow)

    def test_get_workflow_nonexistent(self, test_db):
        """Test retrieving non-existent workflow returns None"""
        workflow = test_db.get_workflow("nonexistent_id")
        assert_that(workflow).is_none()

    def test_list_workflows_empty_database(self, test_db):
        """Test listing workflows from empty database"""
        workflows = test_db.list_workflows()
        assert_that(workflows).is_empty()

    def test_list_workflows_populated_database(self, test_db, test_workflows_list):
        """Test listing workflows from populated database"""
        # Add multiple workflows
        for wf_data in test_workflows_list:
            workflow = Workflow(**wf_data)
            test_db.create_workflow(workflow)

        workflows = test_db.list_workflows()
        assert_that(len(workflows)).is_equal_to(len(test_workflows_list))

        # Verify workflow IDs are present
        workflow_ids = [wf.id for wf in workflows]
        expected_ids = [wf["id"] for wf in test_workflows_list]
        assert_that(set(workflow_ids)).is_equal_to(set(expected_ids))

    @pytest.mark.parametrize(
        "workflow_exists,expected_result", [(True, True), (False, False)]
    )
    def test_delete_workflow(
        self,
        populated_test_db,
        test_db,
        mock_workflow_data,
        workflow_exists,
        expected_result,
    ):
        """Test deleting workflow with existing and non-existent workflows"""
        if workflow_exists:
            db = populated_test_db
            workflow_id = mock_workflow_data["id"]
            # Verify workflow exists before deletion
            assert_that(db.get_workflow(workflow_id)).is_not_none()
        else:
            db = test_db
            workflow_id = "nonexistent_id"

        result = db.delete_workflow(workflow_id)
        assert_that(result).is_equal_to(expected_result)

        if workflow_exists:
            # Verify workflow is archived (soft delete)
            archived_workflow = db.get_workflow(workflow_id)
            assert_that(archived_workflow).is_not_none()
            assert_that(archived_workflow.status).is_equal_to("archived")


class TestConnectionManagement:
    """Test database connection management"""

    def test_connection_context_manager(self, test_db):
        """Test connection context manager works properly"""
        with test_db.get_connection() as conn:
            assert_that(conn).is_instance_of(sqlite3.Connection)
            assert_that(conn.row_factory).is_equal_to(sqlite3.Row)

            # Connection should be usable
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert_that(result[0]).is_equal_to(1)
