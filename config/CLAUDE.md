# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

---

## STOP - Read Before Any Action

```bash
bd ready        # What can I work on?
bd stats        # Project health check
```

### ENFORCED RULES - Hooks Will Block Violations

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TodoWrite is BLOCKED         -> Hook redirects to bd commands              │
│  Edit/Write without reserve   -> Hook blocks until file_reservation_paths() │
│  Work before registration     -> Hook blocks until register_agent()         │
│  bv without --robot-*         -> TUI will hang the agent                    │
│  Work without bd issue ID     -> Untracked work is lost work                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**These are not suggestions - they are enforced by hooks in `~/.claude/settings.json`**

---

## Enforcement Architecture

### What's Enforced Automatically

| Rule | Enforcement | Location |
|------|-------------|----------|
| No TodoWrite | PreToolUse hook blocks & suggests bd | `todowrite-interceptor.py` |
| Must register before editing | PreToolUse hook checks state | `reservation-checker.py` |
| Must reserve files before editing | PreToolUse hook checks reservations | `reservation-checker.py` |
| No destructive git commands | PreToolUse hook blocks dangerous git ops | `git_safety_guard.py` |
| State tracking | PostToolUse hook tracks MCP calls | `mcp-state-tracker.py` |
| Session cleanup | SessionStart hook clears stale state | `session-init.py` |

### Hook Files

```
~/.claude/
├── settings.json              # Hook configuration
├── hooks/
│   ├── todowrite-interceptor.py    # Blocks TodoWrite, suggests bd
│   ├── reservation-checker.py      # Enforces file reservations
│   ├── mcp-state-tracker.py        # Tracks agent state
│   ├── session-init.py             # Session startup cleanup
│   └── git_safety_guard.py         # Blocks destructive git commands
└── agent-state.json           # Current agent state (auto-managed)
```

---

## The Workflow (Enforced Sequence)

### Phase 1: Find Work

```bash
# Check what's available
bd ready

# Claim an issue
bd update <id> --status=in_progress
```

### Phase 2: Agent Identity (REQUIRED before editing)

**Option A: AGENT_NAME Environment Variable (Preferred for multi-agent)**

When using `ntm spawn`, each agent pane automatically gets `AGENT_NAME` set to its pane name (e.g., `myproject__cc_1`). This is the intended design from MCP Agent Mail and avoids conflicts when multiple agents share `~/.claude/agent-state.json`.

```bash
# Set manually if not using ntm:
export AGENT_NAME="MyAgentName"
claude
```

**Option B: register_agent() MCP Call (Single agent)**

```python
# This MUST happen before any Edit/Write operations
response = register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
# Response: {"name": "BlueLake", ...}
# SAVE THIS NAME - you need it for all subsequent calls
```

**If you skip this step, the reservation-checker hook will block all Edit/Write operations.**

### Phase 3: Reserve Files (REQUIRED before editing)

```python
# Reserve the files you'll edit
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<your-assigned-name>",  # e.g., "BlueLake" from register
    paths=["path/to/files/**/*.py"],    # Glob patterns work
    ttl_seconds=3600,                   # 1 hour default
    exclusive=True,
    reason="<issue-id>"                 # e.g., "ubuntu-42" - REQUIRED
)
```

**If you skip this step, the reservation-checker hook will block all Edit/Write operations.**

### Phase 4: Work

```bash
# Now you can safely edit files
# The hooks have verified:
#   1. You're registered
#   2. You have the files reserved
#   3. No other agent has conflicting reservations
```

### Phase 5: Cleanup

```python
# Release reservations when done editing
release_file_reservations(
    project_key="/home/ubuntu",
    agent_name="<your-assigned-name>"
)
```

```bash
# Close the issue
bd close <id> --reason="Implemented X"
```

---

## TodoWrite Replacement Reference

The `todowrite-interceptor.py` hook blocks TodoWrite and tells you what to use instead:

| Instead of TodoWrite | Use bd |
|----------------------|--------|
| Creating todos | `bd create --title="..." --type=task` |
| Marking in_progress | `bd update <id> --status=in_progress` |
| Marking completed | `bd close <id> --reason="..."` |
| Listing todos | `bd ready` |

---

## Error Recovery

