#!/usr/bin/env python3
"""
MCP State Tracker Hook (PostToolUse)
------------------------------------
Tracks agent state after MCP tool calls:
- Updates registration status after register_agent
- Tracks file reservations after file_reservation_paths
- Clears reservations after release_file_reservations

State is stored in ~/.claude/agent-state.json
"""

import json
import sys
import os
import time
from pathlib import Path

STATE_FILE = Path.home() / ".claude" / "agent-state.json"

def load_state():
    """Load agent state from file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "registered": False,
        "agent_name": None,
        "reservations": [],
        "issue_id": None,
        "session_start": time.time()
    }

def save_state(state):
    """Save agent state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        sys.exit(0)  # Non-blocking on parse errors

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_output = input_data.get("tool_output", {})

    # Only track MCP Agent Mail tools
    mcp_tools = {
        "mcp__mcp-agent-mail__register_agent": "register",
        "mcp__mcp-agent-mail__file_reservation_paths": "reserve",
        "mcp__mcp-agent-mail__release_file_reservations": "release",
        "mcp__mcp-agent-mail__macro_start_session": "macro_start",
        # Also handle direct function calls if exposed differently
        "register_agent": "register",
        "file_reservation_paths": "reserve",
        "release_file_reservations": "release",
        "macro_start_session": "macro_start",
    }

    action = mcp_tools.get(tool_name)
    if not action:
        sys.exit(0)

    state = load_state()

    if action == "register":
        # Extract agent name from response
        if isinstance(tool_output, dict):
            agent_name = tool_output.get("name") or tool_output.get("agent_name")
            if agent_name:
                state["registered"] = True
                state["agent_name"] = agent_name
                state["registration_time"] = time.time()
                save_state(state)

    elif action == "reserve":
        # Track reservation
        paths = tool_input.get("paths", [])
        reason = tool_input.get("reason", "")
        ttl = tool_input.get("ttl_seconds", 3600)

        if paths:
            reservation = {
                "paths": paths,
                "reason": reason,
                "created_at": time.time(),
                "expires_at": time.time() + ttl
            }
            state["reservations"].append(reservation)
            if reason and not state.get("issue_id"):
                state["issue_id"] = reason
            save_state(state)

    elif action == "release":
        # Clear reservations
        state["reservations"] = []
        save_state(state)

    elif action == "macro_start":
        # Macro handles register + reserve
        if isinstance(tool_output, dict):
            agent_name = tool_output.get("name") or tool_output.get("agent_name")
            if agent_name:
                state["registered"] = True
                state["agent_name"] = agent_name
                state["registration_time"] = time.time()

            # Also track any reservations from macro
            paths = tool_input.get("paths", [])
            reason = tool_input.get("reason", "")
            if paths:
                reservation = {
                    "paths": paths,
                    "reason": reason,
                    "created_at": time.time(),
                    "expires_at": time.time() + tool_input.get("ttl_seconds", 3600)
                }
                state["reservations"].append(reservation)
            save_state(state)

    sys.exit(0)

if __name__ == "__main__":
    main()
