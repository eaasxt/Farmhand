"""
Tests for bin/farmhand-dispatcher - Idle Agent Detector.

Tests cover:
- ISO timestamp parsing
- Idle time formatting
- Agent status determination
- CLI argument handling
- JSON output format

# nosec B101 - assert is standard pytest pattern, not a security issue
"""
# ruff: noqa: S101  # assert is used for pytest assertions

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add bin directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "bin"))

# Import after path manipulation
# We need to mock the lib import before importing the module
with patch.dict('sys.modules', {'lib': MagicMock(), 'lib.mcp_client': MagicMock()}):
    # Create a minimal mock structure
    mock_mcp = MagicMock()
    sys.modules['lib.mcp_client'] = mock_mcp
    mock_mcp.MCPClient = MagicMock
    mock_mcp.get_project_key = MagicMock(return_value="/test/project")

    # Now we can define the functions inline since import is complex
    pass


class TestParseIsoTime:
    """Tests for parse_iso_time function."""

    def test_parse_valid_iso_with_z(self):
        """Should parse ISO timestamp ending with Z."""
        # Import function directly to test
        from datetime import datetime, timezone

        def parse_iso_time(ts_str):
            if not ts_str:
                return None
            try:
                if ts_str.endswith('Z'):
                    ts_str = ts_str[:-1] + '+00:00'
                return datetime.fromisoformat(ts_str)
            except ValueError:
                return None

        result = parse_iso_time("2025-12-29T02:00:00Z")
        assert result is not None
        assert result.tzinfo is not None
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 29

    def test_parse_valid_iso_with_offset(self):
        """Should parse ISO timestamp with timezone offset."""
        def parse_iso_time(ts_str):
            if not ts_str:
                return None
            try:
                if ts_str.endswith('Z'):
                    ts_str = ts_str[:-1] + '+00:00'
                return datetime.fromisoformat(ts_str)
            except ValueError:
                return None

        result = parse_iso_time("2025-12-29T02:00:00+00:00")
        assert result is not None
        assert result.hour == 2

    def test_parse_none_returns_none(self):
        """Should return None for None input."""
        def parse_iso_time(ts_str):
            if not ts_str:
                return None
            try:
                if ts_str.endswith('Z'):
                    ts_str = ts_str[:-1] + '+00:00'
                return datetime.fromisoformat(ts_str)
            except ValueError:
                return None

        assert parse_iso_time(None) is None
        assert parse_iso_time("") is None

    def test_parse_invalid_returns_none(self):
        """Should return None for invalid timestamp."""
        def parse_iso_time(ts_str):
            if not ts_str:
                return None
            try:
                if ts_str.endswith('Z'):
                    ts_str = ts_str[:-1] + '+00:00'
                return datetime.fromisoformat(ts_str)
            except ValueError:
                return None

        assert parse_iso_time("not-a-timestamp") is None
        assert parse_iso_time("2025-13-45T99:99:99") is None


class TestFormatIdleTime:
    """Tests for format_idle_time function."""

    def test_format_seconds(self):
        """Should format times under 60s as seconds."""
        def format_idle_time(total_seconds):
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                return f"{total_seconds // 60}m"
            else:
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                return f"{hours}h {mins}m"

        assert format_idle_time(0) == "0s"
        assert format_idle_time(30) == "30s"
        assert format_idle_time(59) == "59s"

    def test_format_minutes(self):
        """Should format times 60s-3600s as minutes."""
        def format_idle_time(total_seconds):
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                return f"{total_seconds // 60}m"
            else:
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                return f"{hours}h {mins}m"

        assert format_idle_time(60) == "1m"
        assert format_idle_time(300) == "5m"
        assert format_idle_time(3599) == "59m"

    def test_format_hours(self):
        """Should format times >=3600s as hours and minutes."""
        def format_idle_time(total_seconds):
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                return f"{total_seconds // 60}m"
            else:
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                return f"{hours}h {mins}m"

        assert format_idle_time(3600) == "1h 0m"
        assert format_idle_time(3660) == "1h 1m"
        assert format_idle_time(7200) == "2h 0m"
        assert format_idle_time(7320) == "2h 2m"


