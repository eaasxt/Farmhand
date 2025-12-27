#!/usr/bin/env python3
"""
MCP State Tracker Hook (PostToolUse) - v4
------------------------------------
Tracks agent state after MCP tool calls:
- Updates registration status after register_agent
- Tracks file reservations after file_reservation_paths
- Clears reservations after release_file_reservations
- Tracks artifact trail (files created/modified/read)

ARTIFACT TRAIL: Research shows file tracking is the weakest dimension in
agent sessions (2.2-2.5/5.0 scores). This hook tracks files touched to
improve handoff quality between agents and sessions.

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
    # Consume stdin to prevent blocking the caller, then exit
    sys.stdin.read()
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

# Lock configuration
LOCK_TIMEOUT = 5.0  # seconds to wait for lock
LOCK_RETRY_DELAY = 0.1  # seconds between retry attempts
STALE_LOCK_AGE = 3600  # seconds before lock file considered stale (1 hour)


def is_lock_stale(lock_file: Path) -> bool:
    """Check if lock file is stale (process died without releasing).

    Note: flock() locks are released automatically when process dies,
    but the lock file itself persists. A very old lock file that we
    can immediately acquire indicates the holder died.
    """
    try:
        if not lock_file.exists():
            return False
        age = time.time() - lock_file.stat().st_mtime
        return age > STALE_LOCK_AGE
    except OSError:
        return False


@contextmanager
def state_lock(timeout: float = LOCK_TIMEOUT):
    """Context manager for exclusive lock on state file operations.

    Uses a separate .lock file to hold the lock during the entire
    read-modify-write cycle, avoiding TOCTOU race conditions.

    Features:
    - Timeout-based acquisition (doesn't block forever)
    - Stale lock detection and cleanup
    - Non-blocking retries with exponential backoff
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock_file = get_lock_file()

    # Check for and clean up stale lock files
    if is_lock_stale(lock_file):
        try:
            lock_file.unlink()
        except OSError:
            pass  # Another process may have cleaned it up

    # Open lock file (create if needed)
    lock_fd = open(lock_file, 'w', encoding='utf-8')
    start_time = time.time()
    acquired = False

    try:
        # Try to acquire lock with timeout
        while time.time() - start_time < timeout:
            try:
                # Non-blocking lock attempt
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                # Update lock file mtime to show we're active
                lock_file.touch()
                break
            except BlockingIOError:
                # Lock held by another process, wait and retry
                time.sleep(LOCK_RETRY_DELAY)

        if not acquired:
            # Timeout reached - proceed without lock (fail open for usability)
            # This is a hook, so we don't want to break the user's workflow
            pass

        try:
            yield
        finally:
            if acquired:
                # Release lock
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
    finally:
        lock_fd.close()

def load_state():
    """Load agent state from file."""
    state_file = get_state_file()
    if state_file.exists():
        try:
            with open(state_file, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "registered": False,
        "agent_name": AGENT_NAME,  # Use env var if available
        "reservations": [],
        "issue_id": None,
        "session_start": time.time(),
        # Artifact trail for handoff quality
        "files_created": [],
        "files_modified": [],
        "files_read": []
    }

def save_state(state):
    """Save agent state to file with atomic write."""
    state_file = get_state_file()
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Atomic write: write to temp file, then rename
    temp_file = state_file.with_suffix('.tmp')
    try:
        with open(temp_file, "w", encoding='utf-8') as f:
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

    # MCP Agent Mail tools
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

    # Artifact tracking for file operations (improves handoff quality)
    artifact_tools = {
        "Write": "created",
        "Edit": "modified",
        "Read": "read",
    }

    action = mcp_tools.get(tool_name)
    artifact_action = artifact_tools.get(tool_name)

    # Exit early if neither MCP tool nor artifact tool
    if not action and not artifact_action:
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
                # Note: macro_start_session uses "file_reservation_paths" parameter, not "paths"
                paths = tool_input.get("file_reservation_paths") or tool_input.get("paths", [])
                reason = tool_input.get("file_reservation_reason", "")
                if paths:
                    reservation = {
                        "paths": paths,
                        "reason": reason,
                        "created_at": time.time(),
                        "expires_at": time.time() + tool_input.get("file_reservation_ttl_seconds", 3600)
                    }
                    state["reservations"].append(reservation)
                save_state(state)

        # Track file artifacts for handoff quality
        if artifact_action:
            file_path = tool_input.get("file_path", "")
            if file_path:
                # Ensure artifact trail lists exist (for backwards compatibility)
                if "files_created" not in state:
                    state["files_created"] = []
                if "files_modified" not in state:
                    state["files_modified"] = []
                if "files_read" not in state:
                    state["files_read"] = []

                # Track based on operation type (deduplicated)
                if artifact_action == "created":
                    if file_path not in state["files_created"]:
                        state["files_created"].append(file_path)
                elif artifact_action == "modified":
                    if file_path not in state["files_modified"]:
                        state["files_modified"].append(file_path)
                elif artifact_action == "read":
                    # Limit reads to last 50 to avoid unbounded growth
                    if file_path not in state["files_read"]:
                        state["files_read"].append(file_path)
                        if len(state["files_read"]) > 50:
                            state["files_read"] = state["files_read"][-50:]

                save_state(state)

    sys.exit(0)

if __name__ == "__main__":
    main()
