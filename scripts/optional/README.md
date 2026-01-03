# Farmhand Optional Scripts

This directory contains **opt-in utilities** that extend Farmhand functionality.
These are bolt-on additions that don't modify core behavior.

## Available Scripts

### health-alerts.sh

Real-time health monitoring with desktop notifications.

```bash
# One-time check
./health-alerts.sh

# Continuous monitoring
./health-alerts.sh --watch

# Silent cron mode (only outputs on issues)
./health-alerts.sh --cron

# JSON output for automation
./health-alerts.sh --json
```

**Checks performed:**
- MCP Agent Mail service status
- Ollama service status  
- Beads database accessibility
- Hooks installation
- Stale file reservations (>4 hours)
- Expiring reservations (<10 minutes TTL)
- Disk space usage

**Exit codes:**
- `0` - All healthy
- `1` - Warnings present
- `2` - Critical issues

**Cron installation (optional):**
```bash
# Check every 5 minutes, log issues only
echo "*/5 * * * * $HOME/Farmhand/scripts/optional/health-alerts.sh --cron >> /var/log/farmhand-alerts.log 2>&1" | crontab -
```

## Philosophy

All scripts in this directory follow these principles:

1. **Opt-in** - Not enabled by default
2. **Non-destructive** - Read-only operations
3. **Graceful degradation** - Work without all dependencies
4. **No core modifications** - Pure additions

### farmhand-backup.sh

Automated backup for Farmhand databases with retention management.

```bash
# Run backup now
./farmhand-backup.sh

# List available backups
./farmhand-backup.sh --list

# Interactive restore
./farmhand-backup.sh --restore

# Prune backups older than 30 days
./farmhand-backup.sh --prune 30

# Dry run (show what would be backed up)
./farmhand-backup.sh --dry-run
```

**Databases backed up:**
- `~/.beads/beads.db` - Beads issue tracker
- `~/mcp_agent_mail/storage.sqlite3` - Agent Mail messages
- `~/.claude/agent-state.json` - Current agent state

**Default location:** `~/.farmhand-backups/`

**Systemd timer installation (optional):**
```bash
sudo cp ~/Farmhand/systemd/farmhand-backup.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now farmhand-backup.timer
```

Runs nightly at 3 AM with automatic pruning of backups >30 days old.