### If You Get Blocked by Hooks

**"Agent not registered"**
```python
register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
```

**"File not reserved"**
```python
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<your-name>",
    paths=["path/to/file.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)
```

**"File reserved by another agent"**
```python
# Option 1: Message the other agent
send_message(
    project_key="/home/ubuntu",
    sender_name="<your-name>",
    to=["<other-agent>"],
    subject="File access request",
    body_md="Need access to <file>. Can you release when done?"
)

# Option 2: Wait and check
fetch_inbox(project_key="/home/ubuntu", agent_name="<your-name>")
```

### Crash Recovery

If a session crashes or is interrupted:

```bash
# Check for orphaned state
bd-cleanup --list

# Interactive cleanup
bd-cleanup

# Force cleanup (removes stale reservations > 4 hours old)
bd-cleanup --force

# Nuclear option (releases ALL reservations)
bd-cleanup --release-all

# Just reset local state
bd-cleanup --reset-state
```

### Service Issues

```bash
# MCP Agent Mail down?
sudo systemctl status mcp-agent-mail
sudo systemctl restart mcp-agent-mail
journalctl -u mcp-agent-mail -f

# Ollama down?
sudo systemctl status ollama
sudo systemctl restart ollama
```

---

## Multi-Agent Collaboration Patterns

### Pattern 1: Sequential Handoff

Agent A finishes, Agent B picks up:

```python
# Agent A: Done with work, announce completion
send_message(
    project_key="/home/ubuntu",
    sender_name="AgentA",
    to=[],  # Broadcast
    subject="[ubuntu-42] Phase 1 complete",
    body_md="Backend API done. Frontend work unblocked.",
    thread_id="ubuntu-42"
)
release_file_reservations(project_key="/home/ubuntu", agent_name="AgentA")
```

```bash
# Agent A: Update issue
bd close ubuntu-42 --reason="Phase 1 complete"
bd update ubuntu-43 --status=open  # Unblock next phase
```

```python
# Agent B: Pick up the work
fetch_inbox(project_key="/home/ubuntu", agent_name="AgentB")
# See the message, know context
```

### Pattern 2: Parallel Work (Non-Overlapping Files)

Two agents work simultaneously on different parts:

```python
# Agent A: Reserve backend files
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="AgentA",
    paths=["src/backend/**/*.py", "tests/backend/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="ubuntu-42-backend"
)

# Agent B: Reserve frontend files (no conflict)
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="AgentB",
    paths=["src/frontend/**/*.tsx", "tests/frontend/**/*.tsx"],
    ttl_seconds=3600,
    exclusive=True,
    reason="ubuntu-42-frontend"
)
```

### Pattern 3: Coordinated Access (Same Files)

When agents need the same files at different times:

```python
# Agent A: Working on file, will need to share
send_message(
    project_key="/home/ubuntu",
    sender_name="AgentA",
    to=["AgentB"],
    subject="[ubuntu-42] Will release config.py in 10min",
    body_md="Finishing refactor. Will ping when done.",
    thread_id="ubuntu-42"
)

# Agent A: Done, release and notify
release_file_reservations(project_key="/home/ubuntu", agent_name="AgentA")
send_message(
    project_key="/home/ubuntu",
    sender_name="AgentA",
    to=["AgentB"],
    subject="[ubuntu-42] config.py released",
    body_md="All yours!",
    thread_id="ubuntu-42"
)

# Agent B: Now safe to reserve
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="AgentB",
    paths=["src/config.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="ubuntu-42"
)
```

### Pattern 4: Blocking on Another Agent

When your work depends on another agent's output:

```python
# Create a dependency in beads
```

```bash
bd dep ubuntu-43 ubuntu-44  # 43 blocks 44
```

```python
# Monitor for completion
send_message(
    project_key="/home/ubuntu",
    sender_name="AgentB",
    to=["AgentA"],
    subject="[ubuntu-43] Waiting on your completion",
    body_md="I'm blocked on ubuntu-44 until ubuntu-43 is done.",
    thread_id="ubuntu-43"
)
```

### Pattern 5: Emergency Takeover

If an agent appears stuck/crashed:

