#!/usr/bin/env python3
"""
Base database class with common CRUD patterns for n8n-deploy

Provides reusable connection management and common database operations.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, Union

from ..config import AppConfig


class BaseDB:
    """Base database class with common connection management"""

    def __init__(
        self,
        config: Optional[AppConfig] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize database with path resolution

        Args:
            config: Application configuration with database path
            db_path: Direct database path (overrides config)
        """
        # Database path resolution: config > direct path > default
        if config is not None:
            self.db_path = config.database_path
        elif db_path is not None:
            self.db_path = Path(db_path)
        else:
            from ..config import get_config

            default_config = get_config()
            self.db_path = default_config.database_path

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """
        Context manager for database connections

        Yields:
            SQLite connection with Row factory for dict-like access

        Example:
            >>> with db.get_connection() as conn:
            ...     cursor = conn.execute("SELECT * FROM workflows")
            ...     results = cursor.fetchall()
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(
        self,
        query: str,
        params: Sequence[Any] = (),
        commit: bool = False,
    ) -> sqlite3.Cursor:
        """
        Execute a SQL query with automatic connection management

        Args:
            query: SQL query to execute
            params: Query parameters
            commit: Whether to commit the transaction

        Returns:
            SQLite cursor with query results

        Example:
            >>> cursor = db.execute_query("SELECT * FROM workflows WHERE id = ?", ("wf_123",))
            >>> row = cursor.fetchone()
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            if commit:
                conn.commit()
            return cursor
