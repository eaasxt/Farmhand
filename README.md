<div align="center">

# 🚜 Farmhand

### Transform a Fresh Ubuntu VM into a Multi-Agent AI Coding Powerhouse

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/eaasxt/Farmhand)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04%20%7C%2024.04-orange.svg)](https://ubuntu.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Tests](https://img.shields.io/badge/tests-92%20passing-brightgreen.svg)](#testing)
[![Tools](https://img.shields.io/badge/tools-30%2B-purple.svg)](#-what-gets-installed)

*One command. 30+ tools. Multiple AI agents working in harmony.*

</div>

---

## 📑 Table of Contents

<details>
<summary>Click to expand</summary>

- [TL;DR](#-tldr)
- [Why Farmhand?](#-why-farmhand)
- [Who Is This For?](#-who-is-this-for)
- [Quick Start](#-quick-start)
- [Architecture](#️-architecture)
- [What Gets Installed](#-what-gets-installed)
- [Enforcement Hooks](#-enforcement-hooks)
- [The Workflow](#-the-workflow)
- [Knowledge & Vibes Framework](#-knowledge--vibes-framework)
- [Installation Options](#-installation-options)
- [Post-Installation](#-post-installation)
- [How to Use Farmhand](#-how-to-use-farmhand)
  - [Keyboard Shortcuts](#keyboard-shortcuts--navigation)
  - [Single Agent Workflow](#single-agent-workflow)
  - [Multi-Agent Workflow](#multi-agent-workflow)
  - [Daily Patterns](#daily-workflow-patterns)
  - [Common Scenarios](#handling-common-scenarios)
- [Troubleshooting](#-troubleshooting)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

</details>


## 📋 TL;DR

**Farmhand** takes a bare Ubuntu VM and installs everything you need to run multiple AI coding agents (Claude, Codex, Gemini) that can work together without stepping on each other's toes.

```bash
# Install (15-20 min)
git clone https://github.com/eaasxt/Farmhand.git ~/Farmhand
cd ~/Farmhand && ./install.sh

# After install, you can do this:
ntm spawn myproject --cc=2     # Spawn 2 Claude agents
bd ready                        # See available tasks  
bv --robot-plan                 # Get parallel execution tracks
```

**What makes it special:**
- 🤖 **Multi-agent coordination** — File reservations prevent merge conflicts between agents
- 🔒 **Enforcement hooks** — Agents can't skip the workflow, even if they want to
- 📊 **Graph-based task tracking** — Dependencies, priorities, and parallel execution paths
- 🔬 **Research-backed protocols** — 50+ papers distilled into actionable workflows

> **See it in action:** The [How to Use](#-how-to-use-farmhand) section has a complete walkthrough building "CropWatch" - a smart irrigation controller - with both single and multi-agent workflows.


---

## 🤔 Why Farmhand?

### The Problem

Running multiple AI coding agents on the same codebase creates chaos:

```
Agent A: *edits auth.py*
Agent B: *also edits auth.py*
Result: Merge conflicts, lost work, frustrated developers
```

AI agents don't naturally coordinate. They'll:
- Edit the same files simultaneously
- Duplicate work another agent already did
- Skip security scans because "it looks fine"
- Ignore your project's conventions

### The Solution

Farmhand enforces coordination at the tool level:

```
Agent A: *tries to edit auth.py*
Hook: "File not reserved. Run file_reservation_paths() first."
Agent A: *reserves auth.py*
Agent B: *tries to edit auth.py*  
Hook: "BLOCKED. auth.py reserved by BlueLake until 15:30."
Result: No conflicts, clear ownership, happy developers
```

**Agents can't cheat.** The hooks intercept every file operation and enforce the workflow automatically.



## 🎯 Who Is This For?

<table>
<tr>
<td width="33%">

### 👶 Beginners
"I have a VM and want AI agents writing code for me"

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

### Prerequisites Check

```bash
# Verify you meet requirements
cat /etc/os-release | grep -E "^(ID|VERSION_ID)"  # Ubuntu 22.04+
free -h | grep Mem                                 # 4GB+ RAM recommended
df -h /                                            # 10GB+ disk space
```

### Installation

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
┌──────────────────────────────────────────────────────────────────────────────┐
│                            YOUR VM (Ubuntu 22.04+)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                          AI CODING AGENTS                              │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │  │
│  │  │ Claude Code │   │  Codex CLI  │   │ Gemini CLI  │                   │  │
│  │  │    (cc)     │   │    (cod)    │   │    (gmi)    │                   │  │
│  │  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                   │  │
│  └─────────┼─────────────────┼─────────────────┼──────────────────────────┘  │
│            │                 │                 │                             │
│            ▼                 ▼                 ▼                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                       ENFORCEMENT LAYER (Hooks)                        │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │  │
│  │  │ TodoWrite    │ │ Reservation  │ │ Git Safety   │ │ State        │   │  │
│  │  │ Interceptor  │ │ Checker      │ │ Guard        │ │ Tracker      │   │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│            │                 │                 │                             │
│            ▼                 ▼                 ▼                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        COORDINATION LAYER                              │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │  │
│  │  │ MCP Agent    │ │ Beads (bd)   │ │ Beads Viewer │ │ NTM          │   │  │
│  │  │ Mail         │ │ Task Graph   │ │ (bv)         │ │ Orchestrator │   │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│            │                 │                 │                             │
│            ▼                 ▼                 ▼                             │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         FOUNDATION LAYER                               │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │  │
│  │  │ Ollama       │ │ UBS Scanner  │ │ CASS Memory  │ │ Modern Shell │   │  │
│  │  │ (Embeddings) │ │ (Security)   │ │ (History)    │ │ (zsh/p10k)   │   │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
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

### AI Coding Agents

| Agent | Alias | Mode | Auth |
|-------|-------|------|------|
| Claude Code | `cc` | `--dangerously-skip-permissions` | OAuth |
| Codex CLI | `cod` | `--approval-mode full-auto` | Device code |
| Gemini CLI | `gmi` | `--yolo` | OAuth |

<details>
<summary><strong>📦 Full Tool List (click to expand)</strong></summary>

#### Dicklesworthstone Stack (6 Tools)

| Tool | Purpose | Docs |
|------|---------|------|
| **[ubs](https://github.com/Dicklesworthstone/ultimate_bug_scanner)** | AI-powered bug scanner, pre-commit security | [README](https://github.com/Dicklesworthstone/ultimate_bug_scanner#readme) |
| **[ntm](https://github.com/Dicklesworthstone/ntm)** | Named Tmux Manager for multi-agent orchestration | [README](https://github.com/Dicklesworthstone/ntm#readme) |
| **[cm](https://github.com/Dicklesworthstone/cass_memory_system)** | Procedural memory system for agents | [README](https://github.com/Dicklesworthstone/cass_memory_system#readme) |
| **[caam](https://github.com/Dicklesworthstone/coding_agent_account_manager)** | Backup/restore agent authentication | [README](https://github.com/Dicklesworthstone/coding_agent_account_manager#readme) |
| **[cass](https://github.com/Dicklesworthstone/coding_agent_session_search)** | Search past agent session transcripts | [README](https://github.com/Dicklesworthstone/coding_agent_session_search#readme) |
| **[slb](https://github.com/Dicklesworthstone/simultaneous_launch_button)** | Two-person rule for dangerous commands | [README](https://github.com/Dicklesworthstone/simultaneous_launch_button#readme) |

#### Cloud CLIs

| Tool | Purpose |
|------|---------|
| **vault** | HashiCorp Vault secrets |
| **wrangler** | Cloudflare Workers |
| **supabase** | Supabase backend |
| **vercel** | Vercel deployments |

#### Modern Shell

- **zsh** with Oh My Zsh + Powerlevel10k
- **lsd** (better ls), **bat** (better cat), **lazygit**, **fzf**, **zoxide**, **atuin**
- **bun** + **uv** (fast JS/Python package managers)

</details>

---

## 🔒 Enforcement Hooks

The magic of Farmhand is that agents **can't cheat**. Hooks intercept tool calls and enforce the workflow:

```
┌───────────────────────────────────────────────────────────────┐
│                   HOOK ENFORCEMENT LAYER                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  PreToolUse Hooks (Block BEFORE execution):                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ TodoWrite → BLOCKED → "Use bd create instead"           │  │
│  │ Edit/Write → Check registration → Check reservation     │  │
│  │ Bash(git reset) → BLOCKED → "Destructive command"       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  PostToolUse Hooks (Track AFTER execution):                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ register_agent() → Save agent name to state             │  │
│  │ file_reservation_paths() → Track reservations           │  │
│  │ release_file_reservations() → Clear reservations        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  SessionStart Hooks (Run on session init):                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ Clear stale state files                                 │  │
│  │ Detect orphaned reservations                            │  │
│  │ Inject workflow reminders                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
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
┌─────────────────────────────────────────────────────────────────────────────┐
│                             ENFORCED WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. FIND WORK              2. REGISTER              3. RESERVE              │
│  ┌─────────────┐           ┌─────────────┐          ┌─────────────┐         │
│  │ bd ready    │──────────▶│ register_   │─────────▶│ file_       │         │
│  │ bd update   │           │ agent()     │          │ reservation │         │
│  │ --status=   │           │             │          │ _paths()    │         │
│  │ in_progress │           │ → "BlueLake"│          │ ["src/**"]  │         │
│  └─────────────┘           └─────────────┘          └─────────────┘         │
│                                                                             │
│  4. WORK                   5. COMMIT                6. CLEANUP              │
│  ┌─────────────┐           ┌─────────────┐          ┌─────────────┐         │
│  │ Edit files  │──────────▶│ ubs <files> │─────────▶│ release_    │         │
│  │ (hooks      │           │ git commit  │          │ file_       │         │
│  │ allow now)  │           │ git push    │          │ reservations│         │
│  └─────────────┘           └─────────────┘          │ bd close    │         │
│                                                     └─────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
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

## 🌾 How to Use Farmhand

This section walks you through actually using Farmhand, from your first single-agent session to orchestrating a multi-agent team. We'll use a farming-themed example project throughout: **CropWatch**, a smart irrigation controller.

### Keyboard Shortcuts & Navigation

<details>
<summary><strong>🎹 Click to expand keyboard shortcuts</strong></summary>

#### Terminal & Shell

| Shortcut | Action | Context |
|----------|--------|---------|
| `Ctrl+R` | Fuzzy search command history (atuin) | Any terminal |
| `Ctrl+T` | Fuzzy find files (fzf) | Any terminal |
| `Alt+C` | Fuzzy cd into directory (fzf) | Any terminal |
| `z <partial>` | Smart jump to directory (zoxide) | e.g., `z crop` → `~/projects/cropwatch` |
| `Tab` | Autocomplete with suggestions | zsh-autosuggestions |
| `Ctrl+L` | Clear screen | Any terminal |
| `Ctrl+C` | Cancel current command | Any terminal |
| `Ctrl+D` | Exit shell / EOF | Any terminal |

#### Tmux (Inside NTM Sessions)

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` then `d` | Detach from session |
| `Ctrl+B` then `[` | Enter scroll/copy mode |
| `Ctrl+B` then `]` | Paste buffer |
| `Ctrl+B` then `c` | Create new window |
| `Ctrl+B` then `n` / `p` | Next / previous window |
| `Ctrl+B` then `0-9` | Jump to window by number |
| `Ctrl+B` then `%` | Split pane vertically |
| `Ctrl+B` then `"` | Split pane horizontally |
| `Ctrl+B` then arrow keys | Navigate between panes |
| `F6` | Open NTM command palette |

#### Claude Code (Inside Agent Session)

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current generation |
| `Ctrl+L` | Clear conversation |
| `/help` | Show available commands |
| `/compact` | Toggle compact mode |
| `Esc` | Dismiss/cancel |
| `Up/Down` | Navigate history |

#### Lazygit (Git TUI)

| Shortcut | Action |
|----------|--------|
| `lg` | Launch lazygit |
| `Space` | Stage/unstage file |
| `c` | Commit |
| `P` | Push |
| `p` | Pull |
| `?` | Show all shortcuts |
| `q` | Quit |

</details>

---

### Example Project: CropWatch 🌱

Throughout this guide, we will build **CropWatch** - a smart irrigation controller that:
- Monitors soil moisture sensors
- Controls irrigation valves
- Provides a web dashboard
- Sends alerts when intervention needed

---

### Single Agent Workflow

Perfect for getting started or smaller tasks.

#### Step 1: Create Your Project

```bash
# Create and enter project directory
mkdir -p ~/projects/cropwatch && cd ~/projects/cropwatch

# Initialize git and beads
git init
bd init

# Create initial structure
mkdir -p src tests docs
```

#### Step 2: Plan Your Work with Beads

```bash
# Create the main epic
bd create --title="CropWatch MVP" --type=epic --priority=1

# Break it into tasks
bd create --title="Sensor data models" --type=task --priority=1
bd create --title="Irrigation controller API" --type=task --priority=1
bd create --title="Web dashboard" --type=task --priority=2
bd create --title="Alert system" --type=task --priority=2

# Set dependencies (dashboard depends on API)
bd dep <api-task-id> <dashboard-task-id>

# See what is ready to work on
bd ready
```

Output:
```
cropwatch-a1b [P1] [task] open - Sensor data models
cropwatch-c2d [P1] [task] open - Irrigation controller API
```

#### Step 3: Start Claude in Dangerous Mode

```bash
# Launch Claude with auto-approve (alias: cc)
cc

# Or the full command:
claude --dangerously-skip-permissions
```

#### Step 4: Register and Reserve (Inside Claude)

Once Claude starts, you will see the enforcement hooks in action. Tell Claude:

```
I am working on CropWatch. Please:
1. Register as an agent
2. Reserve the src/ directory
3. Claim the "Sensor data models" task
```

Claude will run:
```python
# Register with MCP Agent Mail
register_agent(
    project_key="/home/ubuntu/projects/cropwatch",
    program="claude-code",
    model="opus-4.5"
)
# Returns: {"name": "BlueLake", ...}

# Reserve files
file_reservation_paths(
    project_key="/home/ubuntu/projects/cropwatch",
    agent_name="BlueLake",
    paths=["src/**", "tests/**"],
    ttl_seconds=3600,
    exclusive=True,
    reason="cropwatch-a1b"
)
```

```bash
# Claude updates beads
bd update cropwatch-a1b --status=in_progress --assignee=BlueLake
```

#### Step 5: Do the Work

Now Claude can edit files freely. Ask it to:

```
Create the sensor data models in src/models/sensor.py with:
- SoilMoistureSensor class
- MoistureReading dataclass with timestamp, value, sensor_id
- Validation for moisture range 0-100%
```

Claude edits files - hooks allow it because files are reserved.

#### Step 6: Commit and Close

When done with the task:

```
Run ubs on the changed files, commit the work, and close the bead.
```

Claude will:
```bash
# Security scan
ubs src/models/sensor.py tests/test_sensor.py

# Commit
git add -A
git commit -m "Add sensor data models

- SoilMoistureSensor class with calibration
- MoistureReading dataclass with validation
- Unit tests with 95% coverage

Closes cropwatch-a1b"
```

```python
# Release reservations
release_file_reservations(
    project_key="/home/ubuntu/projects/cropwatch",
    agent_name="BlueLake"
)
```

```bash
# Close the bead
bd close cropwatch-a1b --reason="Sensor models complete with tests"
```

---

### Multi-Agent Workflow

The real power of Farmhand: multiple AI agents working in parallel.

#### Step 1: Plan Parallel Tracks

First, structure work for parallel execution:

```bash
# Check what can run in parallel
bv --robot-plan

# Output shows tracks:
# Track 1: cropwatch-a1b (Sensor models) -> cropwatch-e5f (Dashboard)
# Track 2: cropwatch-c2d (API) -> cropwatch-g7h (Alerts)
```

#### Step 2: Spawn Multiple Agents

```bash
# Spawn 2 Claude agents for the project
ntm spawn cropwatch --cc=2

# Or mixed agents:
ntm spawn cropwatch --cc=1 --cod=1 --gmi=1
```

This creates a tmux session with:
- Window 1: Claude agent `cropwatch__cc_1`
- Window 2: Claude agent `cropwatch__cc_2`

#### Step 3: Attach and Navigate

```bash
# Attach to the session
ntm attach cropwatch

# You will see the first agent. To switch:
# Ctrl+B then n -> Next window (agent 2)
# Ctrl+B then p -> Previous window (agent 1)
# Ctrl+B then 1 -> Jump to window 1
# Ctrl+B then 2 -> Jump to window 2
```

#### Step 4: Assign Work to Each Agent

**In Window 1 (Agent 1):**
```
You are working on CropWatch. Your focus is the sensor layer.
1. Register as an agent
2. Reserve src/models/** and src/sensors/**
3. Claim "Sensor data models" (cropwatch-a1b)
4. Build the sensor data models and drivers
```

**In Window 2 (Agent 2):**
```
You are working on CropWatch. Your focus is the API layer.
1. Register as an agent  
2. Reserve src/api/** and src/controllers/**
3. Claim "Irrigation controller API" (cropwatch-c2d)
4. Build the FastAPI endpoints for irrigation control
```

Each agent registers separately and gets a unique name (e.g., "BlueLake" and "GreenMountain").

#### Step 5: Agents Coordinate via Messages

If Agent 2 needs something from Agent 1:

```python
# Agent 2 sends a message
send_message(
    project_key="/home/ubuntu/projects/cropwatch",
    sender_name="GreenMountain",
    to=["BlueLake"],
    subject="Need sensor interface",
    body_md="""
I am building the API and need the sensor interface.
Can you prioritize the SensorReader class?
I will wait before implementing the /readings endpoint.
    """,
    importance="high",
    thread_id="cropwatch-c2d"
)
```

Agent 1 sees it in their inbox:
```python
# Check inbox
fetch_inbox(
    project_key="/home/ubuntu/projects/cropwatch",
    agent_name="BlueLake"
)
```

#### Step 6: Use the Command Palette

Press `F6` in any tmux window to open the NTM command palette:

```
+-------------------------------------------+
|         NTM Command Palette               |
+-------------------------------------------+
| [1] Fresh code review                     |
| [2] Check other agents work               |
| [3] Apply UBS to recent changes           |
| [4] Fix bug in current context            |
| [5] Create tests for recent code          |
| [6] Check Agent Mail inbox                |
| [7] Announce completion                   |
| [8] Request help from other agent         |
| ...                                       |
+-------------------------------------------+
```

Select a command and it is pasted into the agent prompt.

#### Step 7: Monitor Progress

In a separate terminal:

```bash
# Watch beads status
watch -n 5 bd stats

# See who is working on what
bd list --status=in_progress

# Graph analysis
bv --robot-summary
```

#### Step 8: Coordinate Completion

When all agents finish their tasks:

```bash
# Check all tracks complete
bv --robot-alerts

# Should show no warnings

# Final stats
bd stats
```

---

### Daily Workflow Patterns

#### Morning: Start Your Session

```bash
# 1. Check project health
cd ~/projects/cropwatch
bd stats
bd ready

# 2. See priority recommendations
bv --robot-priority

# 3. Search past sessions for context
cass search "irrigation valve" --days 7

# 4. Start agents
ntm spawn cropwatch --cc=2
ntm attach cropwatch
```

#### During Work: Common Commands

```bash
# What files are reserved?
bd-cleanup --list

# Quick git status
lg  # Opens lazygit

# Search docs
qmd query "how does the valve controller work"

# Security check before commit
ubs $(git diff --name-only)
```

#### End of Day: Clean Shutdown

```bash
# 1. In each agent window, say:
"Wrap up current work, commit changes, release reservations, and close any completed beads."

# 2. Detach from tmux
# Ctrl+B then d

# 3. Verify clean state
bd list --status=in_progress  # Should be empty or known
bd-cleanup --list             # Check for orphans

# 4. Ensure changes are pushed
cd ~/projects/cropwatch
git status
```

---

### Handling Common Scenarios

#### Scenario: Agent Gets Stuck

```bash
# Check what is blocking
bv --robot-alerts

# If agent crashed, clean up its reservations
bd-cleanup --force

# Restart the agent
ntm spawn cropwatch --cc=1
```

#### Scenario: Need to Edit a Reserved File

```
# Option 1: Ask the reserving agent to release
# (Send them a message via Agent Mail)

# Option 2: Wait for TTL expiry (default 1 hour)

# Option 3: Force cleanup (if agent crashed)
bd-cleanup --release-all

# Option 4: Bypass enforcement (use sparingly)
export FARMHAND_SKIP_ENFORCEMENT=1
claude
```

#### Scenario: Merge Conflicts

```bash
# The reservation system should prevent these, but if they happen:

# 1. Open lazygit
lg

# 2. Navigate to conflicted files
# 3. Press e to edit and resolve
# 4. Stage with Space, commit with c

# Better: Check reservations before working
bd-cleanup --list
```

#### Scenario: Starting Fresh on a New Feature

```bash
# 1. Create the epic and tasks
bd create --title="Greenhouse Integration" --type=epic
bd create --title="Greenhouse sensor protocol" --type=task
bd create --title="Greenhouse UI panel" --type=task
bd create --title="Greenhouse alerts" --type=task

# 2. Set dependencies
bd dep <sensor-id> <ui-id>
bd dep <sensor-id> <alerts-id>

# 3. Check the plan
bv --robot-plan

# 4. Spawn agents and assign tracks
ntm spawn cropwatch --cc=3
```

---

### Tips for Effective Multi-Agent Work

#### Dos

1. **Start with `bd ready`** - Always know what is available before claiming
2. **Use descriptive bead titles** - "Fix auth bug" -> "Fix JWT expiry not refreshing in mobile app"  
3. **Reserve files early** - Claim territory before coding
4. **Commit often** - Small, focused commits are easier to review
5. **Run `ubs` before every commit** - Catch security issues early
6. **Use thread_id in messages** - Keep conversations organized by bead
7. **Close beads promptly** - Do not hoard completed work
8. **Detach, do not kill** - Use `Ctrl+B d` to preserve tmux sessions

#### Do Nots

1. **Do not skip registration** - Hooks will block your edits
2. **Do not run bare `bv`** - It opens TUI and hangs; use `--robot-*` flags
3. **Do not reserve everything** - Only reserve what you are actively editing
4. **Do not ignore inbox messages** - Other agents may be blocked on you
5. **Do not force-kill agents** - Orphans reservations; use clean shutdown
6. **Do not skip `ubs`** - About 40% of LLM-generated code has vulnerabilities
7. **Do not debate in messages** - Write tests to adjudicate disagreements

---

### Quick Reference Card

```
┌─────────────────────┬─────────────────────┬─────────────────────────────┐
│      FIND WORK      │       SETUP         │           WORK              │
├─────────────────────┼─────────────────────┼─────────────────────────────┤
│ bd ready            │ register_agent()    │ Edit files freely           │
│ bv --robot-priority │ file_reservation_   │ (hooks allow after setup)   │
│ bv --robot-plan     │ paths()             │                             │
├─────────────────────┼─────────────────────┼─────────────────────────────┤
│      COMMIT         │      CLEANUP        │        MULTI-AGENT          │
├─────────────────────┼─────────────────────┼─────────────────────────────┤
│ ubs <files>         │ release_file_       │ ntm spawn <p> --cc=2        │
│ git add -A          │ reservations()      │ ntm attach <project>        │
│ git commit          │ bd close <id>       │ F6 → command palette        │
│                     │ bd-cleanup          │ Ctrl+B n/p → switch window  │
├─────────────────────┼─────────────────────┼─────────────────────────────┤
│     SHORTCUTS       │    NAVIGATION       │         RECOVERY            │
├─────────────────────┼─────────────────────┼─────────────────────────────┤
│ cc = claude danger  │ z <dir> = jump      │ bd-cleanup --force          │
│ lg = lazygit        │ Ctrl+R = history    │ bd-cleanup --release-all    │
│ F6 = ntm palette    │ Ctrl+T = find file  │ bd-cleanup --reset-state    │
└─────────────────────┴─────────────────────┴─────────────────────────────┘
```


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

# 92 tests covering:
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

<details>
<summary><strong>View all tool repositories and authors</strong></summary>

### Core

| Tool | Version | Repository | Author |
|------|---------|------------|--------|
| bd (Beads) | v0.36.0 | [steveyegge/beads](https://github.com/steveyegge/beads) | Steve Yegge |
| bv (Beads Viewer) | v0.11.2 | [Dicklesworthstone/beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) | Jeffrey Emanuel |
| qmd | latest | [tobi/qmd](https://github.com/tobi/qmd) | Tobias Lütke |
| MCP Agent Mail | latest | [Dicklesworthstone/mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail) | Jeffrey Emanuel |

### Dicklesworthstone Stack

| Tool | Version | Repository |
|------|---------|------------|
| ubs | v5.0.0 | [Dicklesworthstone/ultimate_bug_scanner](https://github.com/Dicklesworthstone/ultimate_bug_scanner) |
| ast-grep | required | [ast-grep/ast-grep](https://github.com/ast-grep/ast-grep) (UBS dependency) |
| ntm | v1.2.0 | [Dicklesworthstone/ntm](https://github.com/Dicklesworthstone/ntm) |
| cm | v0.2.0 | [Dicklesworthstone/cass_memory_system](https://github.com/Dicklesworthstone/cass_memory_system) |
| caam | latest | [Dicklesworthstone/coding_agent_account_manager](https://github.com/Dicklesworthstone/coding_agent_account_manager) |
| cass | v0.1.36 | [Dicklesworthstone/coding_agent_session_search](https://github.com/Dicklesworthstone/coding_agent_session_search) |
| slb | latest | [Dicklesworthstone/simultaneous_launch_button](https://github.com/Dicklesworthstone/simultaneous_launch_button) |

### Workflow

| Tool | Repository | Author |
|------|------------|--------|
| Knowledge & Vibes | [Mburdo/knowledge_and_vibes](https://github.com/Mburdo/knowledge_and_vibes) | Mburdo |

</details>

---

## 📜 Version History

| Version | Date | Highlights |
|---------|------|------------|
| **v2.2.0** | Dec 2025 | bd v0.36 molecular bonding, UBS v5.0 + ast-grep, CASS v0.1.36, NTM v1.2 |
| **v2.1.0** | Dec 2025 | Knowledge & Vibes workflow, 92 tests, hook enforcement, escape hatch |
| **v2.0.0** | Nov 2025 | Dicklesworthstone stack, MCP Agent Mail, multi-agent coordination |
| **v1.x** | Oct 2025 | Basic VM bootstrap with bd, bv, qmd, Ollama |

<details>
<summary>Detailed changelog</summary>

### v2.2.0 (December 2025)
- **Beads v0.36.0**: Molecular bonding system (`bd mol`, `bd cook`, `bd ship`)
- **UBS v5.0.0**: ast-grep now REQUIRED for JavaScript/TypeScript scanning
- **ast-grep**: Added as mandatory dependency
- **CASS v0.1.36**: New connectors (Pi-Agent, Cursor, ChatGPT Desktop), export/expand/timeline commands
- **NTM v1.2.0**: Dashboard 360-View, file change tracking, CASS integration
- **bv v0.11.2**: Hybrid search with graph-aware ranking
- **ACFS backports**: Claude path handling, Supabase reliability, OhMyZsh pinning
- Expanded `verify.sh` health checks

### v2.1.0 (December 2025)
- Knowledge & Vibes workflow layer (18 skills, 7 commands, 19 protocols)
- Research-backed development practices from 50+ papers
- NTM command palette (40+ prompts)
- Comprehensive test suite (92 tests)
- Hook enforcement layer with `FARMHAND_SKIP_ENFORCEMENT` escape hatch
- Automatic stale reservation cleanup
- Heredoc-aware git safety guard

### v2.0.0 (November 2025)
- Complete restructure with Dicklesworthstone stack
- Multi-agent coordination with MCP Agent Mail
- Enforcement hooks layer (PreToolUse, PostToolUse, SessionStart)
- Cloud CLIs (Vault, Wrangler, Supabase, Vercel)
- AI agent aliases (cc, cod, gmi)
- Modern shell environment

### v1.x (October 2025)
- Basic VM bootstrap
- bd, bv, qmd, Ollama installation
- Initial hook concepts

</details>

---

## 🤝 Contributing

We welcome contributions! Farmhand uses its own workflow for development.

### Quick Contribution

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/Farmhand.git
cd Farmhand

# 2. Create a bead for your change
bd init  # If not already initialized
bd create --title="Add feature X" --type=feature

# 3. Make changes following the workflow
# (register, reserve files, edit, test, commit)

# 4. Run quality gates
python3 -m pytest tests/ -v          # 92 tests must pass
ubs $(git diff --name-only)           # Security scan

# 5. Submit PR
```

### Contribution Ideas

| Area | Examples |
|------|----------|
| **Hooks** | New enforcement rules, better error messages |
| **Tests** | Edge cases, integration tests |
| **Docs** | Tutorials, troubleshooting guides |
| **Tools** | New tool integrations, aliases |

### Code Style

- Python: Follow existing patterns in `hooks/`
- Bash: POSIX-compatible, use shellcheck
- Docs: Clear, actionable, with examples

See [docs/architecture.md](docs/architecture.md) for system design details.

---

## 📄 License

MIT License - see LICENSE file.

---

<div align="center">

**Built with 🚜 by the Farmhand team**

*Making multi-agent AI coding actually work*

---

<sub>Last updated: December 2025 · [Report issues](https://github.com/eaasxt/Farmhand/issues) · [Discussions](https://github.com/eaasxt/Farmhand/discussions)</sub>

</div>
