# CLAUDE.md

Guidance for Claude Code in multi-agent workflows.

---

## Before Any Action

```bash
bd ready        # What can I work on?
bd stats        # Project health
```

### Enforced Rules (Hooks Block Violations)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TodoWrite              → BLOCKED (use bd instead)                      │
│  Edit/Write unregistered → BLOCKED (call register_agent first)          │
│  Edit/Write unreserved   → BLOCKED (call file_reservation_paths first)  │
│  bv without --robot-*    → TUI hangs agent                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Required Workflow

### 1. Find & Claim Work
```bash
bd ready
bd update <id> --status=in_progress
```

### 2. Register (ENFORCED)
```python
response = register_agent(
    project_key="$HOME",
    program="claude-code",
    model="opus-4.5"
)
# Response: {"name": "BlueLake", ...} ← Save this name
```

### 3. Reserve Files (ENFORCED)
```python
file_reservation_paths(
    project_key="$HOME",
    agent_name="<your-assigned-name>",
    paths=["src/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)
```

### 4. Work
Now Edit/Write operations will succeed.

### 5. Cleanup
```python
release_file_reservations(project_key="$HOME", agent_name="<your-name>")
```
```bash
bd close <id> --reason="Done"
```

---

## Error Recovery

**"Agent not registered"** → Call `register_agent()`

**"File not reserved"** → Call `file_reservation_paths()`

**"File reserved by X"** → Message them or wait:
```python
send_message(..., to=["X"], subject="Need access to file")
```

**Session crashed** → Run `bd-cleanup`

**Service down** → `sudo systemctl restart mcp-agent-mail`

---

## Multi-Agent Patterns

### Sequential Handoff
```python
# Agent A done
release_file_reservations(...)
send_message(..., to=[], subject="[issue-id] Done", thread_id="issue-id")
```
```bash
bd close <id>
```

### Parallel (Non-Overlapping)
```python
# Agent A: backend
file_reservation_paths(..., paths=["src/backend/**/*.py"], ...)

# Agent B: frontend (no conflict)
file_reservation_paths(..., paths=["src/frontend/**/*.tsx"], ...)
```

### Coordinated Access
```python
# Agent A: notify, release, notify
send_message(..., to=["AgentB"], body_md="Releasing config.py soon")
release_file_reservations(...)
send_message(..., to=["AgentB"], body_md="Released!")

# Agent B: now reserve
file_reservation_paths(..., paths=["src/config.py"], ...)
```

---

## Tool Reference

### bd (Beads)
```bash
bd ready                    # Available work
bd create --title="X" --type=task
bd update <id> --status=in_progress
bd close <id> --reason="X"
bd show <id>                # Details
bd blocked                  # What's stuck
bd dep <blocker> <blocked>  # Dependencies
```

### bv (Beads Viewer) - ALWAYS use --robot-*
```bash
bv --robot-plan       # Execution order
bv --robot-priority   # What to work on
bv --robot-insights   # Graph metrics
```

### Agent Mail
```python
register_agent(project_key, program, model)
file_reservation_paths(project_key, agent_name, paths, ttl_seconds, exclusive, reason)
release_file_reservations(project_key, agent_name)
send_message(project_key, sender_name, to, subject, body_md, thread_id)
fetch_inbox(project_key, agent_name)
```

### qmd (Markdown Search)
```bash
qmd search "keyword"    # BM25
qmd vsearch "concept"   # Semantic
qmd query "question"    # Hybrid
```

### bd-cleanup
```bash
bd-cleanup              # Interactive
bd-cleanup --list       # Show orphaned
bd-cleanup --force      # Cleanup stale
bd-cleanup --release-all # Nuclear
```

---

## Linking Convention

Use beads issue ID everywhere:
- `thread_id` in messages
- `reason` in reservations
- Subject: `[ubuntu-42] Description`
- Commits: include `ubuntu-42`

---

## Environment

```bash
export BEADS_DB=$HOME/.beads/beads.db
```

| Service | Port | Check |
|---------|------|-------|
| MCP Agent Mail | 8765 | `systemctl status mcp-agent-mail` |
| Ollama | 11434 | `systemctl status ollama` |

---

## Enforcement Hooks

| Hook | Blocks | Location |
|------|--------|----------|
| todowrite-interceptor.py | TodoWrite | ~/.claude/hooks/ |
| reservation-checker.py | Edit/Write without reg/reserve | ~/.claude/hooks/ |
| mcp-state-tracker.py | (tracks state) | ~/.claude/hooks/ |
| session-init.py | (cleanup on start) | ~/.claude/hooks/ |

---

## Rules Summary

1. `bd ready` first
2. `bd update --status=in_progress` to claim
3. `register_agent()` **← ENFORCED**
4. `file_reservation_paths()` **← ENFORCED**
5. Work (Edit/Write now allowed)
6. `release_file_reservations()`
7. `bd close`
8. TodoWrite **← BLOCKED**
9. `bv` only with `--robot-*`
10. `bd-cleanup` for recovery
