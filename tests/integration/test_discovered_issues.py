#!/usr/bin/env python3
"""
Tests for Issues Discovered During End-to-End Testing Session

This file contains test stubs for specific issues that were identified and fixed
during the manual end-to-end testing session. These tests should be implemented
to prevent regression of the discovered issues.
"""

import os
from typing import Any, Dict

import pytest

from api.config import AppConfig

os.environ["N8N_DEPLOY_TESTING"] = "1"


@pytest.mark.integration
class TestDiscoveredNoneTypeErrors:
    """Test fixes for NoneType errors discovered during testing"""

    @pytest.mark.skip(reason="TODO: Implement test for workflow meta null handling")
    def test_workflow_sync_meta_none_error_fix(self, test_config: AppConfig) -> None:
        """
        Test fix for: 'NoneType' object has no attribute 'get'

        Issue: workflow_data.get("meta").get("description") failed when meta was None
        Fix: Changed to workflow_data.get("meta") or {} to handle null meta

        TODO: Implement test that:
        1. Mocks n8n API response with "meta": None
        2. Calls manager.sync_to_database()
        3. Verifies no NoneType error occurs
        4. Confirms description defaults to empty string
        5. Tests both null and missing meta scenarios
        """

        # TODO: Mock n8n API call and test sync_to_database
        pass

    @pytest.mark.skip(reason="TODO: Implement test for missing workflow fields handling")
    def test_workflow_sync_missing_fields_handling(self, test_config: AppConfig) -> None:
        """
        Test that workflow data handling (pull operations) handles missing or null fields gracefully

        Scenario: n8n API returns workflow with various missing optional fields
        Expected: Pull operation succeeds with appropriate defaults for missing fields

        TODO: Implement test with workflows missing:
        - meta field entirely
        - description within meta
        - versionId field
        - other optional fields
        """
        pass


@pytest.mark.integration
class TestDiscoveredDatabaseSchemaIssues:
    """Test fixes for database schema issues discovered during testing"""

    def test_workflow_creation_includes_counter_fields(self, test_config: AppConfig) -> None:
        """
        Test fix for: no such column: push_count

        Issue: Workflow model had push_count/pull_count but database schema didn't
        Fix: Added push_count and pull_count columns to workflows table
        """
        from datetime import datetime

        from api.db.core import DBApi
        from api.db.schema import SchemaApi
        from api.models import Workflow

        db = DBApi(config=test_config)
        schema = SchemaApi(config=test_config)
        schema.initialize_database()

        # Create workflow with counter fields
        wf = Workflow(
            id="test_counters",
            name="Test Workflow",
            file_path="test.json",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            push_count=0,
            pull_count=0,
        )

        # Add workflow - should not raise column error
        db.add_workflow(wf)

        # Retrieve and verify counters exist and are 0
        retrieved = db.get_workflow("test_counters")
        assert retrieved is not None
        assert retrieved.push_count == 0
        assert retrieved.pull_count == 0

    def test_push_pull_counter_increments(self, test_config: AppConfig) -> None:
        """
        Test that push/pull operations correctly increment database counters

        Scenario: Successful push/pull operations should increment respective counters
        Expected: Database counters increment and persist across operations
        """
        from datetime import datetime

        from api.db.core import DBApi
        from api.db.schema import SchemaApi
        from api.models import Workflow

        db = DBApi(config=test_config)
        schema = SchemaApi(config=test_config)
        schema.initialize_database()

        # Create workflow with initial counters at 0
        wf = Workflow(
            id="test_increment",
            name="Test Workflow",
            file_path="test.json",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            push_count=0,
            pull_count=0,
        )
        db.add_workflow(wf)

        # Increment push count
        result = db.increment_push_count("test_increment")
        assert result is True

        # Verify push_count incremented
        updated = db.get_workflow("test_increment")
        assert updated is not None
        assert updated.push_count == 1
        assert updated.pull_count == 0

        # Increment pull count
        result = db.increment_pull_count("test_increment")
        assert result is True

        # Verify pull_count incremented
        updated = db.get_workflow("test_increment")
        assert updated is not None
        assert updated.push_count == 1
        assert updated.pull_count == 1

        # Increment again to test multiple increments
        db.increment_push_count("test_increment")
        db.increment_pull_count("test_increment")

        final = db.get_workflow("test_increment")
        assert final is not None
        assert final.push_count == 2
        assert final.pull_count == 2


