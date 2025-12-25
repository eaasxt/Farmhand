"""
Tests for reservation-checker.py hook.

This hook enforces file reservations before allowing Edit/Write operations.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from conftest import run_hook, parse_hook_output


class TestReservationChecker:
    """Test cases for reservation checker hook."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "reservation-checker.py"

    @pytest.fixture
    def setup_db_with_agent(self, temp_db):
        """Set up database with a registered agent."""
        conn = sqlite3.connect(str(temp_db), timeout=30.0)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        cursor = conn.cursor()

        # Insert project
        cursor.execute(
            "INSERT INTO projects (human_key, created_ts) VALUES (?, ?)",
            ("/home/testuser", datetime.now(timezone.utc).isoformat())
        )
        project_id = cursor.lastrowid

        # Insert agent
        cursor.execute(
            "INSERT INTO agents (project_id, name, program, model, created_ts) VALUES (?, ?, ?, ?, ?)",
            (project_id, "TestAgent", "claude-code", "opus-4.5", datetime.now(timezone.utc).isoformat())
        )
        agent_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {"db_path": temp_db, "agent_id": agent_id, "agent_name": "TestAgent"}

    @pytest.fixture
    def setup_db_with_reservation(self, setup_db_with_agent):
        """Set up database with agent and file reservation."""
        db_info = setup_db_with_agent
        conn = sqlite3.connect(str(db_info["db_path"]), timeout=30.0)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        cursor = conn.cursor()

        # Add reservation (need project_id from setup_db_with_agent)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)

        # Get the project_id (first project created)
        cursor.execute("SELECT id FROM projects LIMIT 1")
        project_id = cursor.fetchone()[0]

        cursor.execute(
            """INSERT INTO file_reservations
               (project_id, agent_id, path_pattern, exclusive, reason, created_ts, expires_ts, released_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (project_id, db_info["agent_id"], "/home/testuser/project/**", 1, "test-123",
             now.isoformat(), expires.isoformat(), None)
        )

        conn.commit()
        conn.close()

        db_info["reserved_pattern"] = "/home/testuser/project/**"
        return db_info

    # === Basic functionality ===

    def test_allows_non_edit_write_tools(self, hook_path):
        """Non-Edit/Write tools should pass through."""
        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file.py"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    def test_allows_bash_tool(self, hook_path):
        """Bash tool should pass through (handled by git_safety_guard)."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    # === Skip paths ===

    def test_allows_mcp_agent_mail_edits(self, hook_path):
        """Edits to mcp_agent_mail directory should be allowed (self-management)."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/ubuntu/mcp_agent_mail/storage.sqlite3"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        # Should allow without checking reservations
        assert exit_code == 0

    def test_allows_beads_directory_edits(self, hook_path):
        """Edits to .beads directory should be allowed."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/ubuntu/.beads/issues.jsonl"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    def test_allows_tmp_edits(self, hook_path):
        """Edits to /tmp should be allowed."""
        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test.txt", "content": "test"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    # === Escape hatch ===

    def test_escape_hatch_bypasses_all_checks(self, hook_path):
        """FARMHAND_SKIP_ENFORCEMENT=1 should bypass all checks."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/some/protected/file.py"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"FARMHAND_SKIP_ENFORCEMENT": "1"}
        )

        assert exit_code == 0
        output = parse_hook_output(stdout)
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    # === Agent not registered ===

    def test_blocks_when_agent_not_registered(self, hook_path, mock_home):
        """Edit should be blocked when agent is not registered."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/home/testuser/project/file.py",
                "old_string": "foo",
                "new_string": "bar"
            }
        }

        # No AGENT_NAME set, no state file exists
        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        reason = output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        assert "not registered" in reason.lower() or "agent" in reason.lower()

    # === With AGENT_NAME env var ===

    def test_blocks_when_file_not_reserved(self, hook_path, mock_home, temp_db):
        """Edit should be blocked when file is not reserved."""
        # Create state file with registered=True and agent_name
        state_file = mock_home / ".claude" / "state-TestAgent.json"
        state_file.write_text(json.dumps({"registered": True, "agent_name": "TestAgent"}))

        # Create mcp_agent_mail directory with db
        mcp_dir = mock_home / "mcp_agent_mail"
        mcp_dir.mkdir()

        # Copy temp_db to expected location
        import shutil
        shutil.copy(temp_db, mcp_dir / "storage.sqlite3")

        # Use a fake path that looks like a real project file
        # IMPORTANT: Can't use mock_home paths because they're in /tmp/ which is skipped
        fake_file_path = "/home/testuser/project/file.py"

        input_data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": fake_file_path,
                "old_string": "foo",
                "new_string": "bar"
            }
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"AGENT_NAME": "TestAgent", "HOME": str(mock_home)}
        )
        output = parse_hook_output(stdout)

        assert exit_code == 0
        # Should be denied because file is not reserved
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny", f"Expected deny but got {decision}. Output: {output}"
        reason = output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        assert "not reserved" in reason.lower() or "reserve" in reason.lower()

    # === Edge cases ===

    def test_handles_empty_file_path(self, hook_path):
        """Empty file path should pass through."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": ""}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        # Should exit 0 (no file to check)
        assert exit_code == 0

    def test_handles_missing_file_path(self, hook_path):
        """Missing file_path key should be handled."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    def test_handles_malformed_json(self, hook_path):
        """Malformed JSON should be handled gracefully."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="not valid json",
            capture_output=True,
            text=True
        )

        # Should exit with error code (1 for JSON decode error)
        assert result.returncode == 1


class TestReservationPatternMatching:
    """Test cases for glob pattern matching in reservations."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "reservation-checker.py"

    def test_glob_star_star_matches_nested(self):
        """Test that ** pattern matches nested directories."""
        # This tests the fnmatch logic directly
        import fnmatch

        pattern = "/home/user/project/**"
        # Note: fnmatch doesn't handle ** like gitignore
        # The hook likely uses custom logic

        # Test basic match
        assert fnmatch.fnmatch("/home/user/project/file.py", "/home/user/project/*")

    def test_exact_path_match(self):
        """Test exact path matching."""
        import fnmatch

        pattern = "/home/user/file.py"
        assert fnmatch.fnmatch("/home/user/file.py", pattern)
        assert not fnmatch.fnmatch("/home/user/other.py", pattern)


