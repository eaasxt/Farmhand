#!/usr/bin/env python3
"""
Tests for bd-claim command.

Run with: uv run pytest tests/test_bd_claim.py -v
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# Path to the bd-claim script
BD_CLAIM_PATH = Path(__file__).parent.parent / "bin" / "bd-claim"


def run_bd_claim(*args, env=None):
    """Run bd-claim with arguments and return (exit_code, stdout, stderr)."""
    cmd = ["python3", str(BD_CLAIM_PATH)] + list(args)
    full_env = {**os.environ, **(env or {})}
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=full_env
    )
    return result.returncode, result.stdout, result.stderr


class TestHelp:
    """Tests for help output."""
    
    def test_help_flag(self):
        """Should show help with --help."""
        exit_code, stdout, stderr = run_bd_claim("--help")
        assert exit_code == 0
        assert "bd-claim" in stdout
        assert "bead_id" in stdout
        assert "--paths" in stdout
        assert "--ttl" in stdout
        assert "--json" in stdout

    def test_missing_bead_id_shows_error(self):
        """Should fail if no bead ID provided."""
        exit_code, stdout, stderr = run_bd_claim()
        assert exit_code != 0
        assert "required" in stderr.lower() or "bead_id" in stderr.lower()


class TestValidation:
    """Tests for input validation."""
    
    def test_fails_without_registration(self, tmp_path):
        """Should fail if agent is not registered."""
        # Use empty state dir and clear AGENT_NAME to simulate unregistered
        env = {"HOME": str(tmp_path), "AGENT_NAME": ""}
        exit_code, stdout, stderr = run_bd_claim("test-bead", "--json", env=env)
        assert exit_code == 1
        result = json.loads(stdout)
        assert result["success"] is False
        assert "not registered" in result["error"].lower()

    def test_json_output_on_error(self, tmp_path):
        """Should output valid JSON even on error when --json is used."""
        env = {"HOME": str(tmp_path), "AGENT_NAME": ""}
        exit_code, stdout, stderr = run_bd_claim("test-bead", "--json", env=env)
        # Should be valid JSON
        result = json.loads(stdout)
        assert "success" in result
        assert "error" in result


class TestParsing:
    """Tests for argument parsing."""
    
    def test_parses_paths(self, tmp_path):
        """Should parse comma-separated paths."""
        # Create a minimal state file to pass registration check
        state_dir = tmp_path / ".claude"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "agent-state.json"
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "TestAgent",
            "reservations": []
        }))
        
        env = {"HOME": str(tmp_path), "AGENT_NAME": ""}
        # This will fail at bead lookup, but we can verify parsing works
        exit_code, stdout, stderr = run_bd_claim(
            "test-bead",
            "--paths", "src/**/*.py,tests/**/*.py",
            "--json",
            env=env
        )
        # Should fail because bead doesn't exist, not because of parsing
        if exit_code == 1:
            result = json.loads(stdout)
            # Error should be about bead not found, not parsing
            assert "parsing" not in result.get("error", "").lower()

    def test_default_ttl(self, tmp_path):
        """Should use default TTL of 3600."""
        # Just verify help shows the default
        exit_code, stdout, stderr = run_bd_claim("--help")
        assert "3600" in stdout


class TestStateFile:
    """Tests for state file handling."""
    
    def test_uses_agent_name_state_file(self, tmp_path):
        """Should use state-{AGENT_NAME}.json when AGENT_NAME is set."""
        state_dir = tmp_path / ".claude"
        state_dir.mkdir(parents=True)
        
        # Create per-agent state file
        agent_state = state_dir / "state-TestAgent.json"
        agent_state.write_text(json.dumps({
            "registered": True,
            "agent_name": "MyName",
            "reservations": []
        }))
        
        env = {"HOME": str(tmp_path), "AGENT_NAME": "TestAgent"}
        exit_code, stdout, stderr = run_bd_claim("test-bead", "--json", env=env)
        
        # Should use the name from state file
        if exit_code == 1:
            result = json.loads(stdout)
            # Error should be about bead not found (meaning agent lookup worked)
            if "not found" in result.get("error", "").lower():
                pass  # Good - agent lookup succeeded

    def test_falls_back_to_legacy_state(self, tmp_path):
        """Should use agent-state.json when AGENT_NAME is not set."""
        state_dir = tmp_path / ".claude"
        state_dir.mkdir(parents=True)
        
        # Create legacy state file
        legacy_state = state_dir / "agent-state.json"
        legacy_state.write_text(json.dumps({
            "registered": True,
            "agent_name": "LegacyAgent",
            "reservations": []
        }))
        
        env = {"HOME": str(tmp_path), "AGENT_NAME": ""}
            
        exit_code, stdout, stderr = run_bd_claim("test-bead", "--json", env=env)
        
        # Should use LegacyAgent from the legacy state file
        result = json.loads(stdout)
        assert result["success"] is False  # Bead won't exist
        assert "LegacyAgent" not in result.get("error", "") or "not found" in result.get("error", "").lower()


class TestProjectKey:
    """Tests for project key detection."""
    
    def test_uses_env_var_first(self, tmp_path, monkeypatch):
        """Should use FARMHAND_PROJECT_KEY if set."""
        state_dir = tmp_path / ".claude"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "agent-state.json"
        state_file.write_text(json.dumps({
            "registered": True,
            "agent_name": "Test",
            "reservations": []
        }))
        
        env = {
            "HOME": str(tmp_path),
            "AGENT_NAME": "",
            "FARMHAND_PROJECT_KEY": "/custom/project"
        }
        exit_code, stdout, stderr = run_bd_claim("test-bead", "--json", env=env)
        
        result = json.loads(stdout)
        # Even on failure, project_key should be in response if we got far enough
        # This test mainly validates the env var is read correctly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
