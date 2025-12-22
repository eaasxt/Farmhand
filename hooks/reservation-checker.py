#!/usr/bin/env python3
"""
File Reservation Checker Hook
-----------------------------
Before allowing Edit/Write operations, verifies:
1. Agent is registered with MCP Agent Mail
2. Agent has reserved the file being edited
3. Reservation is still valid (not expired)

This prevents merge conflicts in multi-agent workflows.

State is tracked in ~/.claude/agent-state.json
"""

import json
import sys
import os
import fnmatch
import time
from pathlib import Path

STATE_FILE = Path.home() / ".claude" / "agent-state.json"
MCP_STORAGE = Path.home() / ".mcp_agent_mail"

def load_state():
    """Load agent state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"registered": False, "agent_name": None, "reservations": [], "issue_id": None}

def get_active_reservations():
    """
    Get active file reservations from MCP Agent Mail storage.
    Returns list of {agent_name, paths, expires_at, reason}
    """
    reservations = []
    reservations_dir = MCP_STORAGE / "reservations"

    if not reservations_dir.exists():
        return reservations

    now = time.time()

    for res_file in reservations_dir.glob("*.json"):
        try:
            with open(res_file) as f:
                data = json.load(f)
                # Check if reservation is still valid
                expires_at = data.get("expires_at", 0)
                if expires_at > now:
                    reservations.append(data)
        except (json.JSONDecodeError, IOError):
            continue

    return reservations

def check_file_reserved(file_path: str, agent_name: str, reservations: list) -> tuple:
    """
    Check if file is reserved by the given agent.
    Returns (is_reserved_by_agent, blocking_agent)
    """
    file_path = os.path.abspath(file_path)

    for res in reservations:
        paths = res.get("paths", [])
        res_agent = res.get("agent_name", "")

        for pattern in paths:
            # Handle glob patterns
            if fnmatch.fnmatch(file_path, pattern) or file_path.startswith(pattern.rstrip("*")):
                if res_agent == agent_name:
                    return (True, None)
                else:
                    return (False, res_agent)

    return (False, None)

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Edit and Write operations
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Skip checks for certain paths (hooks, temp files, etc.)
    skip_patterns = [
        "/.claude/",
        "/tmp/",
        ".pyc",
        "__pycache__",
        ".git/",
        "node_modules/",
    ]

    for pattern in skip_patterns:
        if pattern in file_path:
            sys.exit(0)

    state = load_state()

    # Check 1: Is agent registered?
    if not state.get("registered"):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": """BLOCKED: Agent not registered.

Before editing files, you must:

1. Register with MCP Agent Mail:
   register_agent(
       project_key="/home/ubuntu",
       program="claude-code",
       model="opus-4.5"
   )

2. Note your assigned name from the response (e.g., "BlueLake")

3. Reserve files before editing:
   file_reservation_paths(
       project_key="/home/ubuntu",
       agent_name="<your-assigned-name>",
       paths=["path/to/file.py"],
       ttl_seconds=3600,
       exclusive=True,
       reason="<issue-id>"
   )

See ~/CLAUDE.md for the complete workflow."""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    agent_name = state.get("agent_name")

    # Check 2: Does agent have this file reserved?
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

Options:
1. Wait for {blocking_agent} to release the file
2. Send a message to coordinate:
   send_message(
       project_key="/home/ubuntu",
       sender_name="{agent_name}",
       to=["{blocking_agent}"],
       subject="File access request",
       body_md="Need access to {file_path}..."
   )
3. Check your inbox for updates:
   fetch_inbox(project_key="/home/ubuntu", agent_name="{agent_name}")"""
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

You must reserve files before editing:

file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="{agent_name}",
    paths=["{file_path}"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"  # e.g., "ubuntu-42"
)

Or use a glob pattern:
    paths=["src/**/*.py"]

See ~/CLAUDE.md for the complete workflow."""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # All checks passed
    sys.exit(0)

if __name__ == "__main__":
    main()
