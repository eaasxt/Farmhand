# Upgrading from Farmhand v1.x to v2.0.0

This guide covers upgrading existing Farmhand installations to v2.0.0.

## What's New in v2.0.0

### New Tools

| Tool | Purpose |
|------|---------|
| **ubs** | Ultimate Bug Scanner - pre-commit linting |
| **ntm** | Named Tmux Manager - multi-agent orchestration |
| **cm** | CASS Memory System - procedural memory |
| **caam** | Coding Agent Account Manager - auth backup |
| **slb** | Simultaneous Launch Button - two-person rule |
| **cass** | Coding Agent Session Search (Docker wrapper) |
| **vault** | HashiCorp Vault CLI |
| **wrangler** | Cloudflare Workers CLI |
| **supabase** | Supabase CLI |
| **vercel** | Vercel CLI |
| **Claude Code** | Anthropic's AI coding agent |
| **Codex CLI** | OpenAI's AI coding agent |
| **Gemini CLI** | Google's AI coding agent |

### New Shell Environment

- **zsh** with Oh My Zsh replaces bash
- **Powerlevel10k** theme for enhanced prompts
- Modern CLI tools: lsd, bat, lazygit, fzf, zoxide, atuin
- Plugins: zsh-autosuggestions, zsh-syntax-highlighting

### Updated Configurations

- `CLAUDE.md` expanded from ~200 lines to 700+ lines
- NTM command palette with 40+ pre-built prompts
- Enhanced hooks with UBS integration

## Upgrade Process

### Automatic Upgrade

```bash
cd ~/Farmhand
git pull origin main
./upgrade.sh
```

The upgrade script will:
1. Create a timestamped backup of your configs
2. Update hooks to the latest versions
3. Update CLAUDE.md and settings
4. Install new utilities (bd-cleanup, cass wrapper)
5. Update version tracking

### Manual Upgrade

If you prefer manual control:

```bash
# 1. Backup current configs
mkdir -p ~/.johndeere/backup-manual
cp ~/.claude/settings.json ~/.johndeere/backup-manual/
cp ~/.zshrc ~/.johndeere/backup-manual/ 2>/dev/null || true
cp ~/CLAUDE.md ~/.johndeere/backup-manual/
cp -r ~/.claude/hooks ~/.johndeere/backup-manual/

# 2. Pull latest Farmhand
cd ~/Farmhand
git pull origin main

# 3. Run fresh install with force
./install.sh --force
```

## What Gets Preserved

- **Beads database** (`~/.beads/beads.db`) - Your issues and history
- **Agent state** (`~/.claude/agent-state.json`) - Current registration
- **MCP Agent Mail data** (`~/mcp_agent_mail/storage.sqlite3`) - SQLite database
- **Git configurations** - Your SSH keys and git config

## What Gets Updated

- **Hooks** (`~/.claude/hooks/*.py`) - Latest enforcement logic
- **Settings** (`~/.claude/settings.json`) - Hook configuration
- **CLAUDE.md** (`~/CLAUDE.md`) - Workflow documentation
- **Utilities** (`~/.local/bin/bd-cleanup`, `~/.local/bin/cass`) - Recovery tools

## Post-Upgrade Steps

### 1. Switch to zsh

```bash
exec zsh
```

### 2. Install New Tools (if upgrade skipped them)

```bash
# Dicklesworthstone stack
./scripts/install/03-stack-tools.sh

# Cloud CLIs
./scripts/install/04-cloud-clis.sh

# AI agents
./scripts/install/05-ai-agents.sh

# Shell configuration
./scripts/install/08-shell-config.sh
```

### 3. Authenticate AI Agents

```bash
claude                        # OAuth flow
codex login --device-auth     # Device code flow
gemini                        # Follow prompts
```

### 4. Verify Installation

```bash
./scripts/verify.sh
```

## Troubleshooting

### Hooks not working after upgrade

```bash
# Re-run hooks installation
./scripts/install/09-hooks.sh

# Verify settings.json was updated
cat ~/.claude/settings.json
```

### Missing tools

```bash
# Check what's installed
command -v bd && echo "bd: OK" || echo "bd: MISSING"
command -v bv && echo "bv: OK" || echo "bv: MISSING"
command -v ubs && echo "ubs: OK" || echo "ubs: MISSING"
command -v ntm && echo "ntm: OK" || echo "ntm: MISSING"
```

### cass not working on Ubuntu 22.04

The cass binary requires GLIBC 2.39 (Ubuntu 24.04+). On Ubuntu 22.04, v2.0.0 installs a Docker wrapper:

```bash
# Verify Docker wrapper
cat ~/.local/bin/cass
# Should show Docker invocation

# Test cass
cass --help
```

### Reverting to v1.x

If needed, restore from backup:

```bash
# Find your backup
ls ~/.johndeere/backups/

# Restore specific backup
BACKUP_DIR=~/.johndeere/backups/YYYYMMDD_HHMMSS
cp "$BACKUP_DIR/settings.json" ~/.claude/
cp "$BACKUP_DIR/CLAUDE.md" ~/
cp -r "$BACKUP_DIR/hooks" ~/.claude/

# Downgrade version marker
echo "1.0.0" > ~/.johndeere/version
```

## Breaking Changes

### Settings Location

v1.x used `~/.config/claude-code/settings.json` for MCP configuration.
v2.0.0 uses `~/.claude/settings.json` for all Claude Code configuration.

The upgrade script migrates this automatically.

### Hook Paths

Hook paths are now expanded at install time (no `$HOME` variables in settings.json).

### Shell

v2.0.0 installs zsh as the primary shell. Bash configurations remain but are not actively maintained.

## Questions?

Check the main documentation:
- `~/CLAUDE.md` - Complete workflow guide
- `~/Farmhand/README.md` - Installation reference
- `~/Farmhand/docs/troubleshooting.md` - Common issues
