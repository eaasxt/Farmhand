#!/usr/bin/env python3
"""
Session Init Hook (SessionStart)
--------------------------------
Cleans stale state and injects workflow reminder.
"""

import json
import sys
import os
import time
from pathlib import Path

STATE_FILE = Path.home() / ".claude" / "agent-state.json"
MCP_STORAGE = Path.home() / ".mcp_agent_mail"

def check_orphaned_reservations():
    orphaned = []
    reservations_dir = MCP_STORAGE / "reservations"
    if not reservations_dir.exists():
        return orphaned

    now = time.time()
    for res_file in reservations_dir.glob("*.json"):
        try:
            with open(res_file) as f:
                data = json.load(f)
                created_at = data.get("created_at", 0)
                expires_at = data.get("expires_at", 0)
                if now - created_at > 4 * 3600 and expires_at > now:
                    orphaned.append({
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

    # Clear state on fresh start
    if trigger in ["startup", "clear"]:
        if STATE_FILE.exists():
            try:
                os.remove(STATE_FILE)
            except IOError:
                pass

    orphaned = check_orphaned_reservations()
    context_parts = []

    if orphaned:
        context_parts.append("WARNING: Orphaned reservations detected:")
        for o in orphaned[:3]:
            context_parts.append(f"  - {o['agent']}: {o['paths'][:2]} ({o['age_hours']}h old)")
        context_parts.append("Run `bd-cleanup` to review.")
        context_parts.append("")

    context_parts.append("WORKFLOW: bd ready -> register_agent -> file_reservation_paths -> work -> release -> bd close")

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