@pytest.mark.integration
class TestDiscoveredDependencyInjectionIssues:
    """Test fixes for dependency injection issues discovered during testing"""

    @pytest.mark.skip(reason="TODO: Implement test for single database instance")
    def test_api_key_manager_uses_shared_database_instance(self, test_config: AppConfig) -> None:
        """
        Test fix for: Remove duplicate 'Database initialized'

        Issue: KeyApi created its own DBApi instance
        Fix: Made KeyApi accept database instance from WorkflowApi

        TODO: Implement test that:
        1. Creates WorkflowApi which creates database
        2. Creates KeyApi with shared database instance
        3. Verifies only one database initialization occurs
        4. Confirms both managers use same database connection
        """

    @pytest.mark.skip(reason="TODO: Implement test for required database parameter")
    def test_api_key_manager_requires_database_parameter(self, test_config: AppConfig) -> None:
        """
        TODO: Implement test that:
        1. Attempts to create KeyApi without database parameter
        2. Verifies TypeError is raised for missing required parameter
        3. Confirms parameter ordering is correct (required before
           optional)
        """
        pass


@pytest.mark.integration
class TestDiscoveredHardcodedValueIssues:
    """Test fixes for hardcoded values discovered during testing"""

    @pytest.mark.skip(reason="TODO: Implement test for no hardcoded localhost URLs")
    def test_no_hardcoded_localhost_in_error_messages(self, test_config: AppConfig) -> None:
        """
        Test fix for: Remove any hardcoded values including localhost

        Issue: Error messages referenced hardcoded localhost:5678
        Fix: Removed hardcoded defaults, require explicit configuration

        TODO: Implement test that:
        1. Runs server commands without server URL configuration
        2. Captures error messages and output
        3. Verifies no "localhost" or "5678" in any messages
        4. Confirms generic configuration guidance provided
        """
        pass

    @pytest.mark.skip(reason="TODO: Implement test for server URL validation")
    def test_server_commands_require_explicit_configuration(self, test_config: AppConfig) -> None:
        """
        Test that server commands require explicit URL configuration

        Scenario: No N8N_SERVER_URL or --remote provided
        Expected: Clear error message directing user to configure server URL

        TODO: Implement test that:
        1. Ensures no server URL environment variables set
        2. Runs server, pull, push commands
        3. Verifies all fail with configuration error
        4. Confirms error messages are helpful and specific
        """
        pass

    @pytest.mark.skip(reason="TODO: Implement test for default value validation")
    def test_default_values_follow_type_conventions(self, test_config: AppConfig) -> None:
        """
        Test that default values follow conventions (empty string, 0, {}, [])

        Issue: Some defaults were inconsistent or hardcoded
        Fix: Standardized defaults based on type conventions

        TODO: Implement test that validates:
        - String fields default to "" (empty string)
        - Integer fields default to 0
        - Dict fields default to {}
        - List fields default to []
        - Optional fields default to None
        """
        pass


