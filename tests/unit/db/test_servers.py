#!/usr/bin/env python3
"""
Unit tests for ServerCrud database operations
"""

import pytest
from assertpy import assert_that
from pathlib import Path
from typing import Dict, Any

from api.config import AppConfig
from api.db.servers import ServerCrud


@pytest.fixture
def server_api(temp_dir: Path) -> ServerCrud:
    """Create ServerCrud instance with test database"""
    config = AppConfig(base_folder=temp_dir)
    api = ServerCrud(config=config)
    # Initialize database with schema
    with api.get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                name TEXT NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                skip_ssl_verify BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_key TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS server_api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                api_key_id INTEGER NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers (id) ON DELETE CASCADE,
                FOREIGN KEY (api_key_id) REFERENCES api_keys (id) ON DELETE CASCADE,
                UNIQUE (server_id, api_key_id)
            )
            """
        )
        conn.commit()
    return api


class TestServerCRUD:
    """Test server CRUD operations"""

    def test_add_server_basic(self, server_api: ServerCrud) -> None:
        """Test adding a basic server"""
        server_id = server_api.add_server(url="http://localhost:5678", name="test_server")

        assert_that(server_id).is_greater_than(0)

        # Verify server was added
        server = server_api.get_server_by_name("test_server")
        assert_that(server).is_not_none()
        assert_that(server["url"]).is_equal_to("http://localhost:5678")
        assert_that(server["name"]).is_equal_to("test_server")
        assert_that(server["is_active"]).is_true()

    def test_add_server_duplicate_name(self, server_api: ServerCrud) -> None:
        """Test adding server with duplicate name fails"""
        server_api.add_server(url="http://localhost:5678", name="duplicate")

        with pytest.raises(Exception):  # Should raise UNIQUE constraint error
            server_api.add_server(url="http://other:5678", name="duplicate")

    def test_get_server_by_name(self, server_api: ServerCrud) -> None:
        """Test retrieving server by name"""
        server_api.add_server(
            url="http://localhost:5678",
            name="lookup_test",
        )

        server = server_api.get_server_by_name("lookup_test")
        assert_that(server).is_not_none()
        assert_that(server["name"]).is_equal_to("lookup_test")

        # Test non-existent server
        missing = server_api.get_server_by_name("nonexistent")
        assert_that(missing).is_none()

    def test_get_server_by_url(self, server_api: ServerCrud) -> None:
        """Test retrieving server by URL"""
        server_api.add_server(
            url="http://specific:5678",
            name="url_test",
        )

        server = server_api.get_server_by_url("http://specific:5678")
        assert_that(server).is_not_none()
        assert_that(server["url"]).is_equal_to("http://specific:5678")

    def test_list_servers_empty(self, server_api: ServerCrud) -> None:
        """Test listing servers when none exist"""
        servers = server_api.list_servers()
        assert_that(servers).is_empty()

    def test_list_servers_multiple(self, server_api: ServerCrud) -> None:
        """Test listing multiple servers"""
        server_api.add_server(url="http://server1:5678", name="server1")
        server_api.add_server(url="http://server2:5678", name="server2")
        server_api.add_server(url="http://server3:5678", name="server3")

        servers = server_api.list_servers()
        assert_that(servers).is_length(3)
        names = [s["name"] for s in servers]
        assert_that(names).contains("server1", "server2", "server3")

    def test_list_servers_active_only(self, server_api: ServerCrud) -> None:
        """Test filtering servers by active status"""
        server_api.add_server(url="http://active:5678", name="active", is_active=True)
        server_api.add_server(url="http://inactive:5678", name="inactive", is_active=False)

        all_servers = server_api.list_servers(active_only=False)
        assert_that(all_servers).is_length(2)

        active_servers = server_api.list_servers(active_only=True)
        assert_that(active_servers).is_length(1)
        assert_that(active_servers[0]["name"]).is_equal_to("active")

    def test_update_server(self, server_api: ServerCrud) -> None:
        """Test updating server properties"""
        server_api.add_server(url="http://old:5678", name="update_test")

        success = server_api.update_server(name="update_test", url="http://new:5678", is_active=False)

        assert_that(success).is_true()

        server = server_api.get_server_by_name("update_test")
        assert_that(server["url"]).is_equal_to("http://new:5678")
        assert_that(server["is_active"]).is_false()

    def test_delete_server(self, server_api: ServerCrud) -> None:
        """Test deleting a server"""
        server_api.add_server(url="http://delete:5678", name="delete_test")

        success = server_api.delete_server("delete_test")
        assert_that(success).is_true()

        # Verify deletion
        server = server_api.get_server_by_name("delete_test")
        assert_that(server).is_none()

        # Test deleting non-existent server
        success = server_api.delete_server("nonexistent")
        assert_that(success).is_false()


class TestServerApiKeyLinking:
    """Test server-API key association operations"""

    def test_link_api_key_to_server(self, server_api: ServerCrud) -> None:
        """Test linking an API key to a server"""
        # Create server
        server_api.add_server(url="http://localhost:5678", name="test_server")

        # Create API key
        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("test_key", "eyJhbGci.test.signature"))
            conn.commit()

        # Link them
        server_api.link_api_key("test_server", "test_key")

        # Verify link
        keys = server_api.get_server_api_keys("test_server")
        assert_that(keys).is_length(1)
        assert_that(keys[0]["name"]).is_equal_to("test_key")

    def test_link_api_key_duplicate(self, server_api: ServerCrud) -> None:
        """Test linking same API key twice fails gracefully"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("test_key", "eyJhbGci.test.signature"))
            conn.commit()

        server_api.link_api_key("test_server", "test_key")

        # Second link should fail
        with pytest.raises(Exception):  # UNIQUE constraint
            server_api.link_api_key("test_server", "test_key")

    def test_unlink_api_key_from_server(self, server_api: ServerCrud) -> None:
        """Test unlinking an API key from a server"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("test_key", "eyJhbGci.test.signature"))
            conn.commit()

        server_api.link_api_key("test_server", "test_key")

        # Unlink
        success = server_api.unlink_api_key("test_server", "test_key")
        assert_that(success).is_true()

        # Verify unlinked
        keys = server_api.get_server_api_keys("test_server")
        assert_that(keys).is_empty()

    def test_get_api_key_for_server(self, server_api: ServerCrud) -> None:
        """Test retrieving API key value for a server"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        test_key_value = "eyJhbGci.test.signature"
        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("test_key", test_key_value))
            conn.commit()

        server_api.link_api_key("test_server", "test_key")

        # Get the key
        key = server_api.get_api_key_for_server("test_server")
        assert_that(key).is_equal_to(test_key_value)

        # Verify last_used was updated
        server = server_api.get_server_by_name("test_server")
        assert_that(server["last_used"]).is_not_none()

    def test_get_server_api_keys_empty(self, server_api: ServerCrud) -> None:
        """Test getting API keys for server with no keys linked"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        keys = server_api.get_server_api_keys("test_server")
        assert_that(keys).is_empty()


class TestServerEdgeCases:
    """Test edge cases and error handling"""

    def test_add_server_minimal(self, server_api: ServerCrud) -> None:
        """Test adding server with only required fields"""
        server_id = server_api.add_server(url="http://minimal:5678", name="minimal")

        assert_that(server_id).is_greater_than(0)
        server = server_api.get_server_by_name("minimal")
        assert_that(server["is_active"]).is_true()

    def test_update_server_nonexistent(self, server_api: ServerCrud) -> None:
        """Test updating non-existent server returns False"""
        success = server_api.update_server(name="nonexistent", url="http://new:5678")
        assert_that(success).is_false()

    def test_update_server_no_changes(self, server_api: ServerCrud) -> None:
        """Test updating server with no changes"""
        server_api.add_server(url="http://test:5678", name="test")

        # Update with no actual changes
        success = server_api.update_server(name="test")
        assert_that(success).is_true()


class TestPrimaryApiKeySelection:
    """Test primary API key selection feature"""

    def test_set_primary_api_key(self, server_api: ServerCrud) -> None:
        """Test setting a primary API key for a server"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        # Create two API keys
        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key1", "value1"))
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key2", "value2"))
            conn.commit()

        # Link both keys
        server_api.link_api_key("test_server", "key1")
        server_api.link_api_key("test_server", "key2")

        # Set key1 as primary
        success = server_api.set_primary_api_key("test_server", "key1")
        assert_that(success).is_true()

        # Verify key1 is primary
        primary = server_api.get_primary_api_key_name("test_server")
        assert_that(primary).is_equal_to("key1")

    def test_set_primary_api_key_overrides_previous(self, server_api: ServerCrud) -> None:
        """Test that setting a new primary key clears the previous primary"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key1", "value1"))
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key2", "value2"))
            conn.commit()

        server_api.link_api_key("test_server", "key1")
        server_api.link_api_key("test_server", "key2")

        # Set key1 as primary first
        server_api.set_primary_api_key("test_server", "key1")
        assert_that(server_api.get_primary_api_key_name("test_server")).is_equal_to("key1")

        # Now set key2 as primary
        server_api.set_primary_api_key("test_server", "key2")
        assert_that(server_api.get_primary_api_key_name("test_server")).is_equal_to("key2")

    def test_set_primary_api_key_not_linked(self, server_api: ServerCrud) -> None:
        """Test setting primary for unlinked key returns False"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("unlinked_key", "value"))
            conn.commit()

        # Try to set as primary without linking
        success = server_api.set_primary_api_key("test_server", "unlinked_key")
        assert_that(success).is_false()

    def test_set_primary_api_key_nonexistent_server(self, server_api: ServerCrud) -> None:
        """Test setting primary for non-existent server returns False"""
        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key1", "value1"))
            conn.commit()

        success = server_api.set_primary_api_key("nonexistent", "key1")
        assert_that(success).is_false()

    def test_get_api_key_for_server_prioritizes_primary(self, server_api: ServerCrud) -> None:
        """Test that primary key is returned even when linked after others"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key1", "first_value"))
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key2", "primary_value"))
            conn.commit()

        # Link key1 first, then key2
        server_api.link_api_key("test_server", "key1")
        server_api.link_api_key("test_server", "key2")

        # Set key2 as primary
        server_api.set_primary_api_key("test_server", "key2")

        # Should return key2 (primary) not key1 (most recent)
        key = server_api.get_api_key_for_server("test_server")
        assert_that(key).is_equal_to("primary_value")

    def test_get_api_key_for_server_falls_back_to_recent(self, server_api: ServerCrud) -> None:
        """Test that most recent key is returned when no primary is set"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key1", "first_value"))
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key2", "second_value"))
            conn.commit()

        server_api.link_api_key("test_server", "key1")
        server_api.link_api_key("test_server", "key2")

        # No primary set - should return most recently linked (key2)
        key = server_api.get_api_key_for_server("test_server")
        assert_that(key).is_equal_to("second_value")

    def test_get_api_key_for_server_ignores_inactive(self, server_api: ServerCrud) -> None:
        """Test that inactive API keys are not returned"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute(
                "INSERT INTO api_keys (name, api_key, is_active) VALUES (?, ?, ?)", ("inactive", "inactive_value", False)
            )
            conn.execute("INSERT INTO api_keys (name, api_key, is_active) VALUES (?, ?, ?)", ("active", "active_value", True))
            conn.commit()

        server_api.link_api_key("test_server", "inactive")
        server_api.link_api_key("test_server", "active")

        # Set inactive as primary
        server_api.set_primary_api_key("test_server", "inactive")

        # Should return active key since inactive is filtered out
        key = server_api.get_api_key_for_server("test_server")
        assert_that(key).is_equal_to("active_value")

    def test_get_server_api_keys_includes_primary_flag(self, server_api: ServerCrud) -> None:
        """Test that get_server_api_keys returns is_primary field"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key1", "value1"))
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key2", "value2"))
            conn.commit()

        server_api.link_api_key("test_server", "key1")
        server_api.link_api_key("test_server", "key2")
        server_api.set_primary_api_key("test_server", "key1")

        keys = server_api.get_server_api_keys("test_server")
        assert_that(keys).is_length(2)

        # Find key1 and key2 in results
        key1_data = next((k for k in keys if k["name"] == "key1"), None)
        key2_data = next((k for k in keys if k["name"] == "key2"), None)

        assert_that(key1_data).is_not_none()
        assert_that(key2_data).is_not_none()
        assert_that(key1_data["is_primary"]).is_true()
        assert_that(key2_data["is_primary"]).is_false()

    def test_get_primary_api_key_name_no_primary(self, server_api: ServerCrud) -> None:
        """Test getting primary key name when none is set"""
        server_api.add_server(url="http://localhost:5678", name="test_server")

        with server_api.get_connection() as conn:
            conn.execute("INSERT INTO api_keys (name, api_key) VALUES (?, ?)", ("key1", "value1"))
            conn.commit()

        server_api.link_api_key("test_server", "key1")

        # No primary set
        primary = server_api.get_primary_api_key_name("test_server")
        assert_that(primary).is_none()

    def test_get_primary_api_key_name_nonexistent_server(self, server_api: ServerCrud) -> None:
        """Test getting primary key for non-existent server returns None"""
        primary = server_api.get_primary_api_key_name("nonexistent")
        assert_that(primary).is_none()