```bash
# Check the situation
bd-cleanup --list

# If confirmed abandoned (> 4 hours stale)
bd-cleanup --force

# Or target specific reservation
bd-cleanup  # Interactive mode
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
bd activity                           # Recent activity log

# WRITE
bd create --title="..." --type=task   # New issue
bd update <id> --status=in_progress   # Claim work
bd close <id> --reason="Done"         # Complete
bd dep <blocker> <blocked>            # A blocks B
bd pin <id>                           # Pin important bead
bd unpin <id>                         # Unpin bead

# MOLECULAR BONDING (v0.33+)
bd mol                                # Show molecular bonds
bd cook                               # Process pending bonds
bd ship                               # Ship completed work

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

### Agent Mail - Multi-Agent Coordination

```python
# Register (REQUIRED first)
register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
# Response: {"name": "BlueLake", ...}

# Reserve files (REQUIRED before editing)
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<your-name>",
    paths=["src/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)

# Send message
send_message(
    project_key="/home/ubuntu",
    sender_name="<your-name>",
    to=["OtherAgent"],  # or [] for broadcast
    subject="[<issue-id>] Subject",
    body_md="Message...",
    thread_id="<issue-id>"
)

# Check inbox
fetch_inbox(project_key="/home/ubuntu", agent_name="<your-name>")

# Release when done
release_file_reservations(project_key="/home/ubuntu", agent_name="<your-name>")
```

**Macros (Faster):**

```python
macro_start_session(...)            # register + reserve + fetch inbox
macro_file_reservation_cycle(...)   # reserve -> edit -> release
```

### qmd - Markdown Search

```bash
qmd search "keyword"     # Fast BM25 search
qmd vsearch "concept"    # Semantic vector search
qmd query "question"     # Hybrid + reranking (best quality)
qmd add .                # Index current directory
```

### bd-cleanup - Recovery Utility

```bash
bd-cleanup              # Interactive cleanup
bd-cleanup --list       # List orphaned items
bd-cleanup --force      # Force cleanup stale items
bd-cleanup --release-all # Nuclear: release everything
bd-cleanup --reset-state # Reset local agent state only
```

---

## Environment

```bash
export BEADS_DB=/home/ubuntu/.beads/beads.db
export PATH="/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:$PATH"
```

**Services:**

| Service | Port | Check Command |
|---------|------|---------------|
| MCP Agent Mail | 8765 | `sudo systemctl status mcp-agent-mail` |
| Ollama | 11434 | `sudo systemctl status ollama` |

**Project Structure:**

```
/home/ubuntu/
├── .beads/              # Beads database
├── .claude/
│   ├── settings.json    # Hook configuration
│   ├── hooks/           # Enforcement hooks
│   └── agent-state.json # Current agent state (or state-{AGENT_NAME}.json)
├── mcp_agent_mail/      # Agent Mail server (SQLite in storage.sqlite3)
├── templates/
│   └── AGENTS.md        # Template for project coordination
├── CLAUDE.md            # This file (tool instructions)
└── <project>/
    └── AGENTS.md        # Per-project agent coordination
```

**Two Key Files:**

| File | Location | Purpose |
|------|----------|---------|
| `CLAUDE.md` | `~/CLAUDE.md` | Global tool instructions (hooks, commands, workflow) |
| `AGENTS.md` | `<project>/AGENTS.md` | Per-project coordination (agents, work, conventions) |

Copy `~/templates/AGENTS.md` to each project root for multi-agent work.

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

## Quick Decision Tree

```
Need to track work?           -> bd create --title="..." --type=task
Need to see what to do?       -> bd ready
Need graph analysis?          -> bv --robot-priority
Need to edit files?           -> register_agent() + file_reservation_paths() FIRST
Need to find docs?            -> qmd query "topic"
Need to message agents?       -> send_message() with thread_id=<issue-id>
Session crashed?              -> bd-cleanup
```

---

## Rules Summary (Enforced)

1. `bd ready` first, always
2. `bd update --status=in_progress` before starting
3. `register_agent()` - **ENFORCED: hooks block edits without this**
4. `file_reservation_paths()` - **ENFORCED: hooks block edits without this**
5. Use issue ID as `thread_id` everywhere
6. `release_file_reservations()` when done editing
7. `bd close` when done with issue
8. TodoWrite is **BLOCKED** - use bd instead
9. Never run `bv` without `--robot-*` flags
10. Use `bd-cleanup` for crash recovery

````markdown
## UBS Quick Reference for AI Agents

UBS stands for "Ultimate Bug Scanner": **The AI Coding Agent's Secret Weapon: Flagging Likely Bugs for Fixing Early On**

**Install:** `curl -sSL https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/main/install.sh | bash`

**Dependency:** UBS v5.0.0+ REQUIRES `ast-grep` for JavaScript/TypeScript scanning.

**Golden Rule:** `ubs <changed-files>` before every commit. Exit 0 = safe. Exit >0 = fix & re-run.

**Commands:**
```bash
ubs file.ts file2.py                    # Specific files (< 1s) — USE THIS
ubs $(git diff --name-only --cached)    # Staged files — before commit
ubs --only=js,python src/               # Language filter (3-5x faster)
ubs --ci --fail-on-warning .            # CI mode — before PR
ubs --help                              # Full command reference
ubs sessions --entries 1                # Tail the latest install session log
ubs .                                   # Whole project (ignores things like .venv and node_modules automatically)
```

**Suppression Markers (v5.0.0+):**
```python
x = foo()  # ubs:ignore - Intentional pattern
y = bar()  # nolint - Also works
z = baz()  # noqa - Python-style also supported
```

**Output Format:**
```
⚠️  Category (N errors)
    file.ts:42:5 – Issue description
    💡 Suggested fix
Exit code: 1
```
Parse: `file:line:col` → location | 💡 → how to fix | Exit 0/1 → pass/fail

**Fix Workflow:**
1. Read finding → category + fix suggestion
2. Navigate `file:line:col` → view context
3. Verify real issue (not false positive)
4. Fix root cause (not symptom)
5. Re-run `ubs <file>` → exit 0
6. Commit

**Speed Critical:** Scope to changed files. `ubs src/file.ts` (< 1s) vs `ubs .` (30s). Never full scan for small edits.

**Bug Severity:**
- **Critical** (always fix): Null safety, XSS/injection, async/await, memory leaks
- **Important** (production): Type narrowing, division-by-zero, resource leaks
- **Contextual** (judgment): TODO/FIXME, console logs

**Anti-Patterns:**
- ❌ Ignore findings → ✅ Investigate each
- ❌ Full scan per edit → ✅ Scope to file
- ❌ Fix symptom (`if (x) { x.y }`) → ✅ Root cause (`x?.y`)
````

---

## Safety Rules

### Absolute Prohibition on Deletions

You may **NOT** delete any file or directory unless the user explicitly gives the exact command **in the current session**.

This applies to:
- All existing files (even ones you just created)
- Directories and their contents
- Git operations like `git reset --hard`, `git clean -fd`
- Database drops or truncates

**Destructive operations require:**
1. Explicit written approval in the current session
2. The exact file/directory path confirmed by the user
3. A stated reason for the deletion

**Instead of deleting:**
- Rename files with `.bak` or `.old` suffix
- Move to a `.archive/` directory
- Comment out code rather than removing it

---

## Session Completion Protocol

Before ending a session, complete this checklist:

### 1. Quality Gates
```bash
ubs $(git diff --name-only)     # Scan changed files
bd stats                         # Check project health
```

### 2. Commit Changes
```bash
git add -A
git commit -m "[issue-id] Description

- What was done
- Why it was done
- Any follow-up needed"
```

### 3. Push to Remote (Mandatory)
```bash
git push origin <branch>
```

**Work is NOT complete until `git push` succeeds.**

### 4. Update Beads
```bash
bd close <issue-id> --reason="Completed: <summary>"
# Or if not finished:
bd update <issue-id> --status=open  # Release for others
```

### 5. Release Reservations
```python
release_file_reservations(
    project_key="/home/ubuntu",
    agent_name="<your-name>"
)
```

### 6. Handoff Context
If work continues in another session, leave a message:
```python
send_message(
    project_key="/home/ubuntu",
    sender_name="<your-name>",
    to=[],  # Broadcast
    subject="[issue-id] Session handoff",
    body_md="## Status\n- Completed X\n- Remaining: Y\n- Blocked on: Z",
    thread_id="<issue-id>"
)
```

---

## Code Quality Standards

### Technology Stack
- **JavaScript/TypeScript:** Use `bun` exclusively (no npm, yarn, pnpm)
- **Python:** Use `uv` for package management
- **Shell:** POSIX-compatible bash

### Code Discipline
- Favor explicit, reviewable edits over bulk modifications
- Avoid backwards-compatibility shims when you can just change the code
- Optimize for clean design now rather than legacy support

### Before Committing
1. Run `ubs <changed-files>` - fix all findings
2. Run tests if they exist
3. Check for secrets/credentials in staged files

---

## NTM (Named Tmux Manager)

Orchestrate multiple AI agents in tmux sessions.

### Quick Start
```bash
ntm spawn myproject --cc=2 --cod=1    # 2 Claude + 1 Codex agents
ntm attach myproject                   # Connect to session
ntm palette                            # Command palette (F6 in tmux)
ntm ls                                 # List sessions
ntm dashboard                          # Dashboard 360-View (v1.2.0+)
```

### New Features (v1.2.0+)
- **Dashboard 360-View**: Bird's-eye view of all agent sessions
- **CASS robot mode integration**: Automatic session search
- **File change tracking**: Track which agent modified each file
- **Clipboard integration**: Easy copy/paste between agents

### Command Palette
Press **F6** in tmux (after `ntm bind`) to open the palette with 40+ pre-built prompts:

| Category | Examples |
|----------|----------|
| Analysis | Fresh review, check other agents' work, apply UBS |
| Coding | Fix bug, create tests, build UI/UX |
| Planning | Turn plan into beads, use bv for priorities |
| Git | Commit changes, do GH flow |
| Coordination | Check mail, introduce to agents |

Palette file: `~/.config/ntm/command_palette.md`

---

## Additional Stack Tools

### cass - Coding Agent Session Search
```bash
cass search "error handling"    # Search all agent session history
cass export                     # Export sessions (v0.1.32+)
cass expand                     # Expand context (v0.1.32+)
cass timeline                   # Timeline view (v0.1.32+)
cass --help                     # Full options
```
*Supports: Claude Code, Codex, Pi-Agent, Cursor IDE, ChatGPT Desktop*
*Note: Requires GLIBC 2.39+ (Ubuntu 24.04+)*

### cm - CASS Memory System
```bash
cm --version                    # Procedural memory for agents
cm doctor --json                # Health check
```

### caam - Coding Agent Account Manager
```bash
caam status                     # Show active profiles
caam backup claude my-account   # Backup auth
caam activate claude other      # Switch accounts
caam ls                         # List saved profiles
```

### slb - Simultaneous Launch Button
Two-person rule for dangerous commands (requires confirmation from another agent).
*Note: No binary releases yet*

---

## Vibe Mode Aliases

Quick access to AI agents with dangerous permissions enabled:

| Alias | Command | Mode |
|-------|---------|------|
| `cc` | `claude --dangerously-skip-permissions` | Skip all prompts |
| `cod` | `bunx codex --approval-mode full-auto` | Auto-approve all |
| `gmi` | `bunx gemini --yolo` | YOLO mode |

Safe alternatives:
- `claude-safe`, `codex-safe`, `gemini-safe`

---

## Modern CLI Aliases

| Alias | Tool | Purpose |
|-------|------|---------|
| `ls`, `ll`, `la`, `lt` | lsd | Better ls with icons |
| `cat` | bat | Syntax highlighting |
| `lg` | lazygit | Git TUI |
| `z` | zoxide | Smart cd |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  START SESSION                                                              │
│    bd ready → bd update <id> --status=in_progress                          │
│    register_agent() → file_reservation_paths()                             │
│                                                                             │
│  WORK                                                                       │
│    Edit files → ubs <files> → commit                                       │
│    ntm palette (F6) for common prompts                                     │
│                                                                             │
│  END SESSION                                                                │
│    ubs → git push → bd close → release_file_reservations()                 │
│                                                                             │
│  MULTI-AGENT                                                                │
│    ntm spawn proj --cc=2 --cod=1                                           │
│    send_message() / fetch_inbox() for coordination                         │
│    File reservations prevent conflicts                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```
