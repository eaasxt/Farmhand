# JohnDeere System Architecture

This document describes how the components of JohnDeere work together to provide a multi-agent AI coding environment.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI CODING AGENTS                                   │
│  Claude Code (cc)  │  Codex CLI (cod)  │  Gemini CLI (gmi)                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │    Hooks     │  │  Task Track  │  │  Workflow    │
         │  (Enforce)   │  │  (bd/bv)     │  │  (K&V)       │
         └──────────────┘  └──────────────┘  └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      MCP Agent Mail           │
                    │  (Coordination + Reservations)│
                    │  SQLite: ~/mcp_agent_mail/    │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │   Ollama     │  │    qmd       │  │    UBS       │
         │  (LLM/Embed) │  │  (MD Search) │  │  (Security)  │
         └──────────────┘  └──────────────┘  └──────────────┘
```

## Core Components

### 1. AI Coding Agents

Three AI coding agents are supported, each with "dangerous" mode aliases:

| Agent | Safe Mode | Dangerous Mode | Purpose |
|-------|-----------|----------------|---------|
| Claude Code | `claude` | `cc` | Anthropic's coding agent |
| Codex CLI | `codex` | `cod` | OpenAI's coding agent |
| Gemini CLI | `gemini` | `gmi` | Google's coding agent |

Dangerous modes skip confirmation prompts for faster iteration.

### 2. Task Tracking (Beads)

**bd (Beads CLI)** - Issue and task tracking:
```bash
bd ready                              # Available work
bd create --title="..." --type=task   # Create task
bd update <id> --status in_progress   # Claim
bd close <id> --reason="..."          # Complete
```

**bv (Beads Viewer)** - Graph analysis and prioritization:
```bash
bv --robot-priority    # What to work on next
bv --robot-plan        # Execution order with parallel tracks
bv --robot-insights    # Graph metrics (PageRank, cycles)
```

**Data storage:**
- `BEADS_DB=/home/ubuntu/.beads/beads.db` - SQLite database
- `.beads/issues.jsonl` - Per-project issue export (committed to git)

### 3. Hooks (Enforcement Layer)

Python scripts that intercept Claude Code tool calls:

| Hook | Trigger | Action |
|------|---------|--------|
| `todowrite-interceptor.py` | TodoWrite | Blocks, suggests bd |
| `reservation-checker.py` | Edit/Write | Requires file reservation |
| `mcp-state-tracker.py` | MCP calls | Tracks agent state |
| `session-init.py` | Session start | Clears stale state |
| `git_safety_guard.py` | Bash git | Blocks destructive commands |

See [docs/hooks.md](hooks.md) for details.

### 4. MCP Agent Mail (Coordination)

Multi-agent coordination server providing:

**Agent Registration:**
```python
register_agent(project_key, program, model)
# Returns: {"name": "BlueLake", ...}
```

**File Reservations:**
```python
file_reservation_paths(project_key, agent_name, paths, exclusive, reason)
# Prevents concurrent edits to same files
```

**Messaging:**
```python
send_message(project_key, sender_name, to, subject, body_md)
fetch_inbox(project_key, agent_name)
```

**Architecture:**
- HTTP server at `http://127.0.0.1:8765/mcp/`
- SQLite storage at `~/mcp_agent_mail/storage.sqlite3`
- Systemd service: `mcp-agent-mail.service`

### 5. Knowledge & Vibes (Workflow Framework)

Research-backed workflow system installed as git submodule:

**Skills (18):** Reusable patterns like `/prime`, `/calibrate`, `/execute`

**Slash Commands (7):**
- `/prime` - Session startup
- `/calibrate` - Plan validation
- `/execute` - Parallel execution
- `/next-bead` - Claim next task
- `/decompose-task` - Break down work
- `/ground` - Verify external docs
- `/release` - Pre-ship checklist

**Rules (3):** beads, multi-agent, safety

**Templates (8):** North Star Card, Requirements, ADRs, etc.

**Location:** `~/JohnDeere/vendor/knowledge_and_vibes/` (submodule)

### 6. Supporting Services

