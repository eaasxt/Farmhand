#!/usr/bin/env python3
"""
Session Initialization Hook (SessionStart) - v3
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
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

# Escape hatch for experienced users - bypass all processing
if os.environ.get("FARMHAND_SKIP_ENFORCEMENT") == "1":
    sys.exit(0)

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


def cleanup_old_state_files(max_age_days=7):
    """Remove state files older than max_age_days.

    Args:
        max_age_days: Maximum age in days before cleanup (default 7)

    Returns:
        List of cleaned up file names
    """
    cleaned = []
    cutoff = time.time() - (max_age_days * 24 * 3600)

    if not STATE_DIR.exists():
        return cleaned

    # Clean up old per-agent state files (state-*.json)
    for state_file in STATE_DIR.glob("state-*.json"):
        try:
            if state_file.stat().st_mtime < cutoff:
                state_file.unlink()
                cleaned.append(state_file.name)
        except (IOError, OSError):
            pass  # Skip files we can't access

    return cleaned


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

    # Clean up old state files (older than 7 days)
    cleaned_files = cleanup_old_state_files(max_age_days=7)

    # Check for orphaned reservations
    orphaned = check_orphaned_reservations()

    # Build context message
    context_parts = []

    if cleaned_files:
        context_parts.append(f"Cleaned up {len(cleaned_files)} old state file(s) (> 7 days old)")
        context_parts.append("")

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
