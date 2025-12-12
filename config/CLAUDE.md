# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## STOP - Read Before Any Action

```bash
bd ready        # What can I work on?
bd stats        # Project health check
```

### FORBIDDEN - These Will Break Your Workflow

```
┌────────────────────────────────────────────────────────────────────┐
│  NEVER use TodoWrite tool         -> use bd commands instead       │
│  NEVER run bv without --robot-*   -> TUI will hang the agent       │
│  NEVER edit files without reservation -> causes merge conflicts    │
│  NEVER work without a bd issue ID -> untracked work is lost work   │
└────────────────────────────────────────────────────────────────────┘
```

---

## TodoWrite is FORBIDDEN - Use bd Instead

| Instead of TodoWrite | Use bd |
|----------------------|--------|
| Creating todos | `bd create --title="..." --type=task` |
| Marking in_progress | `bd update <id> --status=in_progress` |
| Marking completed | `bd close <id>` |
| Listing todos | `bd ready` |

---

## The Workflow (Follow Exactly)

```bash
# 1. Find work
bd ready

# 2. Claim it
bd update <id> --status=in_progress
```

```python
# 3. Register and get your assigned name (first call only)
response = register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
# Response: {"name": "BlueLake", ...}  <-- Use this name for ALL subsequent calls

# 4. Reserve files BEFORE editing
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<your-assigned-name>",  # e.g., "BlueLake"
    paths=["path/to/files/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"                 # e.g., "ubuntu-42"
)

# 5. Announce work (good practice)
send_message(
    project_key="/home/ubuntu",
    sender_name="<your-assigned-name>",
    to=[],                              # Empty = broadcast to thread
    subject="[<issue-id>] Starting work",
    body_md="Working on X...",
    thread_id="<issue-id>"
)
```

```bash
# 6. Do the work
# ... edit files, run tests, etc.
```

```python
# 7. Release reservations
release_file_reservations(
    project_key="/home/ubuntu",
    agent_name="<your-assigned-name>"
)
```

```bash
# 8. Close the issue
bd close <id> --reason="Implemented X"
```

### If You Discover New Work While Working

```bash
bd create --title="Found: new thing" --type=task --deps discovered-from:<current-id>
```

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

**Priority:** `0` critical | `1` high | `2` medium (default) | `3` low | `4` backlog

### bv (Beads Viewer) - Graph Intelligence

**NEVER run `bv` without `--robot-*` flags** - TUI will hang the agent.

```bash
bv --robot-help                    # List all safe commands
bv --robot-plan                    # Execution order with parallel tracks
bv --robot-priority                # What to work on + reasoning
bv --robot-insights                # Graph metrics (PageRank, cycles, critical path)
bv --robot-diff --diff-since "1h"  # Recent changes
```

| Use bd for | Use bv for |
|------------|------------|
| CRUD operations | Graph analysis |
| "What's next?" | Impact assessment |
| Status updates | Parallel planning |

### Agent Mail - Multi-Agent Coordination

**Agent Naming:** On `register_agent`, the server assigns you an adjective+noun name (e.g., `BlueLake`, `GreenCastle`). Note your assigned name and use it for ALL subsequent calls.

```python
# First call - note the returned name
register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
# Response: {"name": "BlueLake", ...}
```

**Valid names:** `BlueLake`, `GreenCastle`, `RedStone`
**Invalid names:** `claude-code`, `opus-4.5`, `BackendAgent`

**Core Tools:**

```python
# Reserve files (BEFORE editing)
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

# Release when done
release_file_reservations(project_key="/home/ubuntu", agent_name="<your-name>")
```

**Macros (Faster - Use When Possible):**

```python
macro_start_session(...)            # register + reserve + fetch inbox
macro_file_reservation_cycle(...)   # reserve -> edit -> release
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
qmd add .                # Index current directory
qmd status               # Index health
qmd get "file.md"        # Retrieve content
```

**Options:** `-n 10` (limit) | `--json` (parseable) | `--files` (paths only) | `--min-score 0.5`

Requires Ollama running (`systemctl status ollama`).

---

## Environment

```bash
export BEADS_DB=/home/ubuntu/.beads/beads.db
```

**Services:**

| Service | Port | Check Command |
|---------|------|---------------|
| MCP Agent Mail | 8765 | `sudo systemctl status mcp-agent-mail` |
| Ollama | 11434 | `sudo systemctl status ollama` |

**Project Structure:**

```
/home/ubuntu/
├── .beads/              # Beads database (BEADS_DB)
├── .mcp_agent_mail/     # Agent Mail storage
├── mcp_agent_mail/      # Agent Mail server
└── CLAUDE.md            # This file
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

---

## Anti-Patterns

| Pattern | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| TodoWrite tool | Duplicates beads, loses sync | `bd create/update/close` |
| `bv` without `--robot-*` | TUI hangs the agent | `bv --robot-plan` |
| Edit without reservation | Conflicts with other agents | `file_reservation_paths()` first |
| Work without issue ID | Untracked, no context | `bd create` then work |
| Hardcoding agent name | Name assigned by server | Use response from `register_agent` |
| Forgetting to release | Blocks other agents | `release_file_reservations()` |

---

## Quick Decision Tree

```
Need to track work?           -> bd create --title="..." --type=task
Need to see what to do?       -> bd ready
Need graph analysis?          -> bv --robot-priority
Need to edit files?           -> file_reservation_paths() FIRST
Need to find docs?            -> qmd query "topic"
Need to message agents?       -> send_message() with thread_id=<issue-id>
```

---

## Rules Summary (Quick Check)

1. `bd ready` first, always
2. `bd update --status=in_progress` before starting
3. `register_agent` to get your name
4. Reserve files via Agent Mail before editing
5. Use issue ID as `thread_id` everywhere
6. `release_file_reservations` when done editing
7. `bd close` when done with issue
8. Never use TodoWrite
9. Never run `bv` without `--robot-*` flags
