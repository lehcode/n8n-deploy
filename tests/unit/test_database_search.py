#!/usr/bin/env python3
"""
Unit tests for enhanced search functionality in database core operations.

Tests the dual search capability that searches both user-friendly names and n8n wf IDs.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pytest

from api.config import AppConfig
from api.db.core import DBApi
from api.models import Workflow, WorkflowStatus


class TestDatabaseSearch:
    """Test enhanced search functionality for workflows"""

    @pytest.fixture
    def temp_db(self, tmp_path: Path) -> DBApi:
        """Create a temporary database for testing"""
        db_path = tmp_path / "test_search.db"
        config = AppConfig(base_folder=tmp_path, flow_folder=tmp_path)
        db = DBApi(config=config, db_path=db_path)
        db.schema_api.initialize_database()
        return db

    @pytest.fixture
    def sample_workflows(self, temp_db: DBApi) -> List[Workflow]:
        """Create sample workflows with diverse IDs and names for testing"""
        workflows = [
            # Test workflows with n8n-style IDs
            Workflow(id="deAVBp391wvomsWY", name="signup-flow", status=WorkflowStatus.ACTIVE),  # Exact match test case
            Workflow(id="deAVKx892pqotuXZ", name="login-process", status=WorkflowStatus.ACTIVE),
            Workflow(id="xYz123AbC456DeF", name="email-notification-flow", status=WorkflowStatus.ACTIVE),  # Contains "flow"
            Workflow(id="mNoPqR789StUvWx", name="user-management-system", status=WorkflowStatus.ACTIVE),
            Workflow(id="flow_test_987654", name="data-processing-pipeline", status=WorkflowStatus.ACTIVE),
            # Edge case: ID that contains common search terms
            Workflow(id="flow_in_id_test", name="backup-system", status=WorkflowStatus.INACTIVE),
        ]

        # Insert all workflows into database
        for wf in workflows:
            temp_db.add_workflow(wf)

        return workflows

    def test_search_by_exact_n8n_workflow_id(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test searching by exact n8n wf ID"""
        # Test exact ID match
        results = temp_db.search_workflows("deAVBp391wvomsWY")

        assert len(results) == 1
        assert results[0].id == "deAVBp391wvomsWY"
        assert results[0].name == "signup-flow"

    def test_search_by_partial_n8n_workflow_id(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test searching by partial n8n wf ID"""
        # Test partial ID match - should find workflows with IDs starting with "deAV"
        results = temp_db.search_workflows("deAV")

        assert len(results) == 2
        workflow_ids = [w.id for w in results]
        assert "deAVBp391wvomsWY" in workflow_ids
        assert "deAVKx892pqotuXZ" in workflow_ids

    def test_search_by_exact_workflow_name(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test searching by exact wf name"""
        # Test exact name match
        results = temp_db.search_workflows("signup-flow")

        assert len(results) == 1
        assert results[0].name == "signup-flow"
        assert results[0].id == "deAVBp391wvomsWY"

    def test_search_by_partial_workflow_name(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test searching by partial wf name"""
        # Test partial name match - should find workflows with names containing "flow"
        results = temp_db.search_workflows("flow")

        assert len(results) >= 2  # At least signup-flow and email-notification-flow
        workflow_names = [w.name for w in results]
        assert "signup-flow" in workflow_names
        assert "email-notification-flow" in workflow_names

    def test_search_with_mixed_results(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search that returns results from both ID and name matches"""
        # Search for "flow" - should match:
        # - IDs containing "flow": flow_test_987654, flow_in_id_test
        # - Names containing "flow": signup-flow, email-notification-flow
        results = temp_db.search_workflows("flow")

        assert len(results) >= 4

        # Verify we get both ID matches and name matches
        ids_with_flow = [w.id for w in results if "flow" in w.id]
        names_with_flow = [w.name for w in results if "flow" in w.name]

        assert len(ids_with_flow) >= 2  # flow_test_987654, flow_in_id_test
        assert len(names_with_flow) >= 2  # signup-flow, email-notification-flow

    def test_search_result_ordering(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test that search results are properly ordered (exact matches first)"""
        # Search for "signup-flow" - should prioritize exact name match
        results = temp_db.search_workflows("signup-flow")

        # First result should be exact name match
        assert results[0].name == "signup-flow"

        # Test exact ID match prioritization
        results = temp_db.search_workflows("deAVBp391wvomsWY")
        assert results[0].id == "deAVBp391wvomsWY"

    def test_search_case_sensitivity(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test case sensitivity in search functionality"""
        # Test lowercase search for uppercase content
        results_lower = temp_db.search_workflows("signup")
        results_mixed = temp_db.search_workflows("SignUp")

        # Should find signup-flow regardless of case in search term
        # Note: SQLite LIKE is case-insensitive by default for ASCII characters
        assert len(results_lower) >= 1
        assert any("signup" in w.name.lower() for w in results_lower)

    def test_search_no_results(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search with no matching results"""
        results = temp_db.search_workflows("nonexistent_workflow_12345")

        assert len(results) == 0

    def test_search_empty_query(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search with empty query"""
        results = temp_db.search_workflows("")

        # Empty search should return all workflows
        assert len(results) == len(sample_workflows)

    def test_search_whitespace_query(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search with whitespace-only query"""
        results = temp_db.search_workflows("   ")

        # Whitespace-only search with no matches (none of our sample workflows contain multiple spaces)
        assert len(results) == 0

    def test_search_special_characters(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search with special characters"""
        # Search for hyphen (common in wf names)
        results = temp_db.search_workflows("-")

        # Should find workflows with hyphens in names
        hyphenated_workflows = [w for w in results if "-" in w.name]
        assert len(hyphenated_workflows) >= 4  # Most sample workflows have hyphens

    def test_search_underscore_patterns(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search with underscore patterns"""
        # Search for underscore (common in wf IDs)
        results = temp_db.search_workflows("_")

        # Should find workflows with underscores in IDs or names
        underscore_workflows = [w for w in results if "_" in w.id or "_" in w.name]
        assert len(underscore_workflows) >= 2  # flow_test_987654, flow_in_id_test

    def test_search_partial_id_prefix(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test searching by ID prefix"""
        # Search for workflows starting with specific characters
        results = temp_db.search_workflows("xYz")

        assert len(results) == 1
        assert results[0].id == "xYz123AbC456DeF"
        assert results[0].name == "email-notification-flow"

    def test_search_partial_id_suffix(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test searching by ID suffix"""
        # Search for workflows ending with specific characters
        results = temp_db.search_workflows("654")

        assert len(results) == 1
        assert results[0].id == "flow_test_987654"
        assert results[0].name == "data-processing-pipeline"

    def test_search_workflow_status_independence(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test that search works across all wf statuses"""
        # Search should find workflows regardless of status
        results = temp_db.search_workflows("system")

        # Should find both user-management-system (ACTIVE) and backup-system (INACTIVE)
        assert len(results) >= 2
        statuses = [w.status for w in results]
        assert WorkflowStatus.ACTIVE in statuses
        assert WorkflowStatus.INACTIVE in statuses

    def test_search_with_sql_injection_prevention(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test that search handles potential SQL injection attempts safely"""
        # Test various SQL injection patterns
        injection_attempts = [
            "'; DROP TABLE workflows; --",
            "' OR '1'='1",
            "'; SELECT * FROM workflows; --",
            "%'; UNION SELECT * FROM api_keys; --",
        ]

        for injection in injection_attempts:
            # Should not raise an exception and should return safe results
            results = temp_db.search_workflows(injection)
            # Results should be empty or contain legitimate matches only
            assert isinstance(results, list)
            for wf in results:
                assert isinstance(wf, Workflow)

    def test_search_unicode_characters(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search with unicode characters"""
        # Create a wf with unicode characters
        unicode_workflow = Workflow(id="unicode_test_123", name="测试-wf-with-émojis-🚀", status=WorkflowStatus.ACTIVE)
        temp_db.add_workflow(unicode_workflow)

        # Search for unicode content
        results = temp_db.search_workflows("测试")
        assert len(results) == 1
        assert results[0].name == "测试-wf-with-émojis-🚀"

        # Search for emoji
        results = temp_db.search_workflows("🚀")
        assert len(results) == 1
        assert results[0].name == "测试-wf-with-émojis-🚀"

    def test_search_very_long_query(self, temp_db: DBApi, sample_workflows: List[Workflow]):
        """Test search with very long query strings"""
        # Test with a very long search query
        long_query = "a" * 1000
        results = temp_db.search_workflows(long_query)

        # Should handle gracefully without errors
        assert isinstance(results, list)
        assert len(results) == 0  # No matches expected

    def test_search_performance_with_multiple_results(self, temp_db: DBApi):
        """Test search performance with many workflows"""
        # Create many workflows for performance testing
        workflows = []
        for i in range(100):
            wf = Workflow(id=f"perf_test_{i:03d}_{i*2:03d}", name=f"performance-test-wf-{i}", status=WorkflowStatus.ACTIVE)
            workflows.append(wf)
            temp_db.add_workflow(wf)

        # Search that should match many results
        results = temp_db.search_workflows("perf")
        assert len(results) == 100

        # Search that should match fewer results
        results = temp_db.search_workflows("010")
        assert len(results) >= 1  # At least perf_test_010_020


class TestGetWorkflowByNameOrId:
    """Test get_workflow_by_name_or_id with various lookup strategies"""

    @pytest.fixture
    def temp_db(self, tmp_path: Path) -> DBApi:
        """Create a temporary database for testing"""
        db_path = tmp_path / "test_lookup.db"
        config = AppConfig(base_folder=tmp_path, flow_folder=tmp_path)
        db = DBApi(config=config, db_path=db_path)
        db.schema_api.initialize_database()
        return db

    @pytest.fixture
    def workflows_with_paths(self, temp_db: DBApi) -> List[Workflow]:
        """Create workflows with different file path patterns"""
        workflows = [
            # Simple filename
            Workflow(
                id="wf001",
                name="simple-workflow",
                file="simple-workflow.json",
                status=WorkflowStatus.ACTIVE,
            ),
            # Filename with subdirectory path
            Workflow(
                id="wf002",
                name="nested-workflow",
                file="subdir/nested-workflow.json",
                status=WorkflowStatus.ACTIVE,
            ),
            # Filename with deep path
            Workflow(
                id="wf003",
                name="deep-workflow",
                file="n8n-workflows/research/deep-workflow.json",
                status=WorkflowStatus.ACTIVE,
            ),
            # Workflow without file
            Workflow(
                id="wf004",
                name="no-file-workflow",
                file=None,
                status=WorkflowStatus.ACTIVE,
            ),
        ]

        for wf in workflows:
            temp_db.add_workflow(wf)

        return workflows

    def test_lookup_by_id(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test lookup by workflow ID"""
        result = temp_db.get_workflow_by_name_or_id("wf001")
        assert result is not None
        assert result.id == "wf001"
        assert result.name == "simple-workflow"

    def test_lookup_by_name(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test lookup by workflow name"""
        result = temp_db.get_workflow_by_name_or_id("nested-workflow")
        assert result is not None
        assert result.id == "wf002"
        assert result.name == "nested-workflow"

    def test_lookup_by_exact_filename(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test lookup by exact filename (simple case)"""
        result = temp_db.get_workflow_by_name_or_id("simple-workflow.json")
        assert result is not None
        assert result.id == "wf001"

    def test_lookup_by_exact_path(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test lookup by exact file path"""
        result = temp_db.get_workflow_by_name_or_id("subdir/nested-workflow.json")
        assert result is not None
        assert result.id == "wf002"

    def test_lookup_by_basename_from_path(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test lookup by basename when file is stored with path (ND-50 fix)"""
        # User provides just filename, but database has path
        result = temp_db.get_workflow_by_name_or_id("nested-workflow.json")
        assert result is not None
        assert result.id == "wf002"
        assert result.file == "subdir/nested-workflow.json"

    def test_lookup_by_basename_from_deep_path(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test lookup by basename from deep nested path (ND-50 fix)"""
        # User provides just filename, but database has deep path
        result = temp_db.get_workflow_by_name_or_id("deep-workflow.json")
        assert result is not None
        assert result.id == "wf003"
        assert result.file == "n8n-workflows/research/deep-workflow.json"

    def test_lookup_nonexistent(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test lookup for non-existent workflow"""
        result = temp_db.get_workflow_by_name_or_id("does-not-exist.json")
        assert result is None

    def test_lookup_priority_id_over_name(self, temp_db: DBApi, workflows_with_paths: List[Workflow]):
        """Test that ID lookup takes priority over name"""
        # Add workflow where name matches another workflow's ID pattern
        conflict_wf = Workflow(
            id="conflict-id",
            name="wf001",  # Name matches existing workflow's ID
            file="conflict.json",
            status=WorkflowStatus.ACTIVE,
        )
        temp_db.add_workflow(conflict_wf)

        # Should find by ID first
        result = temp_db.get_workflow_by_name_or_id("wf001")
        assert result is not None
        assert result.id == "wf001"  # Got the one with matching ID, not name
