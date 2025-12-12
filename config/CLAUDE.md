# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## STOP - Read Before Any Action

### FORBIDDEN - These Will Break Your Workflow

```
+------------------------------------------------------------------+
|  NEVER use TodoWrite tool         -> use bd commands instead     |
|  NEVER run bv without --robot-*   -> TUI will hang the agent     |
|  NEVER edit files without reservation -> causes merge conflicts  |
|  NEVER work without a bd issue ID -> untracked work is lost work |
+------------------------------------------------------------------+
```

### REQUIRED - Every Session Starts Here

```bash
bd ready        # What can I work on?
bd stats        # Project health check
```

---

## The Workflow (Follow Exactly)

```bash
# 1. Find and claim work
bd ready
bd update <id> --status=in_progress
```

```python
# 2. Reserve files BEFORE editing (Agent Mail MCP)
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<YourName>",          # From register_agent response
    paths=["src/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"               # e.g., "ubuntu-42"
)
```

```bash
# 3. Do the work
# ... edit, test, iterate ...

# 4. Release and close
```

```python
release_file_reservations(project_key="/home/ubuntu", agent_name="<YourName>")
```

```bash
bd close <id> --reason="Implemented X"
```

### If You Discover New Work While Working

```bash
bd create --title="Found: new thing" --type=task --deps discovered-from:<current-id>
```

---

## TodoWrite is FORBIDDEN - Use bd Instead

If you think "I should use TodoWrite", use bd:

| TodoWrite Pattern | bd Command |
|-------------------|------------|
| Create todo list | `bd create --title="..." --type=task` |
| Mark in_progress | `bd update <id> --status=in_progress` |
| Mark completed | `bd close <id>` |
| View todos | `bd ready` |
| List all | `bd list --status=open` |

---

## Tool Reference

### bd (Beads) - Issue Tracking

```bash
# READ
bd ready                              # Unblocked issues (START HERE)
bd list --status=open                 # All open issues
bd list --status=in_progress          # Currently claimed
bd show <id>                          # Issue details + dependencies
bd blocked                            # What's stuck and why

# WRITE
bd create --title="..." --type=task   # New issue
bd update <id> --status=in_progress   # Claim work
bd close <id> --reason="Done"         # Complete
bd dep <blocker> <blocked>            # A blocks B

# ANALYZE
bd stats                              # Health metrics
```

**Issue Types:** `bug` | `feature` | `task` | `epic` | `chore`
**Priority:** `0` critical, `1` high, `2` medium (default), `3` low, `4` backlog

### bv (Beads Viewer) - Graph Intelligence

**NEVER run `bv` without `--robot-*` flags** - TUI will hang the agent.

```bash
bv --robot-help       # List all safe commands
bv --robot-plan       # Execution order with parallel tracks
bv --robot-priority   # What to work on + reasoning
bv --robot-insights   # Graph metrics (PageRank, cycles, critical path)
```

| Use bd for | Use bv for |
|------------|------------|
| CRUD operations | Graph analysis |
| "What's next?" | Impact assessment |
| Status updates | Parallel planning |

### Agent Mail - Multi-Agent Coordination

**Your Identity** (set on first `register_agent` call):

| Field | Value |
|-------|-------|
| project_key | `/home/ubuntu` |
| program | `claude-code` |
| model | `opus-4.5` |

Agent names are adjective+noun (e.g., `BlueLake`, `GreenCastle`). Note your assigned name and use it consistently.

**Before Editing Files - ALWAYS Reserve:**

```python
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<YourName>",
    paths=["path/to/files/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)
```

**Announce Work:**

```python
send_message(
    project_key="/home/ubuntu",
    sender_name="<YourName>",
    to=[],                              # Empty = broadcast to thread
    subject="[<issue-id>] Starting X",
    body_md="Working on...",
    thread_id="<issue-id>"              # MUST match beads issue
)
```

**Check Messages:**

```python
fetch_inbox(project_key="/home/ubuntu", agent_name="<YourName>")
```

**Service Management:**

```bash
sudo systemctl status mcp-agent-mail   # Check (port 8765)
sudo systemctl restart mcp-agent-mail  # Restart
journalctl -u mcp-agent-mail -f        # Logs
```

### qmd - Markdown Search

```bash
qmd search "keyword"     # Fast BM25 search
qmd vsearch "concept"    # Semantic vector search
qmd query "question"     # Hybrid + reranking (best quality)
qmd status               # Index health
```

Requires Ollama running (`systemctl status ollama`).

---

## Environment

```bash
export BEADS_DB=/home/ubuntu/.beads/beads.db
export PATH="/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
```

| Tool | Location |
|------|----------|
| bd | `~/.local/bin/bd` |
| bv | `/home/linuxbrew/.linuxbrew/bin/bv` |
| qmd | `~/.local/bin/qmd` |

| Service | Port |
|---------|------|
| MCP Agent Mail | 8765 |
| Ollama | 11434 |

---

## Anti-Patterns

| Pattern | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| TodoWrite tool | Duplicates beads, loses sync | `bd create/update/close` |
| `bv` without `--robot-*` | TUI hangs agent | `bv --robot-plan` |
| Edit without reservation | Conflicts with other agents | `file_reservation_paths()` first |
| Work without issue ID | Untracked, no context | `bd create` then work |
| Guessing agent names | Message delivery fails | Use your registered name |

---

## Quick Decision Tree

```
Need to track work?           -> bd create --title="..." --type=task
Need to see what to do?       -> bd ready
Need graph analysis?          -> bv --robot-priority
Need to edit files?           -> file_reservation_paths() FIRST
Need to find documentation?   -> qmd query "topic"
Need to message other agents? -> send_message() with thread_id=<issue-id>
```

---

## Linking Convention

Everything links via the beads issue ID:

| Context | Value |
|---------|-------|
| Mail `thread_id` | beads issue ID (`ubuntu-42`) |
| Mail subject | `[ubuntu-42] Description` |
| Reservation `reason` | `ubuntu-42` |
| Commit message | Include `ubuntu-42` |
