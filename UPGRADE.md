# Upgrading Farmhand

This document describes how to upgrade an existing Farmhand installation.

## Quick Upgrade

```bash
cd ~/Farmhand
git pull origin main
./upgrade.sh
```

## Upgrade from v2.1 to v2.2

### What's New in v2.2

**Knowledge & Vibes Workflow Layer**
- 18 skills for common development patterns
- 7 slash commands (`/prime`, `/calibrate`, `/execute`, etc.)
- 3 behavior rules (beads, multi-agent, safety)
- 8 documentation templates
- 19 formalized protocols with research backing

**New Slash Commands**
| Command | Purpose |
|---------|---------|
| `/prime` | Start session, register agent, claim work |
| `/calibrate` | 5-phase alignment check between phases |
| `/next-bead` | Close current task, UBS scan, claim next |
| `/release` | End session, cleanup |
| `/execute` | Run parallel work orchestration |
| `/decompose-task` | Break phase into atomic beads |
| `/ground` | Verify external dependencies |

**Bug Fixes**
- Fixed `git_safety_guard.py` false positives on string literals
- Fixed race condition in `session-init.py` state file deletion
- Fixed `03-stack-tools.sh` using `exit` instead of `return`
- Fixed pre-commit hook UBS invocation
- Fixed qmd wrapper pointing to wrong file
- Added missing mcp.json installation

**New Features**
- GLIBC version check for CASS compatibility in `verify.sh`
- Dynamic version reading from VERSION file
- Beads daemon starts during installation (232x speedup)

### Upgrade Steps

1. **Pull latest changes**
   ```bash
   cd ~/Farmhand
   git pull origin main
   git submodule update --init --recursive
   ```

2. **Run upgrade script**
   ```bash
   ./upgrade.sh
   ```

   This will:
   - Create a backup in `~/.farmhand/backups/`
   - Update git submodules
   - Update hooks to `~/.claude/hooks/`
   - Update configurations (CLAUDE.md, settings.json)
   - Install Knowledge & Vibes components

3. **Restart shell**
   ```bash
   exec zsh
   ```

4. **Verify installation**
   ```bash
   ./scripts/verify.sh
   ```

### Manual Steps (if needed)

If the automatic upgrade fails or you want more control:

```bash
# Update hooks manually
cp hooks/*.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.py

# Update CLAUDE.md
cp config/CLAUDE.md ~/CLAUDE.md

# Update settings
cp config/claude-settings.json ~/.claude/settings.json

# Update Knowledge & Vibes
source scripts/install/10-knowledge-vibes.sh
```

### Rollback

If you need to rollback:

```bash
# Find your backup
ls ~/.farmhand/backups/

# Restore from backup
BACKUP=~/.farmhand/backups/YYYYMMDD_HHMMSS
cp "$BACKUP/settings.json" ~/.claude/
cp "$BACKUP/CLAUDE.md" ~/
cp -r "$BACKUP/hooks" ~/.claude/
```

## Version History

### v2.2.1 (Current)
- Fixed multiple bugs found in deep code review
- Added GLIBC compatibility check
- Fixed pre-commit hook UBS invocation
- Improved error handling in hooks

### v2.2.0
- Added Knowledge & Vibes workflow layer
- 18 new skills, 7 commands, 3 rules
- Formalized multi-agent protocols

### v2.1.0
- Initial public release
- Core tools (bd, bv, qmd)
- Enforcement hooks
- MCP Agent Mail integration

## Troubleshooting

### "Agent not registered" errors after upgrade
```bash
bd-cleanup --reset-state
```

### MCP tools not available
Ensure `~/.claude/mcp.json` exists with proper configuration:
```bash
cat ~/.claude/mcp.json
```

If missing, the installer creates it in `scripts/install/07-mcp-agent-mail.sh`.

### Hooks not running
Check permissions:
```bash
ls -la ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.py
```

### Version mismatch
Check all version files match:
```bash
cat ~/Farmhand/VERSION
cat ~/.farmhand/version
```
