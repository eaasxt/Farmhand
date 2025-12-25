"""
Tests for obs-mask observation masking utility.

This utility stores large tool outputs to session artifacts and returns
summaries, reducing context consumption by 60-80%.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestObsMask:
    """Test cases for observation masking utility."""

    @pytest.fixture
    def obs_mask_path(self):
        """Path to the obs-mask utility."""
        return Path(__file__).parent.parent / "bin" / "obs-mask"

    @pytest.fixture
    def mock_home(self, tmp_path):
        """Create a mock home directory."""
        mock = tmp_path / "home"
        mock.mkdir()
        return mock

    def run_obs_mask(self, obs_mask_path, input_text, args=None, env=None):
        """Run obs-mask with given input and return output."""
        cmd = [sys.executable, str(obs_mask_path)]
        if args:
            cmd.extend(args)

        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            env=env or os.environ
        )
        return result.returncode, result.stdout, result.stderr

    def test_small_output_passes_through(self, obs_mask_path):
        """Small outputs under threshold should pass through unchanged."""
        input_text = "Small output here"

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100"]
        )

        assert code == 0
        assert stdout == input_text

    def test_large_output_gets_masked(self, obs_mask_path, mock_home):
        """Large outputs over threshold should be masked."""
        # Create 10000 char output
        input_text = "x" * 10000

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100", "--label", "test"],
            env=env
        )

        assert code == 0
        assert "[MASKED]" in stdout
        assert "stored to:" in stdout
        assert "Summary:" in stdout

    def test_artifact_file_created(self, obs_mask_path, mock_home):
        """Masked output should create artifact file."""
        input_text = "y" * 10000

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100", "--label", "artifact-test"],
            env=env
        )

        assert code == 0

        # Check artifact was created
        sessions_dir = mock_home / ".claude" / "sessions"
        assert sessions_dir.exists()

        # Find artifact file
        artifacts = list(sessions_dir.glob("*/artifacts/artifact-test-*.txt"))
        assert len(artifacts) == 1
        assert artifacts[0].read_text() == input_text

    def test_json_output_format(self, obs_mask_path, mock_home):
        """--json flag should output structured JSON."""
        input_text = "z" * 10000

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100", "--json"],
            env=env
        )

        assert code == 0

        result = json.loads(stdout)
        assert result["masked"] is True
        assert "artifact_path" in result
        assert result["original_tokens"] > 100
        assert result["original_chars"] == 10000

    def test_summary_only_flag(self, obs_mask_path, mock_home):
        """--summary-only should not include preview."""
        input_text = "a" * 10000

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100", "--summary-only"],
            env=env
        )

        assert code == 0
        assert "[MASKED]" in stdout
        assert "Preview" not in stdout

    def test_custom_preview_chars(self, obs_mask_path, mock_home):
        """--preview-chars should control preview length."""
        input_text = "b" * 10000

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100", "--preview-chars", "100"],
            env=env
        )

        assert code == 0
        assert "Preview (first 100 chars)" in stdout

    def test_ubs_summary_extraction(self, obs_mask_path, mock_home):
        """Should extract severity counts from UBS-like output."""
        input_text = """
        Critical: Found SQL injection vulnerability
        High: Missing input validation
        High: XSS vulnerability
        Medium: Unused variable
        Low: Console.log statement
        """ * 100  # Make it large enough

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100", "--label", "ubs"],
            env=env
        )

        assert code == 0
        # Should have extracted severity counts
        assert "critical" in stdout.lower() or "high" in stdout.lower()

    def test_threshold_boundary(self, obs_mask_path, mock_home):
        """Output exactly at threshold should pass through."""
        # ~2000 tokens = ~8000 chars
        input_text = "c" * 8000  # Exactly 2000 tokens

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "2000"],
            env=env
        )

        assert code == 0
        # Should pass through (at threshold, not over)
        assert stdout == input_text

    def test_custom_session_id(self, obs_mask_path, mock_home):
        """--session should use custom session ID."""
        input_text = "d" * 10000

        env = os.environ.copy()
        env["HOME"] = str(mock_home)

        code, stdout, stderr = self.run_obs_mask(
            obs_mask_path,
            input_text,
            ["--threshold", "100", "--session", "custom-session-123"],
            env=env
        )

        assert code == 0

        # Check artifact in custom session
        custom_session = mock_home / ".claude" / "sessions" / "custom-session-123" / "artifacts"
        assert custom_session.exists()
        assert len(list(custom_session.glob("*.txt"))) == 1
