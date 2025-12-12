#!/usr/bin/env python3
"""
MCP State Tracker Hook (PostToolUse)
------------------------------------
Tracks agent registration and reservations after MCP tool calls.
"""

import json
import sys
import time
from pathlib import Path

STATE_FILE = Path.home() / ".claude" / "agent-state.json"

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"registered": False, "agent_name": None, "reservations": [], "session_start": time.time()}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_output = input_data.get("tool_output", {})

    # Map tool names to actions
    actions = {
        "mcp__mcp-agent-mail__register_agent": "register",
        "mcp__mcp-agent-mail__file_reservation_paths": "reserve",
        "mcp__mcp-agent-mail__release_file_reservations": "release",
        "mcp__mcp-agent-mail__macro_start_session": "macro_start",
        "register_agent": "register",
        "file_reservation_paths": "reserve",
        "release_file_reservations": "release",
        "macro_start_session": "macro_start",
    }

    action = actions.get(tool_name)
    if not action:
        sys.exit(0)

    state = load_state()

    if action in ["register", "macro_start"]:
        if isinstance(tool_output, dict):
            agent_name = tool_output.get("name") or tool_output.get("agent_name")
            if agent_name:
                state["registered"] = True
                state["agent_name"] = agent_name
                state["registration_time"] = time.time()

    if action in ["reserve", "macro_start"]:
        paths = tool_input.get("paths", [])
        if paths:
            state["reservations"].append({
                "paths": paths,
                "reason": tool_input.get("reason", ""),
                "expires_at": time.time() + tool_input.get("ttl_seconds", 3600)
            })

    if action == "release":
        state["reservations"] = []

    save_state(state)
    sys.exit(0)

if __name__ == "__main__":
    main()