**Ollama** - Local LLM for embeddings and reranking:
- Port: 11434
- Models: embeddinggemma, qwen3-reranker, qwen3:0.6b
- Used by: qmd, cm

**qmd** - Markdown semantic search:
```bash
qmd add .              # Index documents
qmd query "concept"    # Semantic search
```

**UBS** - Ultimate Bug Scanner:
```bash
ubs <files>           # Security + quality scan before commit
```

## Data Flow

### Agent Session Lifecycle

```
1. Session Start
   └─> session-init.py clears stale state

2. Registration
   └─> register_agent() → MCP Agent Mail
   └─> mcp-state-tracker.py records in state file

3. Claim Task
   └─> bd update <id> --status in_progress

4. Reserve Files
   └─> file_reservation_paths() → MCP Agent Mail SQLite

5. Edit Files
   └─> reservation-checker.py validates each Edit/Write

6. Commit
   └─> ubs <files> (mandatory security scan)
   └─> git commit (with .beads/issues.jsonl)

7. Release
   └─> release_file_reservations()
   └─> bd close <id>
```

### Multi-Agent Coordination

```
Agent A                     Agent B
   │                           │
   ├─ register_agent()         ├─ register_agent()
   │  → "BlueLake"             │  → "GreenSnow"
   │                           │
   ├─ reserve(src/api/**)      │
   │  → granted                │
   │                           ├─ reserve(src/api/**)
   │                           │  → CONFLICT (BlueLake has it)
   │                           │
   │                           ├─ reserve(src/frontend/**)
   │                           │  → granted
   │                           │
   ├─ send_message(GreenSnow)  │
   │  "API done, releasing"    │
   │                           │
   ├─ release(src/api/**)      ├─ fetch_inbox()
   │                           │  → sees message
   │                           │
   │                           ├─ reserve(src/api/**)
   │                           │  → granted
```

## File Locations

### Configuration

| Path | Purpose |
|------|---------|
| `~/.claude/settings.json` | Hook configuration |
| `~/.claude/hooks/` | Hook scripts |
| `~/.claude/agent-state.json` | Agent state (single-agent) |
| `~/.claude/state-{NAME}.json` | Agent state (multi-agent) |
| `~/CLAUDE.md` | Workflow instructions |
| `~/.config/ntm/command_palette.md` | NTM prompts |

### Data

| Path | Purpose |
|------|---------|
| `~/.beads/beads.db` | Beads SQLite database |
| `~/mcp_agent_mail/storage.sqlite3` | MCP Agent Mail SQLite |
| `~/mcp_agent_mail/.env` | MCP Agent Mail config |

### Binaries

| Path | Tools |
|------|-------|
| `~/.local/bin/` | bd, bd-cleanup, cass wrapper |
| `/home/linuxbrew/.linuxbrew/bin/` | bv, ubs, ntm, cm, caam |
| `~/.bun/bin/` | bun, bunx |

### Services

| Service | Unit File |
|---------|-----------|
| `mcp-agent-mail` | `/etc/systemd/system/mcp-agent-mail.service` |
| `ollama` | `/etc/systemd/system/ollama.service` |

## Error Handling

### Hook Failures

Hooks follow "fail open" policy - if they crash, edits are allowed to prevent blocking work entirely.

### Service Failures

```bash
# Check status
sudo systemctl status mcp-agent-mail ollama

# View logs
sudo journalctl -u mcp-agent-mail -f
sudo journalctl -u ollama -f

# Restart
sudo systemctl restart mcp-agent-mail
sudo systemctl restart ollama
```

### Crash Recovery

```bash
bd-cleanup --list        # View orphaned state
bd-cleanup --force       # Release stale reservations
bd-cleanup --reset-state # Reset local state only
```

## Security Considerations

1. **UBS is mandatory** before commits - ~40% of LLM-generated code has vulnerabilities

2. **File reservations** prevent merge conflicts in multi-agent scenarios

3. **git_safety_guard** blocks destructive commands like `git reset --hard`

4. **No secrets in code** - hooks don't check this; use UBS + manual review

5. **Local-only by default** - MCP Agent Mail listens on 127.0.0.1 only
