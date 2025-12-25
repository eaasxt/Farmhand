"""
Tests for session-init.py hook.

This hook runs on session start to:
- Clear stale agent state
- Clean up old state files (>7 days)
- Check for orphaned reservations
- Inject workflow context
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from conftest import run_hook, parse_hook_output


class TestSessionInit:
    """Test cases for session init hook."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "session-init.py"

    @pytest.fixture
    def setup_state_dir(self, mock_home):
        """Set up .claude directory with state files."""
        claude_dir = mock_home / ".claude"
        return claude_dir

    # === State file cleanup on startup ===

    def test_clears_agent_state_on_startup(self, hook_path, setup_state_dir):
        """State file for current agent should be cleared on startup."""
        state_file = setup_state_dir / "state-TestAgent.json"
        state_file.write_text(json.dumps({"agent_name": "TestAgent", "old": "data"}))

        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"AGENT_NAME": "TestAgent", "HOME": str(setup_state_dir.parent)}
        )

        assert exit_code == 0
        # State file should be removed
        assert not state_file.exists()

    def test_clears_agent_state_on_clear(self, hook_path, setup_state_dir):
        """State file should be cleared on 'clear' trigger."""
        state_file = setup_state_dir / "state-TestAgent.json"
        state_file.write_text(json.dumps({"agent_name": "TestAgent"}))

        input_data = {"trigger": "clear"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"AGENT_NAME": "TestAgent", "HOME": str(setup_state_dir.parent)}
        )

        assert exit_code == 0
        assert not state_file.exists()

    def test_preserves_other_agent_state(self, hook_path, setup_state_dir):
        """Other agents' state files should NOT be cleared."""
        my_state = setup_state_dir / "state-MyAgent.json"
        other_state = setup_state_dir / "state-OtherAgent.json"

        my_state.write_text(json.dumps({"agent_name": "MyAgent"}))
        other_state.write_text(json.dumps({"agent_name": "OtherAgent"}))

        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"AGENT_NAME": "MyAgent", "HOME": str(setup_state_dir.parent)}
        )

        assert exit_code == 0
        # My state should be cleared
        assert not my_state.exists()
        # Other agent's state should remain
        assert other_state.exists()

    # === Old state file cleanup ===

    def test_cleans_old_state_files(self, hook_path, setup_state_dir):
        """State files older than 7 days should be cleaned up."""
        # Create an old state file (simulate 8 days old)
        old_state = setup_state_dir / "state-OldAgent.json"
        old_state.write_text(json.dumps({"agent_name": "OldAgent"}))

        # Set modification time to 8 days ago
        old_time = time.time() - (8 * 24 * 3600)
        os.utime(old_state, (old_time, old_time))

        # Create a recent state file
        recent_state = setup_state_dir / "state-RecentAgent.json"
        recent_state.write_text(json.dumps({"agent_name": "RecentAgent"}))

        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"AGENT_NAME": "NewAgent", "HOME": str(setup_state_dir.parent)}
        )

        assert exit_code == 0
        # Old state file should be cleaned up
        assert not old_state.exists()
        # Recent state file should remain
        assert recent_state.exists()

    def test_reports_cleaned_files_in_context(self, hook_path, setup_state_dir):
        """Cleaned files should be reported in the context message."""
        # Create old state file
        old_state = setup_state_dir / "state-VeryOldAgent.json"
        old_state.write_text(json.dumps({"agent_name": "VeryOldAgent"}))
        old_time = time.time() - (10 * 24 * 3600)
        os.utime(old_state, (old_time, old_time))

        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"AGENT_NAME": "NewAgent", "HOME": str(setup_state_dir.parent)}
        )

        output = parse_hook_output(stdout)

        assert exit_code == 0
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "cleaned" in context.lower() or "old state" in context.lower()

    # === Workflow reminder ===

    def test_includes_workflow_reminder(self, hook_path, setup_state_dir):
        """Output should include workflow reminder."""
        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(setup_state_dir.parent)}
        )

        output = parse_hook_output(stdout)

        assert exit_code == 0
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "CLAUDE.md" in context or "workflow" in context.lower()

    # === Single-agent mode (no AGENT_NAME) ===

    def test_uses_legacy_state_file_without_agent_name(self, hook_path, setup_state_dir):
        """Without AGENT_NAME, should use agent-state.json."""
        legacy_state = setup_state_dir / "agent-state.json"
        legacy_state.write_text(json.dumps({"old": "data"}))

        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(setup_state_dir.parent)}
            # No AGENT_NAME set
        )

        assert exit_code == 0
        # Legacy state file should be cleared
        assert not legacy_state.exists()

    # === Output format ===

    def test_outputs_valid_hook_json(self, hook_path, setup_state_dir):
        """Output should be valid hook JSON format."""
        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(setup_state_dir.parent)}
        )

        assert exit_code == 0
        output = parse_hook_output(stdout)

        # Should have hookSpecificOutput
        assert "hookSpecificOutput" in output
        assert "hookEventName" in output["hookSpecificOutput"]
        assert output["hookSpecificOutput"]["hookEventName"] == "SessionStart"

    # === Edge cases ===

    def test_handles_missing_trigger(self, hook_path, setup_state_dir):
        """Missing trigger should default to startup."""
        input_data = {}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(setup_state_dir.parent)}
        )

        assert exit_code == 0

    def test_handles_nonexistent_state_dir(self, hook_path, tmp_path):
        """Should handle case where .claude directory doesn't exist."""
        # tmp_path has no .claude directory
        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(tmp_path)}
        )

        # Should not crash
        assert exit_code == 0

    def test_handles_empty_json_input(self, hook_path, setup_state_dir):
        """Empty JSON input should be handled."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="{}",
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(setup_state_dir.parent)}
        )

        assert result.returncode == 0


class TestOrphanedReservationDetection:
    """Test cases for orphaned reservation detection."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "session-init.py"

    def test_detects_stale_reservations(self, hook_path, mock_home, temp_db):
        """Should detect reservations older than 4 hours."""
        # Set up database with old reservation
        import sqlite3

        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()

        # Insert project and agent
        cursor.execute(
            "INSERT INTO projects (human_key, created_ts) VALUES (?, ?)",
            ("/test", datetime.now(timezone.utc).isoformat())
        )
        project_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO agents (project_id, name, program, model, created_ts) VALUES (?, ?, ?, ?, ?)",
            (project_id, "StaleAgent", "claude", "opus", datetime.now(timezone.utc).isoformat())
        )
        agent_id = cursor.lastrowid

        # Create reservation from 5 hours ago
        old_time = datetime.now(timezone.utc) - timedelta(hours=5)
        future_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        cursor.execute(
            """INSERT INTO file_reservations
               (agent_id, path_pattern, exclusive, reason, created_ts, expires_ts, released_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (agent_id, "/stale/path/**", 1, "old-task",
             old_time.isoformat(), future_expires.isoformat(), None)
        )

        conn.commit()
        conn.close()

        # Move db to expected location
        mcp_dir = mock_home / "mcp_agent_mail"
        mcp_dir.mkdir()
        import shutil
        shutil.copy(temp_db, mcp_dir / "storage.sqlite3")

        input_data = {"trigger": "startup"}

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        output = parse_hook_output(stdout)

        assert exit_code == 0
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        # Should mention orphaned/stale reservations
        assert "orphan" in context.lower() or "stale" in context.lower() or "bd-cleanup" in context.lower()