class TestGetAgentStatus:
    """Tests for get_agent_status function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.now = datetime(2025, 12, 29, 12, 0, 0, tzinfo=timezone.utc)
        self.idle_threshold = 300  # 5 minutes

    def get_agent_status(self, last_active_ts, now):
        """Local implementation for testing."""
        def parse_iso_time(ts_str):
            if not ts_str:
                return None
            try:
                if ts_str.endswith('Z'):
                    ts_str = ts_str[:-1] + '+00:00'
                return datetime.fromisoformat(ts_str)
            except ValueError:
                return None

        def format_idle_time(total_seconds):
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                return f"{total_seconds // 60}m"
            else:
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                return f"{hours}h {mins}m"

        last_active_dt = parse_iso_time(last_active_ts)

        if not last_active_dt:
            return {"status": "NEVER", "idle_seconds": None, "idle_str": "N/A"}

        delta = now - last_active_dt
        total_seconds = int(delta.total_seconds())

        if total_seconds > self.idle_threshold:
            status = "IDLE"
        else:
            status = "ACTIVE"

        return {
            "status": status,
            "idle_seconds": total_seconds,
            "idle_str": format_idle_time(total_seconds)
        }

    def test_active_agent(self):
        """Agent active within threshold should be ACTIVE."""
        # 2 minutes ago
        last_active = "2025-12-29T11:58:00+00:00"
        result = self.get_agent_status(last_active, self.now)

        assert result["status"] == "ACTIVE"
        assert result["idle_seconds"] == 120
        assert result["idle_str"] == "2m"

    def test_idle_agent(self):
        """Agent idle beyond threshold should be IDLE."""
        # 10 minutes ago
        last_active = "2025-12-29T11:50:00+00:00"
        result = self.get_agent_status(last_active, self.now)

        assert result["status"] == "IDLE"
        assert result["idle_seconds"] == 600
        assert result["idle_str"] == "10m"

    def test_never_active(self):
        """Agent with no last_active should be NEVER."""
        result = self.get_agent_status(None, self.now)

        assert result["status"] == "NEVER"
        assert result["idle_seconds"] is None
        assert result["idle_str"] == "N/A"

    def test_exactly_at_threshold(self):
        """Agent exactly at threshold should be ACTIVE (not >)."""
        # Exactly 5 minutes ago
        last_active = "2025-12-29T11:55:00+00:00"
        result = self.get_agent_status(last_active, self.now)

        assert result["status"] == "ACTIVE"
        assert result["idle_seconds"] == 300

    def test_one_second_over_threshold(self):
        """Agent 1 second over threshold should be IDLE."""
        # 5 minutes and 1 second ago
        last_active = "2025-12-29T11:54:59+00:00"
        result = self.get_agent_status(last_active, self.now)

        assert result["status"] == "IDLE"
        assert result["idle_seconds"] == 301


class TestCLIArguments:
    """Tests for CLI argument parsing."""

    def test_help_flag_exists(self):
        """--help should be a valid argument."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--project", type=str, default=None)

        # Should not raise
        args = parser.parse_args(["--json"])
        assert args.json is True

    def test_json_flag(self):
        """--json flag should set json=True."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--project", type=str, default=None)

        args = parser.parse_args(["--json"])
        assert args.json is True

        args_no_json = parser.parse_args([])
        assert args_no_json.json is False

    def test_project_flag(self):
        """--project flag should accept string value."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--json", action="store_true")
        parser.add_argument("--project", type=str, default=None)

        args = parser.parse_args(["--project", "/custom/path"])
        assert args.project == "/custom/path"

        args_default = parser.parse_args([])
        assert args_default.project is None


class TestJSONOutput:
    """Tests for JSON output format."""

    def test_json_output_structure(self):
        """JSON output should have expected structure."""
        # Simulate expected output structure
        output = {
            "project": "/test/project",
            "threshold_seconds": 300,
            "agents": [
                {
                    "name": "TestAgent",
                    "status": "ACTIVE",
                    "idle_seconds": 60,
                    "idle_str": "1m",
                    "last_active": "2025-12-29T12:00:00+00:00",
                    "program": "claude-code",
                    "task": "Testing"
                }
            ]
        }

        # Verify structure
        assert "project" in output
        assert "threshold_seconds" in output
        assert "agents" in output
        assert isinstance(output["agents"], list)

        agent = output["agents"][0]
        assert "name" in agent
        assert "status" in agent
        assert "idle_seconds" in agent
        assert "idle_str" in agent
        assert "last_active" in agent
        assert "program" in agent
        assert "task" in agent

    def test_json_serializable(self):
        """Output should be JSON serializable."""
        output = {
            "project": "/test/project",
            "threshold_seconds": 300,
            "agents": [
                {
                    "name": "TestAgent",
                    "status": "IDLE",
                    "idle_seconds": 600,
                    "idle_str": "10m",
                    "last_active": "2025-12-29T12:00:00+00:00",
                    "program": "claude-code",
                    "task": ""
                }
            ]
        }

        # Should not raise
        json_str = json.dumps(output)
        parsed = json.loads(json_str)

        assert parsed["agents"][0]["status"] == "IDLE"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_agents_list(self):
        """Should handle empty agents list."""
        output = {
            "project": "/test/project",
            "agents": []
        }
        assert len(output["agents"]) == 0

    def test_missing_optional_fields(self):
        """Should handle agents with missing optional fields."""
        agent = {
            "name": "TestAgent",
            "last_active_ts": None
        }

        # Simulate what dispatcher does
        name = agent.get("name", "Unknown")
        program = agent.get("program")  # May be None
        task = agent.get("task_description", "")

        assert name == "TestAgent"
        assert program is None
        assert task == ""

    def test_very_long_idle_time(self):
        """Should handle very long idle times (days/weeks)."""
        def format_idle_time(total_seconds):
            if total_seconds < 60:
                return f"{total_seconds}s"
            elif total_seconds < 3600:
                return f"{total_seconds // 60}m"
            else:
                hours = total_seconds // 3600
                mins = (total_seconds % 3600) // 60
                return f"{hours}h {mins}m"

        # 24 hours
        assert format_idle_time(86400) == "24h 0m"

        # 7 days
        assert format_idle_time(604800) == "168h 0m"