@pytest.mark.integration
class TestDiscoveredDisplayIssues:
    """Test fixes for display and formatting issues discovered during testing"""

    def test_list_displays_never_for_null_timestamps(self, test_config: AppConfig) -> None:
        """
        Test fix for: In last Synced replace None with Never

        Issue: List command showed "None" for null last_used/last_synced timestamps
        Fix: Display "Never" in human-readable format
        """
        import subprocess
        from datetime import datetime

        from api.db.core import DBApi
        from api.db.schema import SchemaApi
        from api.models import Workflow

        db = DBApi(config=test_config)
        schema = SchemaApi(config=test_config)
        schema.initialize_database()

        # Create workflow with null last_used
        wf = Workflow(
            id="test_never",
            name="Test Never Display",
            file_path="test.json",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_used=None,  # Explicitly null
        )
        db.add_workflow(wf)

        # Run list command - check for "Never" display
        # Use environment variable to set database path
        import os

        env = os.environ.copy()
        env["N8N_DEPLOY_DATA_DIR"] = str(test_config.base_folder)

        result = subprocess.run(
            ["./n8n-deploy", "wf", "list"],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

        assert result.returncode == 0
        output = result.stdout + result.stderr

        # Should show "Never" for null last_used (not "None")
        assert "Never" in output

    @pytest.mark.skip(reason="TODO: Implement test for environment variable display")
    def test_list_command_shows_environment_info(self, test_config: AppConfig) -> None:
        """
        Test feature: Add N8N_DEPLOY_DATA and N8N_DEPLOY_FLOWS to list command

        Feature: Show environment variable configuration in list command
        Implementation: Display both actual paths and env var values

        TODO: Implement test that:
        1. Sets environment variables N8N_DEPLOY_DATA and N8N_DEPLOY_FLOWS
        2. Runs list command
        3. Verifies output includes directory paths
        4. Confirms environment variable values displayed
        5. Tests both set and unset environment scenarios
        """
        pass

    @pytest.mark.skip(reason="TODO: Implement test for file existence accuracy")
    def test_file_exists_column_accuracy(self, test_config: AppConfig) -> None:
        """
        Test issue: File exist column shows wrong values

        Issue: File existence detection not accurately reflecting filesystem
        Status: Deferred by user ("We'll manage this edge case later")

        TODO: Implement test that:
        1. Creates workflows with various file_path configurations
        2. Creates some actual files, leaves others missing
        3. Runs list command
        4. Verifies File Exists column matches actual filesystem state
        5. Tests path resolution edge cases
        """
        pass


@pytest.mark.integration
class TestDiscoveredConfigurationIssues:
    """Test fixes for configuration issues discovered during testing"""

    @pytest.mark.skip(reason="TODO: Implement test for server URL priority")
    def test_server_url_configuration_priority_order(self, test_config: AppConfig) -> None:
        """
        Test server URL configuration priority: CLI flag > environment variable

        Scenario: Both --remote and N8N_SERVER_URL are configured
        Expected: CLI flag takes precedence over environment variable

        TODO: Implement test that:
        1. Sets N8N_SERVER_URL environment variable
        2. Uses --remote CLI flag with different URL
        3. Mocks server request to capture which URL is used
        4. Verifies CLI flag URL is used, not environment URL
        """
        pass

    @pytest.mark.skip(reason="TODO: Implement test for API key integration")
    def test_server_commands_integrate_with_api_keys(self, test_config: AppConfig) -> None:
        """
        Test that server commands automatically use stored API keys

        Scenario: API key stored in database, server URL configured
        Expected: Server requests include API key from database

        TODO: Implement test that:
        1. Stores API key using apikey add command
        2. Configures server URL
        3. Mocks server response with authentication check
        4. Runs server command (server, pull, push)
        5. Verifies API key included in request headers
        """
        pass


# Utility functions for discovered issue tests
def create_problematic_workflow_data() -> Dict[str, Any]:
    """
    Create workflow data that reproduces discovered issues

    Returns workflow data with null meta field and other problematic values
    that were encountered during end-to-end testing session
    """
    return {
        "id": "problematic_workflow",
        "name": "Problematic Test Workflow",
        "meta": None,  # This caused NoneType errors
        "active": True,
        "nodes": [],
        "connections": {},
        # Missing optional fields that should have defaults
        "versionId": None,
        "createdAt": None,
        "updatedAt": None,
    }


def simulate_database_schema_evolution() -> Dict[str, Any]:
    """
    Simulate database schema changes that occurred during testing

    TODO: Implement function that:
    - Creates database with old schema (missing push_count/pull_count)
    - Attempts operations that require new columns
    - Verifies graceful handling or proper migration
    """
    return {"schema_version": 1, "columns_added": ["push_count", "pull_count"]}


def verify_no_hardcoded_values_in_output(output: str) -> bool:
    """
    Verify that output contains no hardcoded values

    Checks for hardcoded localhost URLs, ports, or other values
    that should be configurable
    """
    hardcoded_patterns = [
        "localhost",
        ":5678",
        "127.0.0.1",
    ]

    for pattern in hardcoded_patterns:
        if pattern.lower() in output.lower():
            return False

    return True
