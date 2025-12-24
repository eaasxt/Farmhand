# JohnDeere Quickstart Guide

Get up and running with JohnDeere in 5 minutes.

## Prerequisites

- Ubuntu 22.04+ VPS (8GB+ RAM recommended)
- Internet connection
- SSH access

## Installation

```bash
# Clone and install
git clone https://github.com/eaasxt/JohnDeere.git ~/JohnDeere
cd ~/JohnDeere
./install.sh
```

The installer takes 10-15 minutes and sets up:
- Core tools (bd, bv, qmd)
- AI agents (Claude Code, Codex, Gemini)
- Multi-agent coordination (MCP Agent Mail)
- Enforcement hooks
- Shell environment (zsh + Powerlevel10k)

## Post-Install Setup

### 1. Switch to zsh

```bash
exec zsh
```

### 2. Authenticate AI Agents

```bash
claude                        # OAuth flow
codex login --device-auth     # Device code flow
gemini                        # Follow prompts
```

### 3. Verify Installation

```bash
./scripts/verify.sh
```

## Your First Session

### Check Available Work

```bash
bd ready                    # What's available
bd stats                    # Project health
```

### Register and Reserve Files

Before editing any files, you must register and reserve:

```python
# Option A: Use macro (recommended)
macro_start_session(
    human_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5",
    file_reservation_paths=["src/**/*.py"]
)

# Option B: Manual steps
register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
# Note your assigned name (e.g., "BlueLake")

file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="BlueLake",  # Your assigned name
    paths=["src/**/*.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="issue-id"
)
```

### Work on Files

Now you can edit files. The hooks enforce:
- Registration required before editing
- File reservation required before editing
- TodoWrite blocked (use `bd` instead)

### Clean Up

```bash
# Release reservations
release_file_reservations(
    project_key="/home/ubuntu",
    agent_name="BlueLake"
)

# Close your issue
bd close <issue-id> --reason="Completed: description"
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `bd ready` | List available work |
| `bd stats` | Project health check |
| `bd create --title="..." --type=task` | Create new task |
| `bd close <id> --reason="..."` | Complete task |
| `bv --robot-priority` | What to work on next |
| `ubs <files>` | Security scan before commit |
| `ntm spawn proj --cc=2` | Spawn multi-agent session |
| `cc` | Claude in dangerous mode |
| `cod` | Codex in full-auto mode |

## Hooks Enforcement

JohnDeere installs hooks that enforce the workflow:

| Hook | What It Does |
|------|--------------|
| `todowrite-interceptor.py` | Blocks TodoWrite, suggests `bd` |
| `reservation-checker.py` | Blocks edits without file reservation |
| `mcp-state-tracker.py` | Tracks agent state |
| `session-init.py` | Cleans stale state on startup |
| `git_safety_guard.py` | Blocks destructive git commands |

If a hook blocks you, it will tell you exactly what to do.

## Crash Recovery

If a session crashes:

```bash
bd-cleanup              # Interactive cleanup
bd-cleanup --list       # View orphaned state
bd-cleanup --force      # Force cleanup stale items
```

## Multi-Agent Workflow

```bash
# Spawn 2 Claude + 1 Codex agents
ntm spawn myproject --cc=2 --cod=1

# Attach to session
ntm attach myproject

# Open command palette (in tmux)
F6
```

Agents coordinate via MCP Agent Mail:
- File reservations prevent conflicts
- Messages enable handoff
- Hooks enforce the protocol

## Next Steps

- Read `~/CLAUDE.md` for the complete workflow guide
- Check `~/JohnDeere/docs/troubleshooting.md` for common issues
- Explore `bv --robot-help` for graph analysis options

## Quick Reference

```
Start:     bd ready -> bd update <id> --status in_progress
Register:  register_agent() or AGENT_NAME env var
Reserve:   file_reservation_paths()
Work:      Edit files -> ubs <files> -> commit
Release:   release_file_reservations()
Close:     bd close <id> --reason="..."
```
