# JohnDeere v2.1.0

Agentic VM Setup - Transform a fresh Ubuntu VPS into a fully-configured multi-agent AI coding environment.

## Quick Install

```bash
# Fresh install
git clone https://github.com/eaasxt/JohnDeere.git ~/JohnDeere
cd ~/JohnDeere
./install.sh

# Upgrade existing installation
./upgrade.sh
```

## What Gets Installed

### Core Stack

| Tool | Purpose |
|------|---------|
| **bd** (Beads) | Issue/task tracking CLI |
| **bv** (Beads Viewer) | Graph visualization & priority analysis |
| **qmd** | Markdown semantic search with Ollama |

### Dicklesworthstone Stack (8 Tools)

| Tool | Purpose | Install Method |
|------|---------|----------------|
| **ubs** | Ultimate Bug Scanner - pre-commit linting | Shell script |
| **ntm** | Named Tmux Manager - multi-agent orchestration | Go from source |
| **cm** | CASS Memory System - procedural memory | Go from source |
| **caam** | Coding Agent Account Manager - auth backup | Go from source |
| **slb** | Simultaneous Launch Button - two-person rule | Go from source |
| **cass** | Coding Agent Session Search | Docker wrapper* |

*cass requires GLIBC 2.39+ (Ubuntu 24.04). On Ubuntu 22.04, a Docker wrapper is installed.

### Cloud CLIs

| Tool | Purpose |
|------|---------|
| **vault** | HashiCorp Vault |
| **wrangler** | Cloudflare Workers |
| **supabase** | Supabase CLI |
| **vercel** | Vercel deployments |

### AI Coding Agents

| Tool | Mode |
|------|------|
| **Claude Code** | `cc` = dangerous mode |
| **Codex CLI** | `cod` = full-auto mode |
| **Gemini CLI** | `gmi` = yolo mode |

### Shell Environment

- **zsh** with Oh My Zsh
- **Powerlevel10k** theme
- **Modern CLI tools**: lsd, bat, lazygit, fzf, zoxide, atuin
- **Plugins**: zsh-autosuggestions, zsh-syntax-highlighting

### Multi-Agent Coordination

- **MCP Agent Mail** - Agent messaging and file reservations
- **Enforcement Hooks** - Block TodoWrite, enforce reservations
- **Ollama** - Local LLM for embeddings/reranking

### Knowledge & Vibes Workflow

Structured workflow framework with research-backed protocols:

| Component | Count | Description |
|-----------|-------|-------------|
| **Skills** | 18 | Reusable development patterns |
| **Slash Commands** | 7 | `/prime`, `/calibrate`, `/execute`, `/next-bead`, `/decompose-task`, `/ground`, `/release` |
| **Rules** | 3 | beads, multi-agent, safety |
| **Templates** | 8 | North Star Card, Requirements, ADRs, etc. |
| **Protocols** | 19 | Planning, decomposition, execution, quality gates |

## Installation Options

```bash
./install.sh              # Full install
./install.sh --minimal    # Skip cloud CLIs
./install.sh --skip-ollama # Skip Ollama and models
./install.sh --dry-run    # Show what would be installed
./install.sh --force      # Reinstall everything
```

## Upgrading from v1.x

```bash
./upgrade.sh
```

This will:
1. Backup your current configs
2. Update hooks, utilities, and configurations
3. Preserve your beads database and agent state

See [docs/upgrade-from-v1.md](docs/upgrade-from-v1.md) for details.

## Directory Structure

```
JohnDeere/
├── VERSION                     # Current version (2.1.0)
├── install.sh                  # Master idempotent installer
├── upgrade.sh                  # Upgrade existing installs
│
├── config/
│   ├── CLAUDE.md               # Workflow instructions (700+ lines)
│   ├── claude-settings.json    # Hook configuration
│   ├── zshrc.template          # Shell configuration
│   ├── p10k.zsh                # Powerlevel10k theme
│   ├── ntm/command_palette.md  # 40+ NTM prompts
│   └── systemd/                # Service files
│
├── hooks/
│   ├── README.md                 # Hook documentation
│   ├── todowrite-interceptor.py  # Blocks TodoWrite
│   ├── reservation-checker.py    # Enforces file reservations
│   ├── mcp-state-tracker.py      # Tracks agent state
│   ├── session-init.py           # Session startup
│   ├── git_safety_guard.py       # Blocks destructive git commands
│   └── on-file-write.sh          # UBS integration
│
├── bin/
│   ├── bd-cleanup              # Recovery utility
│   └── cass                    # Docker wrapper for cass
│
├── scripts/
│   ├── install/
│   │   ├── 01-system-deps.sh   # apt, homebrew, bun, uv
│   │   ├── 02-core-tools.sh    # bd, bv, qmd
│   │   ├── 03-stack-tools.sh   # ubs, ntm, cm, caam, slb, cass
│   │   ├── 04-cloud-clis.sh    # vault, wrangler, supabase, vercel
│   │   ├── 05-ai-agents.sh     # codex, gemini, node
│   │   ├── 06-ollama.sh        # Ollama + models
│   │   ├── 07-mcp-agent-mail.sh
│   │   ├── 08-shell-config.sh  # zsh, oh-my-zsh, p10k
│   │   ├── 09-hooks.sh         # Enforcement hooks
│   │   └── 10-knowledge-vibes.sh # Workflow framework
│   └── verify.sh               # Post-install verification
│
├── vendor/
│   └── knowledge_and_vibes/    # Workflow framework (git submodule)
│
└── docs/
    ├── quickstart.md           # 5-minute getting started
    ├── architecture.md         # System overview
    ├── hooks.md                # Hook system documentation
    ├── troubleshooting.md      # Common issues
    └── upgrade-from-v1.md      # Migration guide
```

