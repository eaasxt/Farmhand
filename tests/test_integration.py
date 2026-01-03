"""
Integration tests for the full Farmhand workflow.

Tests the complete hook chain and state management.
"""

import json
import subprocess
import sys

import pytest

from conftest import run_hook


class TestFullWorkflow:
    """Integration tests for the complete workflow."""

    @pytest.fixture
    def workflow_env(self, mock_home, temp_db):
        """Set up a complete workflow environment."""
        # Create .claude directory structure
        claude_dir = mock_home / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        
        # Create mcp_agent_mail directory
        mcp_dir = mock_home / "mcp_agent_mail"
        mcp_dir.mkdir(exist_ok=True)
        
        # Copy temp_db to expected location
        import shutil
        shutil.copy(temp_db, mcp_dir / "storage.sqlite3")
        
        return {
            "home": mock_home,
            "db_path": mcp_dir / "storage.sqlite3",
            "claude_dir": claude_dir,
            "agent_name": "TestAgent"
        }

    def test_session_start_clears_state(self, hooks_dir, workflow_env):
        """Session start should clear stale state."""
        # Create a stale state file
        state_file = workflow_env["claude_dir"] / "agent-state.json"
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "OldAgent",
            "reservations": [{"paths": ["old/**"]}]
        }))
        
        # Run session-init hook
        hook_path = hooks_dir / "session-init.py"
        input_data = {"trigger": "startup"}
        
        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(workflow_env["home"])}
        )
        
        assert exit_code == 0
        # State file should be cleared
        assert not state_file.exists()

    def test_edit_blocked_without_registration(self, hooks_dir, workflow_env):
        """Edit should be blocked when not registered."""
        hook_path = hooks_dir / "reservation-checker.py"
        input_data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/home/testuser/project/file.py",
                "old_string": "foo",
                "new_string": "bar"
            }
        }
        
        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(workflow_env["home"])}
        )
        
        output = json.loads(stdout) if stdout.strip() else {}
        hook_output = output.get("hookSpecificOutput", {})
        
        assert exit_code == 0
        assert hook_output.get("permissionDecision") == "deny"
        assert "not registered" in hook_output.get("permissionDecisionReason", "").lower() or \
               "agent" in hook_output.get("permissionDecisionReason", "").lower()

    def test_todowrite_blocked(self, hooks_dir):
        """TodoWrite should be blocked and redirected to bd."""
        hook_path = hooks_dir / "todowrite-interceptor.py"
        input_data = {
            "tool_name": "TodoWrite",
            "tool_input": {
                "todos": [{"content": "Test task", "status": "pending"}]
            }
        }
        
        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        
        output = json.loads(stdout) if stdout.strip() else {}
        hook_output = output.get("hookSpecificOutput", {})
        
        assert exit_code == 0
        assert hook_output.get("permissionDecision") == "deny"
        reason = hook_output.get("permissionDecisionReason", "")
        assert "bd" in reason.lower() or "beads" in reason.lower()

    def test_escape_hatch_bypasses_all_hooks(self, hooks_dir, workflow_env):
        """FARMHAND_SKIP_ENFORCEMENT=1 should bypass all hooks."""
        env = {
            "HOME": str(workflow_env["home"]),
            "FARMHAND_SKIP_ENFORCEMENT": "1"
        }
        
        # Test reservation-checker
        hook_path = hooks_dir / "reservation-checker.py"
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/some/file.py"}
        }
        exit_code, stdout, stderr = run_hook(hook_path, input_data, env=env)
        assert exit_code == 0
        output = json.loads(stdout) if stdout.strip() else {}
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"
        
        # Test todowrite-interceptor
        hook_path = hooks_dir / "todowrite-interceptor.py"
        input_data = {
            "tool_name": "TodoWrite",
            "tool_input": {"todos": []}
        }
        exit_code, stdout, stderr = run_hook(hook_path, input_data, env=env)
        assert exit_code == 0
        output = json.loads(stdout) if stdout.strip() else {}
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_state_tracking_after_registration(self, hooks_dir, workflow_env):
        """State should be tracked after MCP registration call."""
        import json as json_module
        hook_path = hooks_dir / "mcp-state-tracker.py"
        input_data = {
            "tool_name": "register_agent",
            "tool_input": {"project_key": "/home/test"},
            "tool_response": json_module.dumps({"name": "BlueLake"})
        }
        
        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"HOME": str(workflow_env["home"])}
        )
        
        assert exit_code == 0
        
        # Check state file was created
        state_file = workflow_env["claude_dir"] / "agent-state.json"
        assert state_file.exists()
        
        state = json.loads(state_file.read_text())
        assert state["registered"] is True
        assert state["agent_name"] == "BlueLake"


class TestHookChaining:
    """Test that hooks work correctly in sequence."""

    def test_workflow_sequence(self, hooks_dir, mock_home, temp_db):
        """Test the complete workflow: session-init -> register -> reserve -> edit."""
        import shutil
        
        # Set up environment
        claude_dir = mock_home / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        
        mcp_dir = mock_home / "mcp_agent_mail"
        mcp_dir.mkdir(exist_ok=True)
        shutil.copy(temp_db, mcp_dir / "storage.sqlite3")
        
        env = {"HOME": str(mock_home), "AGENT_NAME": "TestAgent"}
        
        # Step 1: Session init
        hook_path = hooks_dir / "session-init.py"
        exit_code, _, _ = run_hook(
            hook_path,
            {"trigger": "startup"},
            env=env
        )
        assert exit_code == 0
        
        # Step 2: Simulate registration (create state file)
        state_file = claude_dir / "state-TestAgent.json"
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "TestAgent",
            "reservations": []
        }))
        
        # Step 3: Try to edit without reservation - should fail
        hook_path = hooks_dir / "reservation-checker.py"
        input_data = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/home/testuser/project/file.py",
                "old_string": "a",
                "new_string": "b"
            }
        }
        exit_code, stdout, _ = run_hook(hook_path, input_data, env=env)
        output = json.loads(stdout) if stdout.strip() else {}
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


class TestErrorRecovery:
    """Test error recovery scenarios."""

    def test_malformed_json_handled_gracefully(self, hooks_dir):
        """All hooks should handle malformed JSON gracefully."""
        hooks = [
            "todowrite-interceptor.py",
            "reservation-checker.py",
            "git_safety_guard.py",
            "session-init.py",
            "mcp-state-tracker.py"
        ]
        
        for hook_name in hooks:
            hook_path = hooks_dir / hook_name
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input="not valid json",
                capture_output=True,
                text=True
            )
            
            # All hooks should handle gracefully (exit 0 or 1, no crash)
            assert result.returncode in [0, 1], \
                f"{hook_name} crashed on malformed JSON"

    def test_empty_input_handled(self, hooks_dir):
        """All hooks should handle empty input gracefully."""
        hooks = [
            "todowrite-interceptor.py",
            "reservation-checker.py",
            "git_safety_guard.py",
            "session-init.py",
            "mcp-state-tracker.py"
        ]
        
        for hook_name in hooks:
            hook_path = hooks_dir / hook_name
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input="",
                capture_output=True,
                text=True
            )
            
            # Should not crash
            assert result.returncode in [0, 1], \
                f"{hook_name} crashed on empty input"
