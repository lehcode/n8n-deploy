#!/usr/bin/env python3
"""
Unit tests for n8n_deploy_ API key management
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

from assertpy import assert_that

from api.api_keys import KeyApi, ApiKey


# === API Key Model Tests ===
class TestApiKey:
    """Test ApiKey dataclass functionality"""

    @pytest.mark.parametrize(
        "scenario,key_data,expected_attrs",
        [
            (
                "basic_creation",
                {
                    "id": 123,
                    "name": "test_key",
                    "plain_key": "plain_api_key_value",
                    "created_at": None,  # Will be set in test
                },
                {
                    "id": 123,
                    "name": "test_key",
                    "plain_key": "plain_api_key_value",
                    "is_active": True,
                    "description": None,
                },
            ),
            (
                "all_fields_creation",
                {
                    "id": 456,
                    "name": "full_test_key",
                    "plain_key": "full_plain_key_value",
                    "created_at": None,  # Will be set in test
                    "is_active": False,
                    "description": "Full test API key",
                },
                {
                    "id": 456,
                    "name": "full_test_key",
                    "is_active": False,
                    "description": "Full test API key",
                },
            ),
        ],
    )
    def test_api_key_creation_scenarios(self, scenario, key_data, expected_attrs):
        """Test creating API key with different field combinations"""
        created_time = datetime.now(timezone.utc)
        key_data["created_at"] = created_time

        key = ApiKey(**key_data)

        for attr_name, expected_value in expected_attrs.items():
            actual_value = getattr(key, attr_name)
            assert_that(actual_value).is_equal_to(expected_value)


# === API Key Manager Tests ===
class TestKeyApi:
    """Test KeyApi functionality"""

    def test_manager_initialization_with_config(self, test_config, test_db):
        """Test manager initialization with config"""
        manager = KeyApi(db=test_db, config=test_config)
        assert_that(manager.config).is_equal_to(test_config)
        assert_that(manager.db).is_not_none()

    def test_manager_initialization_without_config(self, test_db):
        """Test manager initialization without config"""
        manager = KeyApi(db=test_db)
        assert_that(manager.config).is_none()
        assert_that(manager.db).is_not_none()


# === Add API Key Tests ===
class TestAddApiKey:
    """Test API key addition functionality"""

    @pytest.mark.parametrize(
        "scenario,name,api_key,description",
        [
            (
                "with_description",
                "test_key",
                "test_api_key_12345",
                "Test API key",
            ),
            ("without_description", "test_key", "test_api_key_12345", None),
            ("basic_key", "test_n8n_key", "test_key_for_n8n", None),
        ],
    )
    def test_add_api_key_variations(
        self,
        test_api_key_manager,
        scenario,
        name,
        api_key,
        description,
    ):
        """Test adding API key with different optional parameters"""
        kwargs = {"name": name, "api_key": api_key}
        if description:
            kwargs["description"] = description

        key_id = test_api_key_manager.add_api_key(**kwargs)
        assert_that(key_id).is_not_none()

        retrieved_key = test_api_key_manager.get_api_key(name)
        assert_that(retrieved_key).is_equal_to(api_key)


# === Get API Key Tests ===
class TestGetApiKey:
    """Test API key retrieval functionality"""

    def test_get_api_key_existing(self, test_api_key_manager, test_api_key_data):
        """Test retrieving existing API key"""
        key_id = test_api_key_manager.add_api_key(
            name=test_api_key_data["name"],
            api_key=test_api_key_data["api_key"],
        )

        retrieved_key = test_api_key_manager.get_api_key(test_api_key_data["name"])

        assert_that(retrieved_key).is_not_none()
        assert_that(retrieved_key).is_instance_of(str)
        assert_that(retrieved_key).is_equal_to(test_api_key_data["api_key"])

    def test_get_api_key_nonexistent(self, test_api_key_manager):
        """Test retrieving non-existent API key returns None"""
        retrieved_key = test_api_key_manager.get_api_key("nonexistent_key_name")
        assert_that(retrieved_key).is_none()


# === API Key Lifecycle Tests ===
class TestApiKeyLifecycle:
    """Test API key lifecycle management"""

    def test_deactivate_api_key(self, test_api_key_manager, test_api_key_data):
        """Test deactivating an API key"""
        key_id = test_api_key_manager.add_api_key(
            name=test_api_key_data["name"],
            api_key=test_api_key_data["api_key"],
        )

        key = test_api_key_manager.get_api_key(test_api_key_data["name"])
        assert_that(key).is_not_none()

        # Deactivate key by name
        result = test_api_key_manager.deactivate_api_key(test_api_key_data["name"])
        assert_that(result).is_true()

        key = test_api_key_manager.get_api_key(test_api_key_data["name"])
        assert_that(key).is_none()

    def test_delete_api_key(self, test_api_key_manager, test_api_key_data):
        """Test deleting an API key"""
        key_id = test_api_key_manager.add_api_key(
            name=test_api_key_data["name"],
            api_key=test_api_key_data["api_key"],
        )

        assert_that(test_api_key_manager.get_api_key(test_api_key_data["name"])).is_not_none()

        result = test_api_key_manager.delete_api_key(test_api_key_data["name"], force=True)
        assert_that(result).is_true()

        assert_that(test_api_key_manager.get_api_key(test_api_key_data["name"])).is_none()
