#!/usr/bin/env python3
"""
File Reservation Checker Hook (v7 - Fixed glob pattern matching)
----------------------------------------------------------------------
Queries the MCP Agent Mail SQLite database directly for file reservations.

State file logic (matches mcp-state-tracker.py and session-init.py):
- When AGENT_NAME is set: uses state-{AGENT_NAME}.json (multi-agent)
- When AGENT_NAME is not set: uses agent-state.json (single-agent)

Agent name resolution (in order):
1. State file (set by mcp-state-tracker when registering via MCP)
2. AGENT_NAME env var (for multi-agent ntm scenarios, must be valid)
3. None (not registered)

This ensures the MCP-assigned name (e.g., "GreenSnow") is used, not garbage
env vars like "%17".
"""

import json
import sys
import os
import fnmatch
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path


class DatabaseUnavailableError(Exception):
    """Raised when database cannot be accessed after retries."""
    pass


# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 0.1  # seconds (exponential backoff base)

# Configuration
AGENT_NAME_ENV = os.environ.get("AGENT_NAME")
STATE_DIR = Path.home() / ".claude"
MCP_DB_PATH = Path.home() / "mcp_agent_mail" / "storage.sqlite3"

# Valid agent name pattern: alphanumeric, may contain underscores/hyphens
VALID_AGENT_NAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_-]*$')

def is_valid_agent_name(name):
    """Check if agent name looks valid (not URL-encoded garbage)."""
    if not name:
        return False
    return bool(VALID_AGENT_NAME_PATTERN.match(name))

def get_state_file():
    """Get the state file path for this agent (matches mcp-state-tracker.py)."""
    if AGENT_NAME_ENV:
        # Multi-agent: per-agent state file
        return STATE_DIR / f"state-{AGENT_NAME_ENV}.json"
    else:
        # Single-agent: legacy shared state file
        return STATE_DIR / "agent-state.json"

