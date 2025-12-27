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
