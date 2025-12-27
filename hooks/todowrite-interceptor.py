#!/usr/bin/env python3
"""
TodoWrite Interceptor Hook (v2 - Improved error messages)
----------------------------------------------------------
Blocks TodoWrite tool calls and instructs Claude to use bd (beads) instead.
This enforces the multi-agent workflow where all task tracking goes through beads.

v2 Changes (Farmhand-d2t):
- Shows translated bd commands for each todo item
- Links to troubleshooting docs
- Better formatting of suggestions

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
        todo_count = len(todos)

        # Build helpful translation message
        bd_commands = []
        for i, todo in enumerate(todos[:5]):  # Limit to first 5 to avoid huge messages
            content = todo.get("content", "")
            status = todo.get("status", "pending")
            # Escape quotes in content for shell safety
            safe_content = content.replace('"', '\\"')[:60]  # Truncate long content

            if status == "pending":
                bd_commands.append(f'bd create --title="{safe_content}" --type=task')
            elif status == "in_progress":
                bd_commands.append('# Mark in_progress: bd update <id> --status=in_progress')
            elif status == "completed":
                bd_commands.append('# Mark completed: bd close <id> --reason="done"')

        if todo_count > 5:
            bd_commands.append(f"# ... and {todo_count - 5} more items")

        suggestion = "\n".join(bd_commands) if bd_commands else 'bd create --title="..." --type=task'

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"""BLOCKED: TodoWrite is disabled. Use beads (bd) instead.

Attempted to create {todo_count} todo(s). Equivalent bd commands:

```bash
{suggestion}
```

Quick reference:
```bash
bd ready                              # List available work (START HERE)
bd create --title="..." --type=task   # Create new task
bd update <id> --status=in_progress   # Claim task
bd close <id> --reason="..."          # Complete task
bd list --status=in_progress          # See your active tasks
```

Why beads instead of TodoWrite?
- Beads are git-backed and persist across sessions
- Beads integrate with multi-agent coordination
- Beads track dependencies between tasks

See: docs/troubleshooting-flowchart.md Section A (Getting Started)"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Not TodoWrite, allow through
    sys.exit(0)

if __name__ == "__main__":
    main()
