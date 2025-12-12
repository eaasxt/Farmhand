#!/usr/bin/env python3
"""
File Reservation Checker Hook (PreToolUse)
------------------------------------------
Blocks Edit/Write without registration and file reservation.
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
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"registered": False, "agent_name": None, "reservations": []}

def get_active_reservations():
    reservations = []
    reservations_dir = MCP_STORAGE / "reservations"
    if not reservations_dir.exists():
        return reservations

    now = time.time()
    for res_file in reservations_dir.glob("*.json"):
        try:
            with open(res_file) as f:
                data = json.load(f)
                if data.get("expires_at", 0) > now:
                    reservations.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return reservations

def check_file_reserved(file_path: str, agent_name: str, reservations: list):
    file_path = os.path.abspath(file_path)
    for res in reservations:
        for pattern in res.get("paths", []):
            if fnmatch.fnmatch(file_path, pattern) or file_path.startswith(pattern.rstrip("*")):
                if res.get("agent_name") == agent_name:
                    return (True, None)
                return (False, res.get("agent_name"))
    return (False, None)

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

    # Skip infrastructure paths
    skip_patterns = ["/.claude/", "/tmp/", ".pyc", "__pycache__", ".git/", "node_modules/"]
    for pattern in skip_patterns:
        if pattern in file_path:
            sys.exit(0)

    state = load_state()

    # Check registration
    if not state.get("registered"):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": """BLOCKED: Agent not registered.

First, register with MCP Agent Mail:

register_agent(
    project_key="$HOME",
    program="claude-code",
    model="opus-4.5"
)

Then reserve files before editing. See ~/CLAUDE.md"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    agent_name = state.get("agent_name")
    reservations = get_active_reservations()
    is_reserved, blocking_agent = check_file_reserved(file_path, agent_name, reservations)

    if blocking_agent:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: File reserved by {blocking_agent}.

File: {file_path}

Options:
1. Message them: send_message(..., to=["{blocking_agent}"], ...)
2. Wait and check: fetch_inbox(...)"""
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

Reserve before editing:

file_reservation_paths(
    project_key="$HOME",
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

    sys.exit(0)

if __name__ == "__main__":
    main()
