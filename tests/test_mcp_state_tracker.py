"""
Tests for mcp-state-tracker.py hook.

This hook tracks agent state after MCP Agent Mail tool calls.
"""

import json
import os
import time
from pathlib import Path

import pytest

from conftest import run_hook, parse_hook_output


class TestMcpStateTracker:
    """Test cases for MCP state tracker hook."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "mcp-state-tracker.py"

    @pytest.fixture
    def state_file(self, mock_home):
        """Create a state file path for testing."""
        return mock_home / ".claude" / "agent-state.json"

    # === Escape hatch ===

    def test_escape_hatch_bypasses_tracking(self, hook_path):
        """JOHNDEERE_SKIP_ENFORCEMENT=1 should bypass all tracking."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test"},
            "tool_output": {"name": "TestAgent"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"JOHNDEERE_SKIP_ENFORCEMENT": "1"}
        )

        assert exit_code == 0
        # No state should be saved (we can't easily verify this without checking file)

    # === Non-MCP tools pass through ===

    def test_ignores_non_mcp_tools(self, hook_path):
        """Non-MCP tools should pass through without action."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/some/file.py"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    def test_ignores_read_tool(self, hook_path):
        """Read tool should pass through."""
        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file.py"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    # === MCP tool recognition ===

    def test_recognizes_register_agent(self, hook_path, mock_home):
        """Should recognize register_agent tool."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test", "program": "claude", "model": "opus"},
            "tool_output": {"name": "TestAgent"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0

    def test_recognizes_mcp_prefixed_register_agent(self, hook_path, mock_home):
        """Should recognize mcp__mcp-agent-mail__register_agent."""
        input_data = {
            "tool_name": "mcp__mcp-agent-mail__register_agent",
            "tool_input": {"project_key": "/home/test"},
            "tool_output": {"name": "BlueLake"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0

    def test_recognizes_file_reservation_paths(self, hook_path, mock_home):
        """Should recognize file_reservation_paths tool."""
        input_data = {
            "tool_name": "file_reservation_paths",
            "tool_input": {
                "project_key": "/home/test",
                "agent_name": "TestAgent",
                "paths": ["src/**"],
                "ttl_seconds": 3600,
                "exclusive": True,
                "reason": "test-123"
            },
            "tool_output": {"success": True}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0

    def test_recognizes_release_file_reservations(self, hook_path, mock_home):
        """Should recognize release_file_reservations tool."""
        input_data = {
            "tool_name": "release_file_reservations",
            "tool_input": {"project_key": "/home/test", "agent_name": "TestAgent"},
            "tool_output": {"released": 1}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0

    def test_recognizes_macro_start_session(self, hook_path, mock_home):
        """Should recognize macro_start_session tool."""
        input_data = {
            "tool_name": "macro_start_session",
            "tool_input": {
                "human_key": "/home/test",
                "program": "claude",
                "model": "opus"
            },
            "tool_output": {
                "agent_name": "GreenMountain",
                "success": True
            }
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0

    # === State file handling ===

    def test_uses_agent_name_in_state_file(self, hook_path, mock_home):
        """Should use state-{AGENT_NAME}.json when AGENT_NAME is set."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test"},
            "tool_output": {"name": "BlueLake"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home), "AGENT_NAME": "MyAgent"}
        )

        assert exit_code == 0
        # State file should be created with agent name
        expected_state_file = mock_home / ".claude" / "state-MyAgent.json"
        assert expected_state_file.exists()

    def test_uses_legacy_state_file_without_agent_name(self, hook_path, mock_home):
        """Should use agent-state.json when AGENT_NAME is not set."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test"},
            "tool_output": {"name": "BlueLake"}
        }

        # Ensure AGENT_NAME is not set
        env = {"HOME": str(mock_home)}

        exit_code, stdout, stderr = run_hook(hook_path, input_data, env=env)

        assert exit_code == 0
        # Legacy state file should be created
        expected_state_file = mock_home / ".claude" / "agent-state.json"
        assert expected_state_file.exists()

    # === Registration tracking ===

    def test_tracks_registration(self, hook_path, mock_home):
        """Should save registered=True after register_agent."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test"},
            "tool_output": {"name": "TestAgent"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0
        state_file = mock_home / ".claude" / "agent-state.json"
        assert state_file.exists()
        
        state = json.loads(state_file.read_text())
        assert state["registered"] is True
        assert state["agent_name"] == "TestAgent"

    # === Reservation tracking ===

    def test_tracks_reservations(self, hook_path, mock_home):
        """Should track reservations after file_reservation_paths."""
        input_data = {
            "tool_name": "file_reservation_paths",
            "tool_input": {
                "paths": ["src/**", "tests/**"],
                "reason": "issue-123",
                "ttl_seconds": 7200
            },
            "tool_output": {"success": True}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0
        state_file = mock_home / ".claude" / "agent-state.json"
        assert state_file.exists()
        
        state = json.loads(state_file.read_text())
        assert len(state["reservations"]) == 1
        assert state["reservations"][0]["paths"] == ["src/**", "tests/**"]
        assert state["reservations"][0]["reason"] == "issue-123"
        assert state["issue_id"] == "issue-123"

    def test_clears_reservations_on_release(self, hook_path, mock_home):
        """Should clear reservations after release_file_reservations."""
        # First create a state file with reservations
        state_dir = mock_home / ".claude"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "agent-state.json"
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "TestAgent",
            "reservations": [{"paths": ["src/**"], "reason": "test"}],
            "issue_id": "test"
        }))

        input_data = {
            "tool_name": "release_file_reservations",
            "tool_input": {"project_key": "/home/test", "agent_name": "TestAgent"},
            "tool_output": {"released": 1}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0
        state = json.loads(state_file.read_text())
        assert state["reservations"] == []

    # === Error handling ===

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

        # Should exit 0 (non-blocking on parse errors)
        assert result.returncode == 0

    def test_handles_empty_input(self, hook_path):
        """Empty input should be handled gracefully."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_handles_missing_tool_output(self, hook_path, mock_home):
        """Should handle missing tool_output gracefully."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test"}
            # No tool_output
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        # Should not crash
        assert exit_code == 0
