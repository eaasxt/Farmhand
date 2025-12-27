#!/usr/bin/env python3
"""
Database Utilities for Farmhand Hooks
--------------------------------------
Shared utilities for SQLite connections with proper concurrency handling.

Features:
- WAL mode for better concurrent access
- Busy timeout to handle lock contention
- Retry logic for transient failures
"""

import sqlite3
import time
from pathlib import Path
from typing import Optional, Callable, Any

# Default configuration
DEFAULT_TIMEOUT = 30.0  # seconds
DEFAULT_BUSY_TIMEOUT = 30000  # milliseconds
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # seconds (exponential backoff base)


def get_connection(
    db_path: Path,
    timeout: float = DEFAULT_TIMEOUT,
    busy_timeout: int = DEFAULT_BUSY_TIMEOUT,
    enable_wal: bool = True
) -> sqlite3.Connection:
    """
    Get a SQLite connection with proper concurrency settings.

    Args:
        db_path: Path to the SQLite database
        timeout: Connection timeout in seconds
        busy_timeout: Busy timeout in milliseconds
        enable_wal: Whether to enable WAL mode (recommended for concurrency)

    Returns:
        Configured sqlite3.Connection

    Raises:
        sqlite3.Error: If connection fails after retries
    """
    conn = sqlite3.connect(str(db_path), timeout=timeout)

    # Enable WAL mode for better concurrent access
    if enable_wal:
        conn.execute('PRAGMA journal_mode=WAL')

    # Set busy timeout to wait for locks instead of failing immediately
    conn.execute(f'PRAGMA busy_timeout={busy_timeout}')

    # Enable foreign keys for data integrity
    conn.execute('PRAGMA foreign_keys=ON')

    return conn


def execute_with_retry(
    db_path: Path,
    operation: Callable[[sqlite3.Connection], Any],
    max_retries: int = MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT
) -> Any:
    """
    Execute a database operation with retry logic.

    Args:
        db_path: Path to the SQLite database
        operation: Callable that takes a connection and performs the operation
        max_retries: Maximum number of retry attempts
        timeout: Connection timeout in seconds

    Returns:
        Result of the operation

    Raises:
        sqlite3.Error: If operation fails after all retries
    """
    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            conn = get_connection(db_path, timeout=timeout)
            try:
                result = operation(conn)
                conn.commit()
                return result
            finally:
                conn.close()
        except sqlite3.OperationalError as e:
            last_error = e
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                # Exponential backoff
                delay = RETRY_DELAY * (2 ** attempt)
                time.sleep(delay)
                continue
            raise
        except sqlite3.Error as e:
            last_error = e
            raise

    # This point is only reachable if max_retries is 0 (no iterations)
    raise sqlite3.Error("Operation failed: max_retries must be at least 1")


def query_with_retry(
    db_path: Path,
    query: str,
    params: tuple = (),
    max_retries: int = MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT
) -> list:
    """
    Execute a query with retry logic.

    Args:
        db_path: Path to the SQLite database
        query: SQL query to execute
        params: Query parameters
        max_retries: Maximum number of retry attempts
        timeout: Connection timeout in seconds

    Returns:
        List of rows from the query

    Raises:
        sqlite3.Error: If query fails after all retries
    """
    def do_query(conn: sqlite3.Connection) -> list:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    return execute_with_retry(db_path, do_query, max_retries, timeout)