def get_state_from_file():
    """Get agent state from the appropriate state file."""
    state_file = get_state_file()
    if state_file.exists():
        try:
            with open(state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def get_agent_name():
    """
    Get agent name with proper priority:
    1. Registered name from agent-state.json (set by MCP registration)
    2. Valid AGENT_NAME env var (for multi-agent scenarios)
    """
    # Priority 1: Check agent-state.json for registered name
    state = get_state_from_file()
    if state.get("registered") and state.get("agent_name"):
        return state["agent_name"]

    # Priority 2: Valid AGENT_NAME env var (multi-agent scenario)
    if AGENT_NAME_ENV and is_valid_agent_name(AGENT_NAME_ENV):
        return AGENT_NAME_ENV

    return None

def is_registered():
    """Check if agent is registered."""
    # Check agent-state.json first
    state = get_state_from_file()
    if state.get("registered"):
        return True

    # Check if valid AGENT_NAME is set (multi-agent scenario)
    if AGENT_NAME_ENV and is_valid_agent_name(AGENT_NAME_ENV):
        return True

    return False

def get_active_reservations():
    """
    Get all active reservations from MCP Agent Mail SQLite database.

    Uses retry logic with exponential backoff. Raises DatabaseUnavailableError
    if database cannot be accessed after all retries (fail-closed behavior).
    """
    reservations = []

    if not MCP_DB_PATH.exists():
        # No database = no reservations (this is fine, not an error)
        return reservations

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            conn = sqlite3.connect(str(MCP_DB_PATH), timeout=30.0)
            # Enable WAL mode for better concurrency with multiple agents
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=30000')
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
            return reservations

        except sqlite3.OperationalError as e:
            last_error = e
            # Retry on lock/busy errors
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                    continue
            # Non-retryable error
            raise DatabaseUnavailableError(f"Database error: {e}") from e

        except sqlite3.Error as e:
            # Other SQLite errors - fail closed
            raise DatabaseUnavailableError(f"Database error: {e}") from e

    # All retries exhausted
    raise DatabaseUnavailableError(
        f"Database unavailable after {MAX_RETRIES} retries. Last error: {last_error}"
    )

def file_matches_pattern(file_path: str, pattern: str) -> bool:
    """
    Check if file matches a glob pattern, with proper ** support.

    Handles:
    - /home/user/project/** (all files under project)
    - /home/user/project/**/*.py (all .py files under project)
    - src/*.js (single-level wildcard)
    - exact/path/file.py (exact match)
    """
    file_path = os.path.abspath(file_path)

    # Handle ** patterns (match any directory depth)
    if "**" in pattern:
        # Split into prefix and suffix around **
        parts = pattern.split("**", 1)
        prefix = parts[0].rstrip("/")
        suffix = parts[1].lstrip("/") if len(parts) > 1 else ""

        # File must be under the prefix directory
        if prefix:
            if not (file_path.startswith(prefix + "/") or file_path == prefix):
                return False

        # If no suffix (e.g., "src/**"), any file under prefix matches
        if not suffix:
            return True

        # Get relative path from prefix
        if prefix:
            rel_path = file_path[len(prefix):].lstrip("/")
        else:
            rel_path = file_path.lstrip("/")

        # For suffix like "*.py", match the filename only
        if "/" not in suffix:
            return fnmatch.fnmatch(os.path.basename(file_path), suffix)

        # For complex suffixes (e.g., "test/*.py"), match relative path
        # Try direct match and also with intermediate directories
        if fnmatch.fnmatch(rel_path, suffix):
            return True
        # Try matching with wildcarded intermediate paths
        parts_to_match = suffix.split("/")
        rel_parts = rel_path.split("/")
        if len(rel_parts) >= len(parts_to_match):
            # Check if suffix matches the end of rel_path
            suffix_match = "/".join(rel_parts[-len(parts_to_match):])
            if fnmatch.fnmatch(suffix_match, suffix):
                return True
        return False

    # Standard fnmatch for non-** patterns (e.g., "src/*.js")
    if fnmatch.fnmatch(file_path, pattern):
        return True

    # Directory prefix matching (e.g., "src/*" should match "src/utils/foo.py")
    # This handles patterns where * should match subdirectories too
    pattern_dir = pattern.rstrip("/*")
    if pattern_dir and file_path.startswith(pattern_dir + "/"):
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
    # Escape hatch for experienced users - bypass all enforcement
    if os.environ.get("FARMHAND_SKIP_ENFORCEMENT") == "1":
        sys.exit(0)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Fail open on parse errors (don't block user workflow)
        sys.exit(0)

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
        home_dir = str(Path.home())
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: Agent not registered.

To fix, call register_agent() first:

```python
register_agent(
    project_key="{home_dir}",
    program="claude-code",
    model="opus-4.5"
)
```

Or set AGENT_NAME before launching:
```bash
export AGENT_NAME="YourAgentName"
claude
```

Quick recovery (if registered but state lost):
```bash
bd-cleanup --reset-state
```"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    agent_name = get_agent_name()

    # Try to get reservations - fail closed if database unavailable
    try:
        reservations = get_active_reservations()
    except DatabaseUnavailableError as e:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: Cannot verify file reservations.

Database temporarily unavailable: {e}

This is a safety measure to prevent conflicting edits.

Options:
1. Wait a moment and retry
2. Check MCP Agent Mail service: sudo systemctl status mcp-agent-mail
3. Run bd-cleanup to check for issues
4. Set FARMHAND_SKIP_ENFORCEMENT=1 to bypass (use with caution)"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    is_reserved, blocking_agent = check_file_reserved(file_path, agent_name, reservations)

    if blocking_agent:
        home_dir = str(Path.home())
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: File reserved by another agent.

File: {file_path}
Reserved by: {blocking_agent}
Your agent: {agent_name}

Options:

1. Request access via Agent Mail:
```python
send_message(
    project_key="{home_dir}",
    sender_name="{agent_name}",
    to=["{blocking_agent}"],
    subject="File access request",
    body_md="Need access to {os.path.basename(file_path)}. Can you release when done?"
)
```

2. Check if reservation is stale:
```bash
bd-cleanup --list
```

3. Work on a different file while waiting"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    if not is_reserved:
        home_dir = str(Path.home())
        # Suggest a glob pattern for the directory
        file_dir = os.path.dirname(file_path)
        suggested_pattern = f"{file_dir}/**"
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: File not reserved.

File: {file_path}
Agent: {agent_name}

Copy-paste to reserve:
```python
file_reservation_paths(
    project_key="{home_dir}",
    agent_name="{agent_name}",
    paths=["{suggested_pattern}"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)
```

Or reserve just this file:
```python
file_reservation_paths(
    project_key="{home_dir}",
    agent_name="{agent_name}",
    paths=["{file_path}"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)
```

Tip: Replace <issue-id> with your bd issue ID (e.g., "ubuntu-42")"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # All checks passed
    sys.exit(0)

if __name__ == "__main__":
    main()
