#!/usr/bin/env python3
"""
MCP State Tracker Hook (PostToolUse) - v3
------------------------------------
Tracks agent state after MCP tool calls:
- Updates registration status after register_agent
- Tracks file reservations after file_reservation_paths
- Clears reservations after release_file_reservations

MULTI-AGENT SAFE: Uses per-agent state files based on AGENT_NAME env var.
State is stored in ~/.claude/state-{AGENT_NAME}.json

LOCKING: Uses a separate .lock file to hold exclusive lock during entire
read-modify-write cycle, avoiding TOCTOU race conditions.
"""

import json
import sys
import os
import time
import fcntl
from pathlib import Path
from contextlib import contextmanager

# Escape hatch for experienced users - bypass all state tracking
if os.environ.get("FARMHAND_SKIP_ENFORCEMENT") == "1":
    sys.exit(0)

# Per-agent state files to avoid conflicts
AGENT_NAME = os.environ.get("AGENT_NAME")
STATE_DIR = Path.home() / ".claude"

def get_state_file():
    """Get the state file path for this agent."""
    if AGENT_NAME:
        # Multi-agent: per-agent state file
        return STATE_DIR / f"state-{AGENT_NAME}.json"
    else:
        # Single-agent: legacy shared state file
        return STATE_DIR / "agent-state.json"

def get_lock_file():
    """Get the lock file path for this agent's state file."""
    state_file = get_state_file()
    return state_file.with_suffix('.lock')

@contextmanager
def state_lock():
    """Context manager for exclusive lock on state file operations.
    
    Uses a separate .lock file to hold the lock during the entire
    read-modify-write cycle, avoiding TOCTOU race conditions.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock_file = get_lock_file()
    
    # Open lock file (create if needed)
    lock_fd = open(lock_file, 'w')
    try:
        # Acquire exclusive lock (blocks until available)
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            # Release lock
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
    finally:
        lock_fd.close()

def load_state():
    """Load agent state from file."""
    state_file = get_state_file()
    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "registered": False,
        "agent_name": AGENT_NAME,  # Use env var if available
        "reservations": [],
        "issue_id": None,
        "session_start": time.time()
    }

def save_state(state):
    """Save agent state to file with atomic write."""
    state_file = get_state_file()
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then rename
    temp_file = state_file.with_suffix('.tmp')
    try:
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)
        temp_file.rename(state_file)  # Atomic rename on POSIX
    except IOError:
        if temp_file.exists():
            temp_file.unlink()

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
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

    # Use lock for entire read-modify-write cycle
    with state_lock():
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
