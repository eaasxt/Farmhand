#!/usr/bin/env python3
"""
Session Initialization Hook (SessionStart)
-------------------------------------------
Handles cleanup and initialization at session start:
- Clears stale agent state from previous sessions
- Checks for orphaned reservations
- Injects workflow context

This ensures clean state after crashes or interrupts.
"""

import json
import sys
import os
import time
from pathlib import Path

STATE_FILE = Path.home() / ".claude" / "agent-state.json"
MCP_STORAGE = Path.home() / ".mcp_agent_mail"

def check_orphaned_reservations():
    """Check for reservations from crashed sessions."""
    orphaned = []
    reservations_dir = MCP_STORAGE / "reservations"

    if not reservations_dir.exists():
        return orphaned

    now = time.time()
    stale_threshold = 4 * 3600  # 4 hours

    for res_file in reservations_dir.glob("*.json"):
        try:
            with open(res_file) as f:
                data = json.load(f)
                created_at = data.get("created_at", 0)
                expires_at = data.get("expires_at", 0)

                # Check for stale but not expired reservations
                if now - created_at > stale_threshold and expires_at > now:
                    orphaned.append({
                        "file": str(res_file),
                        "agent": data.get("agent_name", "unknown"),
                        "paths": data.get("paths", []),
                        "age_hours": round((now - created_at) / 3600, 1)
                    })
        except (json.JSONDecodeError, IOError):
            continue

    return orphaned

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    trigger = input_data.get("trigger", "startup")

    # Clear previous session state on fresh startup
    if trigger in ["startup", "clear"]:
        if STATE_FILE.exists():
            try:
                os.remove(STATE_FILE)
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
