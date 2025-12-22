#!/usr/bin/env python3
"""
Session Initialization Hook (SessionStart)
-------------------------------------------
Handles cleanup and initialization at session start:
- Clears stale agent state from previous sessions (ONLY for this agent)
- Checks for orphaned reservations
- Injects workflow context

MULTI-AGENT SAFE: Uses AGENT_NAME env var to isolate state per agent.
"""

import json
import sys
import os
import time
from pathlib import Path

# Per-agent state files to avoid conflicts
AGENT_NAME = os.environ.get("AGENT_NAME")
STATE_DIR = Path.home() / ".claude"
MCP_STORAGE = Path.home() / ".mcp_agent_mail"

def get_state_file():
    """Get the state file path for this agent."""
    if AGENT_NAME:
        # Multi-agent: per-agent state file
        return STATE_DIR / f"state-{AGENT_NAME}.json"
    else:
        # Single-agent: legacy shared state file
        return STATE_DIR / "agent-state.json"

def parse_timestamp(value, default=0):
    """Parse timestamp - handles both Unix float and ISO string formats."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            # Try ISO format: 2025-12-22T05:38:00Z
            from datetime import datetime
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return dt.timestamp()
        except (ValueError, AttributeError):
            return default
    return default

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
                created_at = parse_timestamp(data.get("created_at"), 0)
                expires_at = parse_timestamp(data.get("expires_at"), 0)

                # Check for stale but not expired reservations
                if created_at > 0 and now - created_at > stale_threshold and expires_at > now:
                    orphaned.append({
                        "file": str(res_file),
                        "agent": data.get("agent_name", "unknown"),
                        "paths": data.get("paths", []),
                        "age_hours": round((now - created_at) / 3600, 1)
                    })
        except (json.JSONDecodeError, IOError, TypeError):
            continue

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
