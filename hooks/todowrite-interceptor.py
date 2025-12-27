#!/usr/bin/env python3
"""
TodoWrite Interceptor Hook
--------------------------
Blocks TodoWrite tool calls and instructs Claude to use bd (beads) instead.
This enforces the multi-agent workflow where all task tracking goes through beads.

Exit codes:
  0 - Success (with deny decision in JSON)
  2 - Blocking error
"""

import json
import os
import sys

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

    if tool_name == "TodoWrite":
        todos = tool_input.get("todos", [])

        # Build helpful translation message
        bd_commands = []
        for todo in todos:
            content = todo.get("content", "")
            status = todo.get("status", "pending")

            if status == "pending":
                bd_commands.append(f'bd create --title="{content}" --type=task')
            elif status == "in_progress":
                bd_commands.append('# For in_progress: bd update <id> --status=in_progress')
            elif status == "completed":
                bd_commands.append('# For completed: bd close <id> --reason="{content}"')

        suggestion = "\n".join(bd_commands) if bd_commands else "bd create --title=\"...\" --type=task"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: TodoWrite is forbidden in this environment.

Use beads (bd) for all task tracking:

{suggestion}

Quick reference:
  bd create --title="..." --type=task   # Create task
  bd update <id> --status=in_progress   # Claim task
  bd close <id> --reason="..."          # Complete task
  bd ready                              # List available work

See ~/CLAUDE.md for the complete workflow."""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Not TodoWrite, allow through
    sys.exit(0)

if __name__ == "__main__":
    main()
