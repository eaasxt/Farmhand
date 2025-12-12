#!/usr/bin/env python3
"""
TodoWrite Interceptor Hook (PreToolUse)
---------------------------------------
Blocks TodoWrite and redirects to bd (beads) commands.
"""

import json
import sys

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name == "TodoWrite":
        todos = tool_input.get("todos", [])
        bd_commands = []

        for todo in todos:
            content = todo.get("content", "")
            status = todo.get("status", "pending")
            if status == "pending":
                bd_commands.append(f'bd create --title="{content}" --type=task')
            elif status == "in_progress":
                bd_commands.append(f'# bd update <id> --status=in_progress')
            elif status == "completed":
                bd_commands.append(f'# bd close <id> --reason="{content}"')

        suggestion = "\n".join(bd_commands) if bd_commands else "bd create --title=\"...\" --type=task"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: TodoWrite is forbidden.

Use beads (bd) instead:

{suggestion}

Reference:
  bd create --title="..." --type=task   # Create
  bd update <id> --status=in_progress   # Claim
  bd close <id> --reason="..."          # Complete
  bd ready                              # List work"""
            }
        }
        print(json.dumps(output))

    sys.exit(0)

if __name__ == "__main__":
    main()
