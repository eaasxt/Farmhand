#!/usr/bin/env python3
"""
Session Initialization Hook (SessionStart) - v2
------------------------------------------------
Handles cleanup and initialization at session start:
- Clears stale agent state from previous sessions (ONLY for this agent)
- Checks for orphaned reservations in SQLite database
- Injects workflow context

MULTI-AGENT SAFE: Uses AGENT_NAME env var to isolate state per agent.
"""

import json
import sys
import os
import time
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

def check_orphaned_reservations():
    """Check for stale reservations from crashed sessions in SQLite database."""
    orphaned = []

    if not MCP_DB_PATH.exists():
        return orphaned

    try:
        conn = sqlite3.connect(str(MCP_DB_PATH), timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find reservations that are old (> 4 hours) but not released and not expired
        stale_threshold_hours = 4
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            SELECT
                fr.path_pattern,
                fr.created_ts,
                fr.expires_ts,
                a.name as agent_name
            FROM file_reservations fr
            JOIN agents a ON fr.agent_id = a.id
            WHERE fr.released_ts IS NULL
              AND fr.expires_ts > ?
              AND datetime(fr.created_ts, '+' || ? || ' hours') < ?
        """, (now_str, stale_threshold_hours, now_str))

        for row in cursor.fetchall():
            # Calculate age
            try:
                created = datetime.fromisoformat(row["created_ts"].replace('Z', '+00:00'))
                age_hours = (now - created).total_seconds() / 3600
            except (ValueError, AttributeError):
                age_hours = stale_threshold_hours + 1

            orphaned.append({
                "agent": row["agent_name"],
                "paths": [row["path_pattern"]],
                "age_hours": round(age_hours, 1)
            })

        conn.close()
    except sqlite3.Error:
        pass

    return orphaned

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    trigger = input_data.get("trigger", "startup")
    state_file = get_state_file()

    # Clear THIS AGENT's state on fresh startup (not other agents')
    if trigger in ["startup", "clear"]:
        if state_file.exists():
            try:
                os.remove(state_file)
            except IOError:
                pass

    # Check for orphaned reservations
    orphaned = check_orphaned_reservations()

    # Build context message
    context_parts = []

    if orphaned:
        context_parts.append("WARNING: Found potentially orphaned file reservations:")
        for orph in orphaned[:5]:  # Limit to 5
            context_parts.append(f"  - {orph['agent']}: {orph['paths']} (age: {orph['age_hours']}h)")
        context_parts.append("Run `bd-cleanup` to review and release if needed.")
        context_parts.append("")

    context_parts.append("WORKFLOW REMINDER: Read ~/CLAUDE.md before starting work.")
    context_parts.append("Required sequence: bd ready -> register_agent -> file_reservation_paths -> work -> release -> bd close")

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(context_parts)
        }
    }
    print(json.dumps(output))
    sys.exit(0)

if __name__ == "__main__":
    main()
