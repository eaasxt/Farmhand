"""
Tests for todowrite-interceptor.py hook.

This hook blocks all TodoWrite tool calls and suggests using beads (bd) instead.
"""

import pytest

from conftest import run_hook, parse_hook_output


class TestTodoWriteInterceptor:
    """Test cases for TodoWrite interceptor hook."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "todowrite-interceptor.py"

    def test_blocks_todowrite_with_pending_todos(self, hook_path):
        """TodoWrite with pending todos should be blocked."""
        input_data = {
            "tool_name": "TodoWrite",
            "tool_input": {
                "todos": [
                    {"content": "Fix the bug", "status": "pending", "activeForm": "Fixing the bug"}
                ]
            }
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        assert "BLOCKED" in output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        assert "bd create" in output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")

    def test_blocks_todowrite_with_in_progress(self, hook_path):
        """TodoWrite with in_progress todos should be blocked."""
        input_data = {
            "tool_name": "TodoWrite",
            "tool_input": {
                "todos": [
                    {"content": "Working on feature", "status": "in_progress", "activeForm": "Working"}
                ]
            }
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        assert "bd update" in output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")

    def test_blocks_todowrite_with_completed(self, hook_path):
        """TodoWrite with completed todos should be blocked."""
        input_data = {
            "tool_name": "TodoWrite",
            "tool_input": {
                "todos": [
                    {"content": "Done with task", "status": "completed", "activeForm": "Done"}
                ]
            }
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        assert "bd close" in output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")

    def test_allows_non_todowrite_tools(self, hook_path):
        """Non-TodoWrite tools should be allowed through."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/some/file.py",
                "old_string": "foo",
                "new_string": "bar"
            }
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        # Should exit 0 with no output (allow)
        assert exit_code == 0
        assert stdout.strip() == "" or "deny" not in stdout

    def test_escape_hatch_bypasses_block(self, hook_path):
        """FARMHAND_SKIP_ENFORCEMENT=1 should bypass the block."""
        input_data = {
            "tool_name": "TodoWrite",
            "tool_input": {
                "todos": [
                    {"content": "Test", "status": "pending", "activeForm": "Testing"}
                ]
            }
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"FARMHAND_SKIP_ENFORCEMENT": "1"}
        )

        # Should exit 0 with no denial
        assert exit_code == 0
        output = parse_hook_output(stdout)
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_handles_empty_todos_list(self, hook_path):
        """Empty todos list should still be blocked (it's still TodoWrite)."""
        input_data = {
            "tool_name": "TodoWrite",
            "tool_input": {
                "todos": []
            }
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_handles_malformed_input(self, hook_path):
        """Malformed JSON input should not crash."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="not valid json",
            capture_output=True,
            text=True
        )

        # Should handle gracefully (exit 1 for parse error is acceptable)
        assert result.returncode in [0, 1]
