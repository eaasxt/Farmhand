"""
Tests for mcp-state-tracker.py hook.

This hook tracks agent state after MCP Agent Mail tool calls.
"""

import json

import pytest

from conftest import run_hook


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
        """FARMHAND_SKIP_ENFORCEMENT=1 should bypass all tracking."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test"},
            "tool_response": json.dumps({"name": "TestAgent"})
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"FARMHAND_SKIP_ENFORCEMENT": "1"}
        )

        assert exit_code == 0
        # No state should be saved (we can't easily verify this without checking file)

    # === Non-tracked tools pass through ===

    def test_ignores_untracked_tools(self, hook_path):
        """Untracked tools (Bash, Grep, etc.) should pass through without action."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    def test_ignores_glob_tool(self, hook_path):
        """Glob tool should pass through."""
        input_data = {
            "tool_name": "Glob",
            "tool_input": {"pattern": "*.py"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    # === MCP tool recognition ===

    def test_recognizes_register_agent(self, hook_path, mock_home):
        """Should recognize register_agent tool."""
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test", "program": "claude", "model": "opus"},
            "tool_response": json.dumps({"name": "TestAgent"})
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
            "tool_response": json.dumps({"name": "BlueLake"})
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
            "tool_response": json.dumps({"success": True})
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
            "tool_response": json.dumps({"released": 1})
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
            "tool_response": json.dumps({
                "agent": {"name": "GreenMountain"},
                "success": True
            })
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
            "tool_response": json.dumps({"name": "BlueLake"})
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
            "tool_response": json.dumps({"name": "BlueLake"})
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
            "tool_response": json.dumps({"name": "TestAgent"})
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
            "tool_response": json.dumps({"success": True})
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
            "tool_response": json.dumps({"released": 1})
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


class TestArtifactTracking:
    """Test cases for artifact trail tracking (v4 feature)."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "mcp-state-tracker.py"

    @pytest.fixture
    def state_file(self, mock_home):
        """Create a state file path for testing."""
        return mock_home / ".claude" / "agent-state.json"

    def test_tracks_write_as_created(self, hook_path, mock_home):
        """Write tool should add file to files_created."""
        input_data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/home/test/new_file.py", "content": "..."}
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
        assert "/home/test/new_file.py" in state["files_created"]

    def test_tracks_edit_as_modified(self, hook_path, mock_home):
        """Edit tool should add file to files_modified."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/test/existing.py", "old_string": "a", "new_string": "b"}
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
        assert "/home/test/existing.py" in state["files_modified"]

    def test_tracks_read_as_read(self, hook_path, mock_home):
        """Read tool should add file to files_read."""
        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/home/test/readme.md"}
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
        assert "/home/test/readme.md" in state["files_read"]

    def test_deduplicates_file_entries(self, hook_path, mock_home):
        """Same file should only appear once in artifact lists."""
        # Create initial state
        state_dir = mock_home / ".claude"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "agent-state.json"
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "Test",
            "reservations": [],
            "files_created": [],
            "files_modified": ["/home/test/file.py"],
            "files_read": []
        }))

        # Edit same file again
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/test/file.py", "old_string": "a", "new_string": "b"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0
        state = json.loads(state_file.read_text())
        # Should still only have one entry
        assert state["files_modified"].count("/home/test/file.py") == 1

    def test_limits_files_read_to_50(self, hook_path, mock_home):
        """files_read should be limited to last 50 entries."""
        # Create initial state with 50 files
        state_dir = mock_home / ".claude"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "agent-state.json"
        initial_files = [f"/home/test/file{i}.py" for i in range(50)]
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "Test",
            "reservations": [],
            "files_created": [],
            "files_modified": [],
            "files_read": initial_files
        }))

        # Read a new file
        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/home/test/new_file.py"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0
        state = json.loads(state_file.read_text())
        # Should be exactly 50 entries
        assert len(state["files_read"]) == 50
        # New file should be present
        assert "/home/test/new_file.py" in state["files_read"]
        # First file should be gone (oldest removed)
        assert "/home/test/file0.py" not in state["files_read"]

    def test_backwards_compatible_with_old_state(self, hook_path, mock_home):
        """Should work with state files that don't have artifact fields."""
        # Create old-style state without artifact fields
        state_dir = mock_home / ".claude"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "agent-state.json"
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "Test",
            "reservations": []
            # No files_created, files_modified, files_read
        }))

        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/home/test/file.py"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(mock_home)}
        )

        assert exit_code == 0
        state = json.loads(state_file.read_text())
        # Should have created the artifact fields
        assert "files_created" in state
        assert "files_modified" in state
        assert "files_read" in state
        assert "/home/test/file.py" in state["files_modified"]
