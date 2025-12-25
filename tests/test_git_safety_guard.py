"""
Tests for git_safety_guard.py hook.

This hook blocks destructive git and filesystem commands.
"""

import json
import pytest

from conftest import run_hook, parse_hook_output


class TestGitSafetyGuard:
    """Test cases for git safety guard hook."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "git_safety_guard.py"

    # === Destructive commands that SHOULD be blocked ===

    def test_blocks_git_reset_hard(self, hook_path):
        """git reset --hard should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git reset --hard HEAD~1"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        assert "BLOCKED" in output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")

    def test_blocks_git_clean_force(self, hook_path):
        """git clean -f should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git clean -fd"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_git_push_force(self, hook_path):
        """git push --force should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_git_push_force_short(self, hook_path):
        """git push -f should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push -f origin main"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_git_push_force_with_lease(self, hook_path):
        """git push --force-with-lease should be blocked (still rewrites history)."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force-with-lease origin main"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_git_push_plus_refspec(self, hook_path):
        """git push origin +main should be blocked (+ prefix force push)."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin +main"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        assert "refspec" in output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "").lower() or \
               "remote history" in output.get("hookSpecificOutput", {}).get("permissionDecisionReason", "").lower()

    def test_blocks_git_branch_force_delete(self, hook_path):
        """git branch -D should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git branch -D feature-branch"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_git_stash_drop(self, hook_path):
        """git stash drop should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git stash drop"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_git_stash_clear(self, hook_path):
        """git stash clear should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git stash clear"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_rm_rf(self, hook_path):
        """rm -rf on non-temp directories should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf src/"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_blocks_git_checkout_dot(self, hook_path):
        """git checkout . should be blocked."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git checkout ."}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    # === Safe commands that SHOULD be allowed ===

    def test_allows_git_checkout_branch(self, hook_path):
        """git checkout -b should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git checkout -b new-feature"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        # Should not have a deny decision
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_allows_git_status(self, hook_path):
        """git status should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_allows_git_log(self, hook_path):
        """git log should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git log --oneline -10"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_allows_git_push_normal(self, hook_path):
        """Normal git push should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin main"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_allows_git_clean_dry_run(self, hook_path):
        """git clean -n (dry run) should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git clean -n"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_allows_rm_rf_tmp(self, hook_path):
        """rm -rf /tmp/ should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/myapp-cache/"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    def test_allows_git_restore_staged(self, hook_path):
        """git restore --staged should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git restore --staged file.py"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)

        assert exit_code == 0
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    # === Non-Bash tools should pass through ===

    def test_allows_non_bash_tools(self, hook_path):
        """Non-Bash tools should be allowed."""
        input_data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/some/file.py"}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

    # === Escape hatch ===

    def test_escape_hatch_bypasses_block(self, hook_path):
        """FARMHAND_SKIP_ENFORCEMENT=1 should bypass the block."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git reset --hard HEAD~1"}
        }

        exit_code, stdout, stderr = run_hook(
            hook_path,
            input_data,
            env={"FARMHAND_SKIP_ENFORCEMENT": "1"}
        )

        assert exit_code == 0
        output = parse_hook_output(stdout)
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"

    # === Edge cases ===

    def test_handles_empty_command(self, hook_path):
        """Empty command should be allowed."""
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": ""}
        }

        exit_code, stdout, stderr = run_hook(hook_path, input_data)

        assert exit_code == 0

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


class TestHeredocStripping:
    """Tests for heredoc content stripping to avoid false positives."""

    @pytest.fixture
    def hook_path(self, hooks_dir):
        return hooks_dir / "git_safety_guard.py"

    def test_heredoc_content_not_scanned(self, hook_path):
        """Heredoc content should not trigger blocking."""
        cmd = "cat << 'EOF'\n# Example: git push --force origin main\nEOF"
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        }
        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)
        assert exit_code == 0, "Heredoc content should not trigger blocking"

    def test_unquoted_heredoc_marker(self, hook_path):
        """Unquoted heredoc markers should also be stripped."""
        cmd = "cat << MARKER\ngit push --force\nMARKER"
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        }
        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)
        assert exit_code == 0, "Unquoted heredoc content should not trigger"

    def test_command_before_heredoc_still_checked(self, hook_path):
        """Commands before heredoc should still be checked."""
        cmd = "git reset --hard && cat << 'EOF'\nsome content\nEOF"
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        }
        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)
        assert output is not None, "Command before heredoc should be checked"
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"

    def test_double_quoted_heredoc_marker(self, hook_path):
        """Double-quoted heredoc markers should be handled."""
        cmd = 'cat << "END"\ngit clean -fd\nEND'
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": cmd}
        }
        exit_code, stdout, stderr = run_hook(hook_path, input_data)
        output = parse_hook_output(stdout)
        assert exit_code == 0, "Double-quoted heredoc content should not trigger"
