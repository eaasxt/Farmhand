# JohnDeere VM Bootstrap

Quick setup for a fully-configured Claude Code development VM with multi-agent coordination.

## What's Included

| Tool | Description |
|------|-------------|
| `bd` (beads) | Issue/task tracking CLI |
| `bv` (beads-viewer) | Graph visualization for issues |
| `qmd` | Markdown semantic search |
| MCP Agent Mail | Multi-agent coordination server |
| Ollama | Local LLM for embeddings/reranking |
| Claude Code | AI-powered CLI (via Homebrew) |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/eaasxt/JohnDeere.git ~/JohnDeere
cd ~/JohnDeere

# Run the full installer (takes ~10-15 min)
./scripts/install.sh

# Restart shell to pick up PATH changes
exec bash -l

# Verify everything works
./scripts/verify.sh
```

## Manual Step-by-Step

If you prefer more control:

```bash
# 1. System dependencies
./scripts/01-system-deps.sh

# 2. Core tools (bd, bv, qmd)
./scripts/02-tools.sh

# 3. Ollama + models
./scripts/03-ollama.sh

# 4. MCP Agent Mail
./scripts/04-mcp-agent-mail.sh

# 5. Claude Code configuration
./scripts/05-claude-config.sh

# 6. Systemd services
./scripts/06-services.sh
```

## After Installation

1. **Start Claude Code**: `claude`
2. **Check services**: `sudo systemctl status mcp-agent-mail ollama`
3. **Review the workflow**: Read `~/CLAUDE.md`

## Directory Structure

```
JohnDeere/
├── scripts/              # Installation scripts
│   ├── install.sh        # Master installer
│   ├── 01-system-deps.sh # apt packages, homebrew, bun
│   ├── 02-tools.sh       # bd, bv, qmd
│   ├── 03-ollama.sh      # Ollama + models
│   ├── 04-mcp-agent-mail.sh
│   ├── 05-claude-config.sh
│   ├── 06-services.sh
│   └── verify.sh         # Post-install verification
├── config/
│   ├── CLAUDE.md         # Main workflow instructions
│   ├── bashrc-additions  # Shell environment
│   ├── systemd/          # Service files
│   └── beads/            # Beads configuration
└── docs/
    └── troubleshooting.md
```

## Requirements

- Ubuntu 22.04+ (tested on Ubuntu 22.04 LTS)
- At least 4GB RAM (8GB recommended for Ollama)
- Internet connection

## License

Private repository - internal use only.
