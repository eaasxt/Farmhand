# JohnDeere Hooks

Enforcement scripts that intercept Claude Code tool calls to enforce multi-agent workflow.

## Installation

Hooks are installed by `scripts/install/09-hooks.sh`:
1. Copies scripts to `~/.claude/hooks/`
2. Updates `~/.claude/settings.json` with hook configuration
3. Makes scripts executable

## Hooks Overview

| File | Trigger | Purpose |
|------|---------|---------|
| `todowrite-interceptor.py` | TodoWrite | Blocks TodoWrite, suggests `bd` |
| `reservation-checker.py` | Edit, Write | Enforces file reservations |
| `mcp-state-tracker.py` | MCP tools | Tracks agent state |
| `session-init.py` | Session start | Clears stale state |
| `git_safety_guard.py` | Bash (git) | Blocks destructive git commands |
| `on-file-write.sh` | PostToolUse | Optional UBS integration |

## Hook Descriptions

### todowrite-interceptor.py

**Purpose:** Force agents to use `bd` (beads) instead of TodoWrite for task tracking.

**Behavior:** Always blocks with helpful message showing equivalent bd commands.

### reservation-checker.py (v6)

**Purpose:** Enforce file reservations before editing.

**Checks:**
1. Agent is registered (via MCP or AGENT_NAME env var)
2. Target file is reserved by this agent
3. Target file is not reserved by another agent

**State file logic:**
- With `AGENT_NAME` env var: `~/.claude/state-{AGENT_NAME}.json`
- Without: `~/.claude/agent-state.json`

**Reservation lookup:** Queries `~/mcp_agent_mail/storage.sqlite3` directly.

### mcp-state-tracker.py

**Purpose:** Track agent state after MCP calls.

**Tracked tools:**
- `register_agent` → Sets registered=true, stores agent name
- `file_reservation_paths` → Tracks reservations locally
- `release_file_reservations` → Clears local reservations
- `macro_start_session` → Combines register + reserve

### session-init.py

**Purpose:** Clean start for new sessions.

**Behavior:**
1. Clears this agent's state file
2. Checks for orphaned reservations (> 4 hours old)
3. Warns if stale reservations found
4. Injects workflow reminder

### git_safety_guard.py

**Purpose:** Prevent accidental data loss from destructive git commands.

**Blocked:**
- `git checkout -- .`
- `git reset --hard`
- `git clean -f` (except dry-run)
- `git push --force`
- `git branch -D`
- `git stash drop/clear`
- `rm -rf` (outside temp dirs)

**Always allowed:**
- `git checkout -b` (create branch)
- `git restore --staged` (unstage)
- `git clean -n` (dry-run)
- `rm -rf /tmp/...` (temp dirs)

### on-file-write.sh

**Purpose:** Optional hook to run UBS after file writes.

**Note:** Currently minimal; can be extended for automatic scanning.

## Configuration

Hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/todowrite-interceptor.py"}]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/reservation-checker.py"}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/git_safety_guard.py"}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__mcp-agent-mail__.*",
        "hooks": [{"type": "command", "command": "~/.claude/hooks/mcp-state-tracker.py"}]
      }
    ],
    "SessionStart": [
      {"type": "command", "command": "~/.claude/hooks/session-init.py"}
    ]
  }
}
```

## Developing Hooks

### Input Format (stdin)

```json
{
  "tool_name": "Edit",
  "tool_input": {"file_path": "/path/to/file.py", ...},
  "tool_output": {}  // Only for PostToolUse
}
```

### Output Format (stdout)

**To block:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Explanation..."
  }
}
```

**To allow:** Exit 0 with no output.

### Best Practices

1. **Fail open** - If uncertain, allow the operation
2. **Clear messages** - Tell the user exactly what to do
3. **Consistent state files** - Use `get_state_file()` pattern
4. **Handle JSON errors** - Gracefully handle malformed input
5. **No side effects in PreToolUse** - Only PostToolUse should modify state

## Troubleshooting

### Hook not running

1. Check permissions: `chmod +x ~/.claude/hooks/*.py`
2. Verify settings.json matcher pattern
3. Check Claude Code recognizes the hook: restart Claude Code

### Wrong state file

All hooks must use consistent state file logic:
```python
def get_state_file():
    if os.environ.get("AGENT_NAME"):
        return Path.home() / ".claude" / f"state-{os.environ['AGENT_NAME']}.json"
    else:
        return Path.home() / ".claude" / "agent-state.json"
```

### SQLite errors

If reservation-checker can't read the database:
```bash
# Check database exists
ls -la ~/mcp_agent_mail/storage.sqlite3

# Check MCP Agent Mail is running
sudo systemctl status mcp-agent-mail
```