class TestFileMatchesPattern:
    """Unit tests for the file_matches_pattern function."""

    @pytest.fixture
    def file_matches_pattern(self, hooks_dir):
        """Import and return the file_matches_pattern function from the hook."""
        import sys
        import importlib.util

        hook_path = hooks_dir / "reservation-checker.py"
        spec = importlib.util.spec_from_file_location("reservation_checker", hook_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["reservation_checker"] = module
        spec.loader.exec_module(module)
        return module.file_matches_pattern

    # === ** pattern tests ===

    def test_double_star_matches_direct_child(self, file_matches_pattern):
        """Pattern /home/user/project/** should match direct children."""
        assert file_matches_pattern("/home/user/project/file.py", "/home/user/project/**")

    def test_double_star_matches_nested_deeply(self, file_matches_pattern):
        """Pattern /home/user/project/** should match deeply nested files."""
        assert file_matches_pattern(
            "/home/user/project/src/utils/helpers/file.py",
            "/home/user/project/**"
        )

    def test_double_star_no_match_outside_prefix(self, file_matches_pattern):
        """Pattern /home/user/project/** should NOT match files outside prefix."""
        assert not file_matches_pattern("/home/other/file.py", "/home/user/project/**")

    def test_double_star_no_match_sibling_dir(self, file_matches_pattern):
        """Pattern /home/user/project/** should NOT match sibling directories."""
        assert not file_matches_pattern(
            "/home/user/other-project/file.py",
            "/home/user/project/**"
        )

    # === **/*.ext pattern tests ===

    def test_double_star_with_extension_matches(self, file_matches_pattern):
        """Pattern /project/**/*.py should match .py files anywhere under project."""
        assert file_matches_pattern("/project/file.py", "/project/**/*.py")
        assert file_matches_pattern("/project/src/file.py", "/project/**/*.py")
        assert file_matches_pattern("/project/src/deep/nested/file.py", "/project/**/*.py")

    def test_double_star_with_extension_no_match_wrong_ext(self, file_matches_pattern):
        """Pattern /project/**/*.py should NOT match non-.py files."""
        assert not file_matches_pattern("/project/file.js", "/project/**/*.py")
        assert not file_matches_pattern("/project/src/file.ts", "/project/**/*.py")

    # === Simple * pattern tests ===

    def test_single_star_matches_single_level(self, file_matches_pattern):
        """Pattern /project/*.py should match files in that directory."""
        assert file_matches_pattern("/project/file.py", "/project/*.py")

    def test_single_star_also_matches_subdirs(self, file_matches_pattern):
        """Pattern /project/* should match subdirectory files (directory prefix matching)."""
        # This is our extension - * patterns also match as prefix
        assert file_matches_pattern("/project/src/file.py", "/project/*")

    # === Exact path tests ===

    def test_exact_path_matches(self, file_matches_pattern):
        """Exact paths should match exactly."""
        assert file_matches_pattern("/home/user/file.py", "/home/user/file.py")

    def test_exact_path_no_match_different(self, file_matches_pattern):
        """Exact paths should NOT match different files."""
        assert not file_matches_pattern("/home/user/other.py", "/home/user/file.py")

    # === Edge cases ===

    def test_relative_patterns_need_matching_prefix(self, file_matches_pattern):
        """Should handle patterns that look relative (like src/**)."""
        # With an absolute file path, relative-looking patterns won't match
        # unless the file happens to start with that
        # Relative patterns only match if file starts with same prefix
        # src/** wont match /src/file.py because prefix "src" != "/src"
        assert not file_matches_pattern("/src/file.py", "src/**")
        # This is expected - src/** would match /src/... if prefix is empty

    def test_handles_trailing_slashes(self, file_matches_pattern):
        """Should handle patterns with trailing slashes."""
        assert file_matches_pattern("/project/file.py", "/project/**")
        assert file_matches_pattern("/project/file.py", "/project/**/")
