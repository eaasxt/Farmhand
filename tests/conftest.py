"""
Pytest configuration and shared fixtures for Farmhand hook tests.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


@pytest.fixture
def hooks_dir():
    """Return the path to the hooks directory."""
    return HOOKS_DIR


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary .claude directory for state files."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return claude_dir


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database mimicking MCP Agent Mail."""
    import sqlite3

    db_path = tmp_path / "storage.sqlite3"
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    # Enable WAL mode for consistency with production code
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    cursor = conn.cursor()

    # Create minimal schema matching MCP Agent Mail
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            human_key TEXT UNIQUE,
            created_ts TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE agents (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            name TEXT,
            program TEXT,
            model TEXT,
            created_ts TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE file_reservations (
            id INTEGER PRIMARY KEY,
            project_id INTEGER,
            agent_id INTEGER,
            path_pattern TEXT,
            exclusive INTEGER,
            reason TEXT,
            created_ts TEXT,
            expires_ts TEXT,
            released_ts TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    """)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Mock HOME directory to use tmp_path."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Create .claude directory
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    return tmp_path


def run_hook(hook_script: Path, input_data: dict, env: dict = None) -> tuple[int, str, str]:
    """
    Run a hook script with given input and return (exit_code, stdout, stderr).

    Args:
        hook_script: Path to the hook Python script
        input_data: Dictionary to pass as JSON via stdin
        env: Optional environment variables to set

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=run_env
    )

    return result.returncode, result.stdout, result.stderr


def parse_hook_output(stdout: str) -> dict:
    """Parse JSON output from a hook script."""
    if not stdout.strip():
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


@pytest.fixture
def run_hook_func(hooks_dir):
    """Fixture that returns a function to run hooks."""
    def _run(hook_name: str, input_data: dict, env: dict = None):
        hook_path = hooks_dir / hook_name
        return run_hook(hook_path, input_data, env)
    return _run
