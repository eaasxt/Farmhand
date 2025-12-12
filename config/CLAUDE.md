# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## BEFORE ANYTHING ELSE

```bash
bd ready        # See available work
bd stats        # Project health
```

---

## Critical Rules

1. **Use `bd` for ALL task tracking** - NEVER use TodoWrite tool
2. **Use `bv` with `--robot-*` flags ONLY** - Never launch interactive TUI
3. **Reserve files before editing** - Prevents multi-agent conflicts
4. **Link everything to beads issues** - Use issue ID as thread_id everywhere

### TodoWrite is FORBIDDEN

| Instead of TodoWrite | Use bd |
|---------------------|--------|
| Creating todos | `bd create --title="..." --type=task` |
| Marking in_progress | `bd update <id> --status=in_progress` |
| Marking completed | `bd close <id>` |
| Listing todos | `bd ready` |

---

## The Workflow (Follow This Exactly)

```bash
# 1. Find work
bd ready

# 2. Claim it
bd update <id> --status=in_progress
```

```python
# 3. Reserve files (Agent Mail MCP)
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<your-assigned-name>",  # From register_agent response
    paths=["path/to/files/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"  # e.g., "ubuntu-42"
)

# 4. Announce (optional but good practice)
send_message(
    project_key="/home/ubuntu",
    sender_name="<your-assigned-name>",
    to=[],  # Empty = broadcast to thread followers
    subject="[<issue-id>] Starting work",
    body_md="Working on X...",
    thread_id="<issue-id>"
)
```

```bash
# 5. Do the work
# ... edit files, run tests, etc.

# 6. Release and close
```

```python
release_file_reservations(
    project_key="/home/ubuntu",
    agent_name="<your-assigned-name>"
)
```

```bash
bd close <id> --reason="Implemented X"
```

---

## bd (Beads) Quick Reference

```bash
# Discovery
bd ready                              # Unblocked issues ready to work
bd list --status=open                 # All open
bd show <id>                          # Full details + deps

# Lifecycle
bd create --title="..." --type=task   # types: bug|feature|task|epic|chore
bd update <id> --status=in_progress   # Claim
bd close <id> --reason="Done"         # Complete

# Dependencies
bd dep <blocker> <blocked>            # A blocks B
bd blocked                            # Show blocked issues

# Multi-project: prefix titles with [ProjectName]
bd create --title="[MyApp] Add login" --type=feature
```

**Issue Types:** `bug` (broken), `feature` (new), `task` (work item), `epic` (large), `chore` (maintenance)

**Priorities:** `0` critical, `1` high, `2` medium (default), `3` low, `4` backlog

---

## bv (Beads Viewer) - Robot Flags ONLY

**NEVER run `bv` without flags** - you'll get stuck in the TUI.

```bash
bv --robot-help       # All AI commands
bv --robot-insights   # Graph metrics (PageRank, critical path, cycles)
bv --robot-plan       # Execution plan with parallel tracks
bv --robot-priority   # Priority recommendations with reasoning
```

Use `bd` for CRUD operations, `bv` for graph intelligence.

---

## Agent Mail - Multi-Agent Coordination

### Your Identity

On first `register_agent` call, the server assigns you an adjective+noun name (e.g., `PurpleBear`, `GreenCastle`). **Note your assigned name and use it consistently.**

```python
# First call in session - note the returned name
register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
# Response includes: {"name": "YourAssignedName", ...}
```

| Setting | Value |
|---------|-------|
| Project | `/home/ubuntu` |
| Program | `claude-code` |

### Agent Naming Rules

Names must be **adjective+noun** style:
- `BlueLake`, `GreenCastle`, `RedStone`
- NOT: `claude-code`, `opus-4.5`, `BackendAgent`

### Core Tools

```python
# Reserve files (do this BEFORE editing)
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<your-name>",
    paths=["src/**/*.py", "tests/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="ubuntu-42"
)

# Send message (thread_id = beads issue ID)
send_message(
    project_key="/home/ubuntu",
    sender_name="<your-name>",
    to=["OtherAgent"],  # or [] for thread broadcast
    subject="[ubuntu-42] Status update",
    body_md="Completed the refactor...",
    thread_id="ubuntu-42"
)

# Check inbox
fetch_inbox(project_key="/home/ubuntu", agent_name="<your-name>")

# Release reservations when done
release_file_reservations(project_key="/home/ubuntu", agent_name="<your-name>")
```

### Macros (Faster, Use When Possible)

```python
# Start session: register + reserve + fetch inbox
macro_start_session(...)

# File edit cycle: reserve → edit → release
macro_file_reservation_cycle(...)
```

### Linking Convention

| Context | Value |
|---------|-------|
| Mail `thread_id` | beads issue ID (`ubuntu-42`) |
| Mail subject | `[ubuntu-42] Description` |
| Reservation `reason` | `ubuntu-42` |
| Commit message | Include `ubuntu-42` |

### Service Management

```bash
sudo systemctl status mcp-agent-mail   # Check
sudo systemctl restart mcp-agent-mail  # Restart
# Web UI: http://127.0.0.1:8765/mail
```

---

## qmd - Markdown Search

```bash
qmd search "keyword"     # Fast BM25
qmd vsearch "concept"    # Semantic vector search
qmd query "question"     # Hybrid + reranking (best quality)

qmd add .                # Index current directory
qmd status               # Index health
```

Requires Ollama running (`systemctl status ollama`).

---

## Environment

```bash
# Centralized beads database
export BEADS_DB=/home/ubuntu/.beads/beads.db

# All tools in PATH after: source ~/.bashrc
bd, bv, qmd, ollama
```

### Services

| Service | Port | Command |
|---------|------|---------|
| MCP Agent Mail | 8765 | `sudo systemctl status mcp-agent-mail` |
| Ollama | 11434 | `sudo systemctl status ollama` |

---

## Rules Summary

1. `bd ready` first, always
2. `bd update --status=in_progress` before starting
3. Reserve files via Agent Mail before editing
4. Use issue ID as thread_id everywhere
5. `bd close` when done
6. Never use TodoWrite
7. Never run `bv` without `--robot-*` flags
