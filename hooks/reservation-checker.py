#!/usr/bin/env python3
"""
File Reservation Checker Hook (v4 - Queries MCP Agent Mail SQLite database)
---------------------------------------------------------------------------
Queries the MCP Agent Mail SQLite database directly for file reservations.
Uses AGENT_NAME environment variable or falls back to agent-state.json.

Per MCP Agent Mail docs:
"set AGENT_NAME in your environment so the pre-commit guard can block
commits that conflict with others' active exclusive file reservations."
"""

import json
import sys
import os
import fnmatch
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Per-agent state files to avoid conflicts
AGENT_NAME = os.environ.get("AGENT_NAME")
STATE_DIR = Path.home() / ".claude"
MCP_DB_PATH = Path.home() / "mcp_agent_mail" / "storage.sqlite3"

def get_state_file():
    """Get the state file path for this agent."""
    if AGENT_NAME:
        # Multi-agent: per-agent state file
        return STATE_DIR / f"state-{AGENT_NAME}.json"
    else:
        # Single-agent: legacy shared state file
        return STATE_DIR / "agent-state.json"

def get_agent_name():
    """Get agent name from environment (preferred) or per-agent state file (fallback)."""
    # Preferred: environment variable
    if AGENT_NAME:
        return AGENT_NAME

    # Fallback: per-agent state file
    state_file = get_state_file()
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
                return state.get("agent_name")
        except (json.JSONDecodeError, IOError):
            pass
    return None

def is_registered():
    """Check if agent is registered (env var set OR state file says so)."""
    if AGENT_NAME:
        return True

    state_file = get_state_file()
    if state_file.exists():
        try:
            with open(state_file) as f:
                state = json.load(f)
                return state.get("registered", False)
        except (json.JSONDecodeError, IOError):
            pass
    return False

def get_active_reservations():
    """Get all active reservations from MCP Agent Mail SQLite database."""
    reservations = []

    if not MCP_DB_PATH.exists():
        return reservations

    try:
        conn = sqlite3.connect(str(MCP_DB_PATH), timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get active (non-released, non-expired) reservations
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT
                fr.path_pattern,
                fr.exclusive,
                fr.reason,
                fr.expires_ts,
                a.name as agent_name,
                p.human_key as project_key
            FROM file_reservations fr
            JOIN agents a ON fr.agent_id = a.id
            JOIN projects p ON fr.project_id = p.id
            WHERE fr.released_ts IS NULL
              AND fr.expires_ts > ?
        """, (now,))

        for row in cursor.fetchall():
            reservations.append({
                "agent_name": row["agent_name"],
                "paths": [row["path_pattern"]],
                "exclusive": bool(row["exclusive"]),
                "reason": row["reason"],
                "project_key": row["project_key"],
                "expires_ts": row["expires_ts"]
            })

        conn.close()
    except sqlite3.Error:
        # If database is locked or inaccessible, fail open (allow edits)
        pass

    return reservations

def file_matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if file matches a glob pattern."""
    if "**" in pattern:
        base = pattern.split("**")[0].rstrip("/")
        if file_path.startswith(base + "/") or file_path == base:
            return True
    
    if fnmatch.fnmatch(file_path, pattern):
        return True
    
    pattern_dir = pattern.rstrip("/*")
    if file_path.startswith(pattern_dir + "/"):
        return True
    
    return False

def check_file_reserved(file_path: str, agent_name: str, reservations: list) -> tuple:
    """
    Check if file is reserved by the given agent.
    Returns (is_reserved_by_agent, blocking_agent_or_none)
    """
    file_path = os.path.abspath(file_path)
    
    for res in reservations:
        res_agent = res.get("agent_name", "")
        for pattern in res.get("paths", []):
            if file_matches_pattern(file_path, pattern):
                if res_agent.lower() == agent_name.lower():
                    return (True, None)  # Reserved by this agent
                else:
                    return (False, res_agent)  # Reserved by another agent
    
    return (False, None)  # Not reserved by anyone

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Skip certain paths (including mcp_agent_mail so agents can manage their own reservations)
    skip_patterns = ["/.claude/", "/.local/bin/", "/tmp/", ".pyc", "__pycache__", ".git/", "node_modules/", "/.mcp_agent_mail/"]
    for pattern in skip_patterns:
        if pattern in file_path:
            sys.exit(0)

    # Check registration
    if not is_registered():
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": """BLOCKED: Agent not registered.

Set AGENT_NAME environment variable, or call register_agent() first.

Option 1 (preferred): Set env var before launching agent:
  export AGENT_NAME="YourAgentName"
  claude

Option 2: Register via MCP:
  register_agent(project_key="/home/ubuntu", program="claude-code", model="opus-4.5")

See ~/CLAUDE.md for details."""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    agent_name = get_agent_name()
    reservations = get_active_reservations()
    is_reserved, blocking_agent = check_file_reserved(file_path, agent_name, reservations)

    if blocking_agent:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: File reserved by another agent.

File: {file_path}
Reserved by: {blocking_agent}
Your agent: {agent_name}

Wait for {blocking_agent} to release, or coordinate via Agent Mail."""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    if not is_reserved:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: File not reserved.

File: {file_path}
Agent: {agent_name}

Reserve before editing:
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="{agent_name}",
    paths=["{file_path}"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # All checks passed
    sys.exit(0)

if __name__ == "__main__":
    main()
