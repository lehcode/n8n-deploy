#!/usr/bin/env python3
"""
Unit tests for n8n_deploy_ API key management
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

from assertpy import assert_that

from api.api_keys import ApiKeyManager, ApiKey


class TestApiKey:
    """Test ApiKey dataclass functionality"""

    @pytest.mark.parametrize(
        "scenario,key_data,expected_attrs",
        [
            (
                "basic_creation",
                {
                    "id": "test_key_123",
                    "name": "test_key",
                    "plain_key": "plain_api_key_value",
                    "created_at": None,  # Will be set in test
                },
                {
                    "id": "test_key_123",
                    "name": "test_key",
                    "plain_key": "plain_api_key_value",
                    "is_active": True,
                    "last_used": None,
                    "expires_at": None,
                    "description": None,
                },
            ),
            (
                "all_fields_creation",
                {
                    "id": "full_key_456",
                    "name": "full_test_key",
                    "plain_key": "full_plain_key_value",
                    "created_at": None,  # Will be set in test
                    "last_used": "offset_hours_1",  # Will be calculated
                    "expires_at": "offset_days_30",  # Will be calculated
                    "is_active": False,
                    "description": "Full test API key",
                },
                {
                    "id": "full_key_456",
                    "name": "full_test_key",
                    "is_active": False,
                    "description": "Full test API key",
                },
            ),
        ],
    )
    def test_api_key_creation_scenarios(self, scenario, key_data, expected_attrs):
        """Test creating API key with different field combinations"""
        # Setup timestamps
        created_time = datetime.now(timezone.utc)
        key_data["created_at"] = created_time

        # Handle special timestamp fields
        if key_data.get("last_used") == "offset_hours_1":
            key_data["last_used"] = created_time + timedelta(hours=1)
        if key_data.get("expires_at") == "offset_days_30":
            key_data["expires_at"] = created_time + timedelta(days=30)

        # Create key
        key = ApiKey(**key_data)

        # Verify expected attributes
        for attr_name, expected_value in expected_attrs.items():
            actual_value = getattr(key, attr_name)
            assert_that(actual_value).is_equal_to(expected_value)

        # Scenario-specific checks
        if scenario == "all_fields_creation":
            assert_that(key.last_used).is_equal_to(key_data["last_used"])
            assert_that(key.expires_at).is_equal_to(key_data["expires_at"])


class TestApiKeyManager:
    """Test ApiKeyManager functionality"""

    def test_manager_initialization_with_config(self, test_config):
        """Test manager initialization with config"""
        manager = ApiKeyManager(config=test_config)
        assert_that(manager.config).is_equal_to(test_config)
        assert_that(manager.db).is_not_none()

    def test_manager_initialization_without_config(self):
        """Test manager initialization without config"""
        manager = ApiKeyManager()
        assert_that(manager.config).is_none()
        assert_that(manager.db).is_not_none()


class TestAddApiKey:
    """Test API key addition functionality"""

    @pytest.mark.parametrize(
        "scenario,name,api_key,description,expires_days",
        [
            (
                "with_description",
                "test_key",
                "test_api_key_12345",
                "Test API key",
                None,
            ),
            ("with_expiration", "test_key", "test_api_key_12345", None, 30),
            ("basic_key", "test_n8n_key", "test_key_for_n8n", None, None),
        ],
    )
    def test_add_api_key_variations(
        self,
        test_api_key_manager,
        scenario,
        name,
        api_key,
        description,
        expires_days,
    ):
        """Test adding API key with different optional parameters"""
        kwargs = {"name": name, "api_key": api_key}
        if description:
            kwargs["description"] = description
        if expires_days:
            kwargs["expires_days"] = expires_days

        key_id = test_api_key_manager.add_api_key(**kwargs)
        assert_that(key_id).is_not_none()

        retrieved_key = test_api_key_manager.get_api_key(key_id)
        assert_that(retrieved_key).is_equal_to(api_key)


class TestGetApiKey:
    """Test API key retrieval functionality"""

    def test_get_api_key_existing(self, test_api_key_manager, test_api_key_data):
        """Test retrieving existing API key"""
        # Add key first
        key_id = test_api_key_manager.add_api_key(
            name=test_api_key_data["name"],
            api_key=test_api_key_data["api_key"],
        )

        # Retrieve key (returns key string)
        retrieved_key = test_api_key_manager.get_api_key(key_id)

        assert_that(retrieved_key).is_not_none()
        assert_that(retrieved_key).is_instance_of(str)
        assert_that(retrieved_key).is_equal_to(test_api_key_data["api_key"])

    def test_get_api_key_nonexistent(self, test_api_key_manager):
        """Test retrieving non-existent API key returns None"""
        retrieved_key = test_api_key_manager.get_api_key("nonexistent_key_id")
        assert_that(retrieved_key).is_none()


class TestApiKeyLifecycle:
    """Test API key lifecycle management"""

    def test_deactivate_api_key(self, test_api_key_manager, test_api_key_data):
        """Test deactivating an API key"""
        # Add key
        key_id = test_api_key_manager.add_api_key(
            name=test_api_key_data["name"],
            api_key=test_api_key_data["api_key"],
        )

        # Verify key is accessible
        key = test_api_key_manager.get_api_key(key_id)
        assert_that(key).is_not_none()

        # Deactivate key
        result = test_api_key_manager.deactivate_api_key(key_id)
        assert_that(result).is_true()

        # Verify key is no longer accessible (deactivated keys return None)
        key = test_api_key_manager.get_api_key(key_id)
        assert_that(key).is_none()

    def test_delete_api_key(self, test_api_key_manager, test_api_key_data):
        """Test deleting an API key"""
        # Add key
        key_id = test_api_key_manager.add_api_key(
            name=test_api_key_data["name"],
            api_key=test_api_key_data["api_key"],
        )

        # Verify key exists
        assert_that(test_api_key_manager.get_api_key(key_id)).is_not_none()

        # Delete key (requires confirm=True)
        result = test_api_key_manager.delete_api_key(key_id, confirm=True)
        assert_that(result).is_true()

        # Verify key is deleted
        assert_that(test_api_key_manager.get_api_key(key_id)).is_none()
