# JohnDeere Hooks System

The hooks system enforces multi-agent coordination by intercepting Claude Code tool calls and blocking operations that violate the workflow.

## Overview

Hooks are Python scripts that run before/after Claude Code tool calls. They're configured in `~/.claude/settings.json` and installed to `~/.claude/hooks/`.

```
~/.claude/
├── settings.json           # Hook configuration
├── hooks/
│   ├── todowrite-interceptor.py
│   ├── reservation-checker.py
│   ├── mcp-state-tracker.py
│   ├── session-init.py
│   └── git_safety_guard.py
└── agent-state.json        # State file (single-agent)
└── state-{AGENT_NAME}.json # State file (multi-agent)
```

## Hook Types

### PreToolUse Hooks

Run **before** a tool executes. Can block the operation.

| Hook | Triggers On | Purpose |
|------|-------------|---------|
| `todowrite-interceptor.py` | TodoWrite | Blocks TodoWrite, suggests `bd` |
| `reservation-checker.py` | Edit, Write | Enforces file reservations |
| `git_safety_guard.py` | Bash (git commands) | Blocks destructive git operations |

### PostToolUse Hooks

Run **after** a tool executes. Cannot block, only observe.

| Hook | Triggers On | Purpose |
|------|-------------|---------|
| `mcp-state-tracker.py` | MCP tools | Tracks registration/reservation state |

### SessionStart Hooks

Run when a Claude Code session begins.

| Hook | Purpose |
|------|---------|
| `session-init.py` | Clears stale state, checks orphaned reservations |

## Hook Details

### todowrite-interceptor.py

**Trigger:** TodoWrite tool calls

**Behavior:** Always blocks with a helpful message showing equivalent `bd` commands.

**Example output:**
```
BLOCKED: TodoWrite is forbidden in this environment.

Use beads (bd) for all task tracking:

bd create --title="Fix login bug" --type=task

Quick reference:
  bd create --title="..." --type=task   # Create task
  bd update <id> --status=in_progress   # Claim task
  bd close <id> --reason="..."          # Complete task
  bd ready                              # List available work
```

### reservation-checker.py

**Trigger:** Edit, Write tool calls

**Behavior:** Checks three conditions:
1. Agent is registered (via MCP or AGENT_NAME env var)
2. Target file is reserved by this agent
3. Target file is not reserved by another agent

**Skip patterns:** Files matching these patterns are not checked:
- `/.claude/`
- `/.local/bin/`
- `/tmp/`
- `.pyc`, `__pycache__`
- `.git/`
- `node_modules/`

**State file logic:**
- When `AGENT_NAME` env var is set: uses `~/.claude/state-{AGENT_NAME}.json`
- When not set: uses `~/.claude/agent-state.json`

This matches the logic in `mcp-state-tracker.py` for consistency.

**Reservation lookup:** Queries the MCP Agent Mail SQLite database directly:
```
~/mcp_agent_mail/storage.sqlite3
  └── file_reservations table
```

### mcp-state-tracker.py

**Trigger:** MCP Agent Mail tool calls (PostToolUse)

**Tracked tools:**
- `register_agent` → Sets `registered=true`, stores agent name
- `file_reservation_paths` → Tracks reservations locally
- `release_file_reservations` → Clears local reservation tracking
- `macro_start_session` → Combines register + reserve

**State file:** Uses same logic as reservation-checker:
- Multi-agent: `~/.claude/state-{AGENT_NAME}.json`
- Single-agent: `~/.claude/agent-state.json`

### session-init.py

**Trigger:** Session start

**Behavior:**
1. Clears this agent's state file (enables fresh start)
2. Checks for orphaned reservations in SQLite database
3. Warns if stale reservations found (> 4 hours old)
4. Injects workflow context reminder

**Output:** Adds context to session:
```
WARNING: Found potentially orphaned file reservations:
  - BlueLake: [src/**] (age: 5.2h)
Run `bd-cleanup` to review and release if needed.

WORKFLOW REMINDER: Read ~/CLAUDE.md before starting work.
Required sequence: bd ready -> register_agent -> file_reservation_paths -> work -> release -> bd close
```

### git_safety_guard.py

**Trigger:** Bash tool calls containing git commands

**Blocked patterns:**
- `git checkout -- .` - Discards all changes
- `git reset --hard` - Destroys uncommitted work
- `git clean -f` - Removes untracked files
- `git push --force` - Rewrites remote history
- `git branch -D` - Force-deletes branch
- `git stash drop/clear` - Loses stashed changes
- `rm -rf` (outside temp dirs) - Recursive deletion

**Safe patterns (always allowed):**
- `git checkout -b` - Create new branch
- `git restore --staged` - Unstage without discarding
- `git clean -n` - Dry-run clean
- `rm -rf /tmp/...` - Temp directory cleanup

## Configuration

Hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [{"type": "command", "command": "/home/ubuntu/.claude/hooks/todowrite-interceptor.py"}]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "/home/ubuntu/.claude/hooks/reservation-checker.py"}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "/home/ubuntu/.claude/hooks/git_safety_guard.py"}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__mcp-agent-mail__.*",
        "hooks": [{"type": "command", "command": "/home/ubuntu/.claude/hooks/mcp-state-tracker.py"}]
      }
    ],
    "SessionStart": [
      {"type": "command", "command": "/home/ubuntu/.claude/hooks/session-init.py"}
    ]
  }
}
```

## Hook Input/Output Format

### Input (stdin)

```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "old_string": "...",
    "new_string": "..."
  },
  "tool_output": {}  // Only for PostToolUse
}
```

### Output (stdout) - Block

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Explanation of why blocked..."
  }
}
```

### Output - Allow

Exit code 0 with no JSON output = allow.

## Troubleshooting

### "Agent not registered"

The reservation-checker couldn't find registration. Fix:

```python
register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
```

Or set `AGENT_NAME` environment variable before launching Claude.

### "File not reserved"

Reserve the file before editing:

```python
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="YourAgentName",
    paths=["/path/to/file.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="issue-id"
)
```

### "File reserved by another agent"

Wait for the other agent to release, or coordinate via Agent Mail:

```python
send_message(
    project_key="/home/ubuntu",
    sender_name="YourName",
    to=["OtherAgent"],
    subject="File access request",
    body_md="Need access to /path/to/file.py"
)
```

### State file mismatch

If registration doesn't seem to work, check state file consistency:

```bash
# Check which state file is being used
ls -la ~/.claude/state-*.json ~/.claude/agent-state.json

# View contents
cat ~/.claude/agent-state.json
```

### Stale reservations

Clean up orphaned state:

```bash
bd-cleanup --list       # View orphaned items
bd-cleanup --force      # Release stale reservations
bd-cleanup --reset-state # Reset local state only
```

## Extending Hooks

To add a new hook:

1. Create the Python script in `~/.claude/hooks/`
2. Add configuration to `~/.claude/settings.json`
3. Test with a sample tool call

Hook requirements:
- Read JSON from stdin
- Exit 0 to allow, or output deny JSON
- Must be executable (`chmod +x`)
- Should handle errors gracefully (fail open if uncertain)
