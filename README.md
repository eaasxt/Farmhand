<div align="center">

# 🚜 Farmhand

### Transform a Fresh Ubuntu VPS into a Multi-Agent AI Coding Powerhouse

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/eaasxt/Farmhand)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04%20%7C%2024.04-orange.svg)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Tests](https://img.shields.io/badge/tests-88%20passing-brightgreen.svg)](#testing)
[![Tools](https://img.shields.io/badge/tools-30%2B-purple.svg)](#-what-gets-installed)

*One command. 30+ tools. Multiple AI agents working in harmony.*

</div>

---

## 📋 TL;DR

**Farmhand** takes a bare Ubuntu VPS and installs everything you need to run multiple AI coding agents (Claude, Codex, Gemini) that can work together without stepping on each other's toes.

```bash
git clone https://github.com/eaasxt/Farmhand.git ~/Farmhand
cd ~/Farmhand && ./install.sh
```

**What makes it special:**
- 🤖 **Multi-agent coordination** — File reservations prevent merge conflicts between agents
- 🔒 **Enforcement hooks** — Agents can't skip the workflow, even if they want to
- 📊 **Graph-based task tracking** — Dependencies, priorities, and parallel execution paths
- 🔬 **Research-backed protocols** — 50+ papers distilled into actionable workflows

---

## 🎯 Who Is This For?

<table>
<tr>
<td width="33%">

### 👶 Beginners
"I have a VPS and want AI agents writing code for me"

→ Run `./install.sh` and follow the prompts

</td>
<td width="33%">

### 👨‍💻 Developers
"I want reproducible multi-agent setups"

→ Idempotent installer, version-controlled configs

</td>
<td width="33%">

### 👥 Teams
"We need multiple agents coordinating on one codebase"

→ File reservations, messaging, conflict prevention

</td>
</tr>
</table>

---

## ⚡ Quick Start

```bash
# 1. Clone and install (15-20 minutes)
git clone https://github.com/eaasxt/Farmhand.git ~/Farmhand
cd ~/Farmhand && ./install.sh

# 2. Switch to configured shell
exec zsh

# 3. Authenticate your AI agents
claude                      # OAuth flow
codex login --device-auth   # Device code
gemini                      # Follow prompts

# 4. Verify everything works
./scripts/verify.sh

# 5. Start working
bd ready                    # See available tasks
ntm spawn myproject --cc=2  # Spawn 2 Claude agents
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              YOUR VPS (Ubuntu 22.04+)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         AI CODING AGENTS                                  │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                     │   │
│  │  │ Claude Code │   │  Codex CLI  │   │ Gemini CLI  │                     │   │
│  │  │    (cc)     │   │    (cod)    │   │    (gmi)    │                     │   │
│  │  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                     │   │
│  └─────────┼─────────────────┼─────────────────┼───────────────────────────┘   │
│            │                 │                 │                                │
│            ▼                 ▼                 ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      ENFORCEMENT LAYER (Hooks)                           │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │ TodoWrite    │ │ Reservation  │ │ Git Safety   │ │ State        │    │   │
│  │  │ Interceptor  │ │ Checker      │ │ Guard        │ │ Tracker      │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│            │                 │                 │                                │
│            ▼                 ▼                 ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      COORDINATION LAYER                                   │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │ MCP Agent    │ │ Beads (bd)   │ │ Beads Viewer │ │ NTM          │    │   │
│  │  │ Mail         │ │ Task Graph   │ │ (bv)         │ │ Orchestrator │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│            │                 │                 │                                │
│            ▼                 ▼                 ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      FOUNDATION LAYER                                     │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │ Ollama       │ │ UBS Scanner  │ │ CASS Memory  │ │ Modern Shell │    │   │
│  │  │ (Embeddings) │ │ (Security)   │ │ (History)    │ │ (zsh/p10k)   │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Multi-Agent Coordination

```
    Agent A                    MCP Agent Mail                    Agent B
       │                            │                               │
       │  1. register_agent()       │                               │
       │ ─────────────────────────> │                               │
       │  <- "BlueLake"             │                               │
       │                            │                               │
       │  2. file_reservation_paths │                               │
       │     paths=["src/**"]       │                               │
       │ ─────────────────────────> │                               │
       │  <- reserved               │                               │
       │                            │   3. file_reservation_paths   │
       │                            │      paths=["src/**"]         │
       │                            │ <──────────────────────────── │
       │                            │   -> CONFLICT! src/** locked  │
       │                            │                               │
       │  4. Edit src/file.py       │                               │
       │  ✓ Allowed (reserved)      │                               │
       │                            │   5. Edit src/file.py         │
       │                            │   ✗ BLOCKED by hook           │
       │                            │                               │
       │  6. release_reservations   │                               │
       │ ─────────────────────────> │                               │
       │                            │   7. file_reservation_paths   │
       │                            │ <──────────────────────────── │
       │                            │   <- reserved (now allowed)   │
```

---

## 🛠 What Gets Installed

### Core Stack (Essential)

| Tool | Purpose | Docs |
|------|---------|------|
| **[bd](https://github.com/steveyegge/beads)** | Distributed, git-backed graph issue tracker | [README](https://github.com/steveyegge/beads#readme) |
| **[bv](https://github.com/Dicklesworthstone/beads_viewer)** | Terminal UI for beads with graph visualization | [README](https://github.com/Dicklesworthstone/beads_viewer#readme) |
| **[qmd](https://github.com/tobi/qmd)** | Markdown semantic search with local LLM | [README](https://github.com/tobi/qmd#readme) |
| **[MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail)** | Agent messaging & file reservations | [README](https://github.com/Dicklesworthstone/mcp_agent_mail#readme) |

### Dicklesworthstone Stack (8 Tools)

| Tool | Purpose | Docs |
|------|---------|------|
| **[ubs](https://github.com/Dicklesworthstone/ultimate_bug_scanner)** | AI-powered bug scanner, pre-commit security | [README](https://github.com/Dicklesworthstone/ultimate_bug_scanner#readme) |
| **[ntm](https://github.com/Dicklesworthstone/ntm)** | Named Tmux Manager for multi-agent orchestration | [README](https://github.com/Dicklesworthstone/ntm#readme) |
| **[cm](https://github.com/Dicklesworthstone/cass_memory_system)** | Procedural memory system for agents | [README](https://github.com/Dicklesworthstone/cass_memory_system#readme) |
| **[caam](https://github.com/Dicklesworthstone/coding_agent_account_manager)** | Backup/restore agent authentication | [README](https://github.com/Dicklesworthstone/coding_agent_account_manager#readme) |
| **[cass](https://github.com/Dicklesworthstone/coding_agent_session_search)** | Search past agent session transcripts | [README](https://github.com/Dicklesworthstone/coding_agent_session_search#readme) |
| **[slb](https://github.com/Dicklesworthstone/simultaneous_launch_button)** | Two-person rule for dangerous commands | [README](https://github.com/Dicklesworthstone/simultaneous_launch_button#readme) |

### AI Coding Agents

| Agent | Alias | Mode | Auth |
|-------|-------|------|------|
| Claude Code | `cc` | `--dangerously-skip-permissions` | OAuth |
| Codex CLI | `cod` | `--approval-mode full-auto` | Device code |
| Gemini CLI | `gmi` | `--yolo` | OAuth |

### Cloud CLIs

| Tool | Purpose |
|------|---------|
| **vault** | HashiCorp Vault secrets |
| **wrangler** | Cloudflare Workers |
| **supabase** | Supabase backend |
| **vercel** | Vercel deployments |

### Modern Shell

- **zsh** with Oh My Zsh + Powerlevel10k
- **lsd** (better ls), **bat** (better cat), **lazygit**, **fzf**, **zoxide**, **atuin**
- **bun** + **uv** (fast JS/Python package managers)

---

## 🔒 Enforcement Hooks

The magic of Farmhand is that agents **can't cheat**. Hooks intercept tool calls and enforce the workflow:

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOOK ENFORCEMENT LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PreToolUse Hooks (Block BEFORE execution):                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ TodoWrite → BLOCKED → "Use bd create instead"            │   │
│  │ Edit/Write → Check registration → Check reservation      │   │
│  │ Bash(git reset) → BLOCKED → "Destructive command"        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  PostToolUse Hooks (Track AFTER execution):                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ register_agent() → Save agent name to state              │   │
│  │ file_reservation_paths() → Track reservations            │   │
│  │ release_file_reservations() → Clear reservations         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  SessionStart Hooks (Run on session init):                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Clear stale state files                                  │   │
│  │ Detect orphaned reservations                             │   │
│  │ Inject workflow reminders                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Hook Reference

| Hook | Trigger | What It Does |
|------|---------|--------------|
| `todowrite-interceptor.py` | `TodoWrite` | Blocks and suggests `bd` commands |
| `reservation-checker.py` | `Edit`, `Write` | Requires registration + reservation |
| `git_safety_guard.py` | `Bash` | Blocks destructive git commands |
| `mcp-state-tracker.py` | MCP calls | Tracks agent state after MCP operations |
| `session-init.py` | Session start | Cleans stale state, shows reminders |

### Escape Hatch

For experienced users who need to bypass enforcement:

```bash
export FARMHAND_SKIP_ENFORCEMENT=1
claude  # Now hooks won't block
unset FARMHAND_SKIP_ENFORCEMENT
```

---

## 📖 The Workflow

### Required Sequence

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           ENFORCED WORKFLOW                                     │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   1. FIND WORK                 2. REGISTER                 3. RESERVE          │
│   ┌─────────────┐              ┌─────────────┐             ┌─────────────┐     │
│   │ bd ready    │──────────────│ register_   │─────────────│ file_       │     │
│   │ bd update   │              │ agent()     │             │ reservation │     │
│   │ --status=   │              │             │             │ _paths()    │     │
│   │ in_progress │              │ -> "Blue    │             │             │     │
│   └─────────────┘              │    Lake"    │             │ paths=      │     │
│                                └─────────────┘             │ ["src/**"]  │     │
│                                                            └─────────────┘     │
│                                                                                 │
│   4. WORK                      5. COMMIT                   6. CLEANUP          │
│   ┌─────────────┐              ┌─────────────┐             ┌─────────────┐     │
│   │ Edit files  │──────────────│ ubs <files> │─────────────│ release_    │     │
│   │ (hooks      │              │ git commit  │             │ file_       │     │
│   │ allow now)  │              │ git push    │             │ reservations│     │
│   │             │              │             │             │ ()          │     │
│   └─────────────┘              └─────────────┘             │             │     │
│                                                            │ bd close    │     │
│                                                            └─────────────┘     │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Essential Commands

| Action | Command |
|--------|---------|
| See available work | `bd ready` |
| Claim a task | `bd update <id> --status=in_progress` |
| Graph analysis | `bv --robot-priority` |
| Execution order | `bv --robot-plan` |
| Spawn agents | `ntm spawn proj --cc=2 --cod=1` |
| Bug scan | `ubs <files>` |
| Close task | `bd close <id> --reason="Done"` |
| Recovery | `bd-cleanup` |

---

## 🧠 Knowledge & Vibes Framework

Built on [50+ research papers](https://github.com/Mburdo/knowledge_and_vibes), the workflow includes:

| Component | Count | Purpose |
|-----------|-------|---------|
| **Skills** | 18 | Reusable patterns (`/prime`, `/execute`, `/calibrate`) |
| **Rules** | 3 | Beads, multi-agent coordination, safety |
| **Protocols** | 19 | Planning, decomposition, quality gates |
| **Templates** | 8 | North Star Card, ADRs, Requirements |

### Key Insights from Research

| Finding | Paper | Implementation |
|---------|-------|----------------|
| Plans help most for debugging (+9.1%) | Planning-Driven Programming 2024 | Mandatory North Star Card |
| Extended debate makes decisions worse | Debate or Vote 2025 | "Tests adjudicate, not rhetoric" |
| TDD produces 45.97% higher success | TDD for AI 2024 | TDD-first protocols |
| ~40% of LLM code has vulnerabilities | LLM Security 2024 | Mandatory `ubs --staged` |

---

## 📦 Installation Options

```bash
# Full installation (recommended)
./install.sh

# Minimal (skip cloud CLIs)
./install.sh --minimal

# Skip Ollama (if you have it already)
./install.sh --skip-ollama

# See what would be installed
./install.sh --dry-run

# Force reinstall everything
./install.sh --force
```

### Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Ubuntu 22.04 | Ubuntu 24.04 |
| **RAM** | 4GB | 8GB+ (for Ollama) |
| **Disk** | 10GB | 20GB+ |
| **Network** | Required | Fast connection |

### What Gets Created

```
~/.claude/
├── settings.json          # Hook configuration
├── hooks/                 # Python enforcement hooks
├── agent-state.json       # Current agent state
└── state-{AGENT_NAME}.json # Per-agent state files

~/.beads/
└── beads.db              # Task graph database

~/mcp_agent_mail/
├── storage.sqlite3       # Agent Mail database
└── .env                  # Bearer token

~/.config/ntm/
└── command_palette.md    # 40+ prompt templates
```

---

## 🚀 Post-Installation

### 1. Authenticate AI Agents

```bash
# Claude Code
claude
# Follow OAuth flow in browser

# Codex CLI
codex login --device-auth
# Enter code at github.com/login/device

# Gemini CLI
gemini
# Follow OAuth flow
```

### 2. Initialize Your Project

```bash
cd ~/your-project
bd init                           # Initialize beads
bd create --title="First task" --type=task
bd ready                          # See it's available
```

### 3. Start Multi-Agent Session

```bash
ntm spawn myproject --cc=2 --cod=1  # 2 Claude + 1 Codex
ntm attach myproject                 # Connect to session
# Press F6 for command palette
```

### 4. Verify Setup

```bash
./scripts/verify.sh
```

---

## 🔧 Troubleshooting

### Common Issues

| Error | Solution |
|-------|----------|
| "Agent not registered" | Run `register_agent()` first |
| "File not reserved" | Run `file_reservation_paths()` first |
| "TodoWrite blocked" | Use `bd create` instead |
| `bv` hangs | Always use `--robot-*` flags |
| Stale reservations | Run `bd-cleanup --force` |

### Service Management

```bash
# Check services
sudo systemctl status mcp-agent-mail ollama

# Restart if needed
sudo systemctl restart mcp-agent-mail
sudo systemctl restart ollama

# View logs
sudo journalctl -u mcp-agent-mail -f
```

### Complete Reset

```bash
# Stop services
sudo systemctl stop mcp-agent-mail ollama

# Clear state files (use bd-cleanup instead of manual deletion)
bd-cleanup --reset-state
bd-cleanup --release-all

# Restart
sudo systemctl start mcp-agent-mail ollama
```

See [docs/troubleshooting.md](docs/troubleshooting.md) for more.

---

## 🧪 Testing

The hook system has comprehensive test coverage:

```bash
cd ~/Farmhand
python3 -m pytest tests/ -v

# 88 tests covering:
# - TodoWrite interception
# - Git safety guards
# - Reservation enforcement
# - State tracking
# - Integration workflows
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [docs/quickstart.md](docs/quickstart.md) | 5-minute getting started |
| [docs/architecture.md](docs/architecture.md) | System design overview |
| [docs/hooks.md](docs/hooks.md) | Hook system deep-dive |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues & fixes |
| [docs/upgrade-from-v1.md](docs/upgrade-from-v1.md) | Migration guide |
| [config/CLAUDE.md](config/CLAUDE.md) | Agent workflow instructions (700+ lines) |

---

## 🔗 Tool Repositories

### Core

| Tool | Repository | Author |
|------|------------|--------|
| bd (Beads) | [steveyegge/beads](https://github.com/steveyegge/beads) | Steve Yegge |
| bv (Beads Viewer) | [Dicklesworthstone/beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) | Jeffrey Emanuel |
| qmd | [tobi/qmd](https://github.com/tobi/qmd) | Tobias Lütke |
| MCP Agent Mail | [Dicklesworthstone/mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail) | Jeffrey Emanuel |

### Dicklesworthstone Stack

| Tool | Repository |
|------|------------|
| ubs | [Dicklesworthstone/ultimate_bug_scanner](https://github.com/Dicklesworthstone/ultimate_bug_scanner) |
| ntm | [Dicklesworthstone/ntm](https://github.com/Dicklesworthstone/ntm) |
| cm | [Dicklesworthstone/cass_memory_system](https://github.com/Dicklesworthstone/cass_memory_system) |
| caam | [Dicklesworthstone/coding_agent_account_manager](https://github.com/Dicklesworthstone/coding_agent_account_manager) |
| cass | [Dicklesworthstone/coding_agent_session_search](https://github.com/Dicklesworthstone/coding_agent_session_search) |
| slb | [Dicklesworthstone/simultaneous_launch_button](https://github.com/Dicklesworthstone/simultaneous_launch_button) |

### Workflow

| Tool | Repository | Author |
|------|------------|--------|
| Knowledge & Vibes | [Mburdo/knowledge_and_vibes](https://github.com/Mburdo/knowledge_and_vibes) | Mburdo |

---

## 📜 Version History

### v2.1.0 (Current)
- Knowledge & Vibes workflow layer (18 skills, 7 commands, 19 protocols)
- Research-backed development practices
- NTM command palette (40+ prompts)
- Comprehensive test suite (88 tests)
- Hook enforcement layer with escape hatch

### v2.0.0
- Complete restructure with Dicklesworthstone stack
- Multi-agent coordination with MCP Agent Mail
- Enforcement hooks layer
- Cloud CLIs, AI agents, modern shell

### v1.x (Legacy)
- Basic VM bootstrap
- bd, bv, qmd, Ollama

---

## 🤝 Contributing

1. Fork the repository
2. Create a bead for your change: `bd create --title="Add feature X" --type=feature`
3. Make changes following the workflow
4. Run tests: `python3 -m pytest tests/ -v`
5. Run security scan: `ubs $(git diff --name-only)`
6. Submit PR

---

## 📄 License

MIT License - see LICENSE file.

---

<div align="center">

**Built with 🚜 by the Farmhand team**

*Making multi-agent AI coding actually work*

</div>