## Post-Install

See [docs/quickstart.md](docs/quickstart.md) for a complete getting-started guide.

```bash
# Switch to new shell
exec zsh

# Authenticate AI agents
claude                              # Follow OAuth flow
codex login --device-auth           # Device code flow
gemini                              # Follow prompts

# Verify installation
./scripts/verify.sh
```

## Quick Commands

```bash
# Issue tracking
bd ready                    # What's available to work on
bd stats                    # Project health
bd create --title="..." --type=task

# Graph analysis (ALWAYS use --robot-* flags)
bv --robot-priority         # What to work on next
bv --robot-plan             # Execution order

# Bug scanning
ubs <files>                 # Scan before commit

# Multi-agent
ntm spawn proj --cc=2 --cod=1   # Spawn agent sessions
ntm palette                      # Command palette (F6)

# AI agents (dangerous modes)
cc                          # Claude --dangerously-skip-permissions
cod                         # Codex --approval-mode full-auto
gmi                         # Gemini --yolo
```

## Enforcement Layer

Hooks enforce the multi-agent workflow:

| Hook | What It Does |
|------|--------------|
| `todowrite-interceptor.py` | Blocks TodoWrite, suggests bd |
| `reservation-checker.py` | Blocks Edit/Write without file reservation |
| `mcp-state-tracker.py` | Tracks agent state |
| `session-init.py` | Cleans stale state on session start |
| `git_safety_guard.py` | Blocks destructive git commands |
| `on-file-write.sh` | Runs UBS on written files |

See [docs/hooks.md](docs/hooks.md) for detailed hook documentation.

## Requirements

- Ubuntu 22.04+ (tested on 22.04 and 24.04)
- At least 8GB RAM (for Ollama models)
- 10GB+ free disk space
- Internet connection

## Version History

### v2.1.0 (Current)
- Added Knowledge & Vibes workflow layer (git submodule)
- 18 skills for common development patterns
- 7 slash commands (/prime, /calibrate, /execute, etc.)
- 3 behavior rules (beads, multi-agent, safety)
- 8 documentation templates
- 19 formalized protocols with research backing

### v2.0.0
- Complete restructure from vestigial v1
- Added Dicklesworthstone stack (8 tools)
- Added cloud CLIs (vault, wrangler, supabase, vercel)
- Added AI agents (Claude Code, Codex, Gemini)
- Full zsh configuration with Powerlevel10k
- NTM command palette with 40+ prompts
- Docker wrapper for cass (Ubuntu 22.04 compatibility)
- Idempotent installer with upgrade support

### v1.x (Legacy)
- Basic VM bootstrap
- bd, bv, qmd, Ollama, MCP Agent Mail
- Enforcement hooks

## Tool Sources

| Tool | Repository |
|------|------------|
| bd | [steveyegge/beads](https://github.com/steveyegge/beads) |
| bv | [Dicklesworthstone/beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) |
| qmd | [tobi/qmd](https://github.com/tobi/qmd) |
| ubs | [Dicklesworthstone/ultimate_bug_scanner](https://github.com/Dicklesworthstone/ultimate_bug_scanner) |
| ntm | [Dicklesworthstone/ntm](https://github.com/Dicklesworthstone/ntm) |
| cm | [Dicklesworthstone/cass_memory_system](https://github.com/Dicklesworthstone/cass_memory_system) |
| caam | [Dicklesworthstone/coding_agent_account_manager](https://github.com/Dicklesworthstone/coding_agent_account_manager) |
| slb | [Dicklesworthstone/simultaneous_launch_button](https://github.com/Dicklesworthstone/simultaneous_launch_button) |
| cass | [Dicklesworthstone/coding_agent_session_search](https://github.com/Dicklesworthstone/coding_agent_session_search) |
| MCP Agent Mail | [Dicklesworthstone/mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail) |
| Knowledge & Vibes | [Mburdo/knowledge_and_vibes](https://github.com/Mburdo/knowledge_and_vibes) |

## License

Private repository - internal use only.
