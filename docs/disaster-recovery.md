# Disaster Recovery Guide

This guide covers recovery procedures for common failure scenarios in the Farmhand multi-agent environment.

---

## Quick Triage

```bash
# Check overall system health
bd-cleanup --list

# Check services
sudo systemctl status mcp-agent-mail ollama

# Check database integrity
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "PRAGMA integrity_check;"
sqlite3 ~/.beads/beads.db "PRAGMA integrity_check;"
```

---

## 1. SQLite Database Corruption

### Symptoms
- `sqlite3.DatabaseError: database disk image is malformed`
- `SQLITE_CORRUPT` errors in logs
- Queries returning unexpected results or failing

### Recovery: Agent Mail Database

```bash
# 1. Stop the service
sudo systemctl stop mcp-agent-mail

# 2. Check integrity
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "PRAGMA integrity_check;"

# 3. If corrupted, attempt recovery
cd ~/mcp_agent_mail

# Backup corrupted database
cp storage.sqlite3 storage.sqlite3.corrupted.$(date +%Y%m%d)

# Try to recover data
sqlite3 storage.sqlite3 ".recover" | sqlite3 storage.recovered.sqlite3

# If recovery worked, replace original
mv storage.recovered.sqlite3 storage.sqlite3

# 4. If recovery fails, reinitialize (loses data)
rm storage.sqlite3
sudo systemctl start mcp-agent-mail
# Database will be recreated on first use
```

### Recovery: Beads Database

```bash
# 1. Check integrity
sqlite3 ~/.beads/beads.db "PRAGMA integrity_check;"

# 2. If corrupted, attempt recovery
cd ~/.beads

# Backup corrupted database
cp beads.db beads.db.corrupted.$(date +%Y%m%d)

# Try to recover
sqlite3 beads.db ".recover" | sqlite3 beads.recovered.db

# If successful
mv beads.recovered.db beads.db

# 3. If recovery fails, reinitialize from issues.jsonl
rm beads.db
bd sync  # Rebuilds from issues.jsonl if present
```

### Prevention

The hooks use WAL mode and busy timeouts to reduce corruption risk:
```python
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA busy_timeout=30000')
```

If experiencing frequent corruption:
1. Check disk space: `df -h`
2. Check for disk errors: `dmesg | grep -i error`
3. Ensure proper shutdown (don't kill -9 processes with open DB connections)

---

## 2. Orphaned Reservations

### Symptoms
- "File reserved by another agent" errors for files no one is using
- `bd-cleanup --list` shows stale reservations
- Agents cannot reserve files

### Quick Fix

```bash
# Interactive cleanup (recommended)
bd-cleanup

# Auto-cleanup stale (>4 hours) reservations
bd-cleanup --force

# Nuclear option: release ALL reservations
bd-cleanup --release-all
```

### Manual Cleanup

```bash
# View active reservations
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "
SELECT
    fr.id,
    a.name as agent,
    fr.path_pattern,
    fr.reason,
    fr.created_ts,
    fr.expires_ts
FROM file_reservations fr
JOIN agents a ON fr.agent_id = a.id
WHERE fr.released_ts IS NULL
ORDER BY fr.created_ts DESC;
"

# Release specific reservation by ID
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "
UPDATE file_reservations
SET released_ts = datetime('now')
WHERE id = <reservation_id>;
"

# Release all reservations for a specific agent
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "
UPDATE file_reservations
SET released_ts = datetime('now')
WHERE agent_id = (SELECT id FROM agents WHERE name = 'AgentName')
AND released_ts IS NULL;
"
```

### Prevention

- Always call `release_file_reservations()` before ending sessions
- Use reasonable TTLs (default 1 hour)
- Use `bd-cleanup` after crashes

---

## 3. Service Won't Start

### MCP Agent Mail

```bash
# Check status
sudo systemctl status mcp-agent-mail

# View logs
journalctl -u mcp-agent-mail -f

# Common fixes:

# 1. Port already in use
sudo lsof -i :8765
# Kill the process or change port

# 2. Database locked
rm ~/mcp_agent_mail/storage.sqlite3-wal
rm ~/mcp_agent_mail/storage.sqlite3-shm
sudo systemctl restart mcp-agent-mail

# 3. Permissions issue
sudo chown -R $USER:$USER ~/mcp_agent_mail
chmod 755 ~/mcp_agent_mail
chmod 644 ~/mcp_agent_mail/storage.sqlite3

# 4. Missing dependencies
cd ~/mcp_agent_mail
npm install

# 5. Reinstall from scratch
sudo systemctl stop mcp-agent-mail
rm -rf ~/mcp_agent_mail
# Re-run installation
```

### Ollama

```bash
# Check status
sudo systemctl status ollama

# View logs
journalctl -u ollama -f

# Common fixes:

# 1. Port in use
sudo lsof -i :11434

# 2. GPU issues (check CUDA)
nvidia-smi

# 3. Restart
sudo systemctl restart ollama

# 4. Reinstall
curl -fsSL https://ollama.ai/install.sh | sh
```

---

## 4. Multi-Agent Deadlock

### Symptoms
- Multiple agents waiting on each other's file reservations
- No agent making progress
- Circular dependency in reservations

### Detection

```bash
# List all active reservations with agents
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "
SELECT
    a.name as agent,
    fr.path_pattern,
    fr.reason
FROM file_reservations fr
JOIN agents a ON fr.agent_id = a.id
WHERE fr.released_ts IS NULL
ORDER BY a.name;
"

# Check agent inbox for blocking messages
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "
SELECT
    sender.name as from_agent,
    recipient.name as to_agent,
    m.subject
FROM messages m
JOIN agents sender ON m.sender_id = sender.id
JOIN message_recipients mr ON m.id = mr.message_id
JOIN agents recipient ON mr.recipient_id = recipient.id
WHERE m.subject LIKE '%BLOCKED%'
ORDER BY m.created_ts DESC
LIMIT 10;
"
```

### Resolution

**Option 1: Coordinate release order**
1. Identify which agent can make progress first
2. Have other agents release their reservations
3. Let first agent complete
4. Resume others in order

**Option 2: Release reservations**
```bash
# Release all reservations, let agents re-coordinate
bd-cleanup --release-all
```

**Option 3: Kill and restart**
```bash
# Kill stuck agents (in tmux)
ntm kill <session-name>

# Clean up state
bd-cleanup --force

# Restart
ntm spawn <session-name> --cc=2
```

### Prevention

- Design workflows to avoid overlapping file reservations
- Use shorter TTLs for reservations
- Implement reservation timeouts in agent code
- Use sequential workflows for shared files

---

## 5. State File Corruption

### Symptoms
- `json.JSONDecodeError` in hook logs
- Agent thinks it's registered but isn't
- Inconsistent behavior between sessions

### Recovery

```bash
# Reset state for current agent
bd-cleanup --reset-state

# For multi-agent, reset specific agent
rm ~/.claude/state-<AgentName>.json
rm ~/.claude/state-<AgentName>.lock

# Reset all agent state files
rm ~/.claude/state-*.json
rm ~/.claude/state-*.lock
rm ~/.claude/agent-state.json

# Clean up stale lock files (>1 hour old)
bd-cleanup --clean-locks
```

### Verify State Files

```bash
# Check state file validity
for f in ~/.claude/state-*.json ~/.claude/agent-state.json; do
    if [ -f "$f" ]; then
        echo "Checking $f:"
        python3 -m json.tool "$f" > /dev/null 2>&1 && echo "  Valid" || echo "  INVALID"
    fi
done
```

### Manual State Reset

```bash
# Write minimal valid state
echo '{"registered": false, "agent_name": null, "reservations": []}' > ~/.claude/agent-state.json
```

---

## 6. Hook Blocking All Operations

### Symptoms
- Every Edit/Write operation is blocked
- "Agent not registered" even after registering
- "File not reserved" even after reserving

### Diagnosis

```bash
# Check if hooks are the issue
FARMHAND_SKIP_ENFORCEMENT=1 claude
# If this works, hooks are the problem

# Check state file
cat ~/.claude/agent-state.json

# Check database connectivity
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "SELECT 1;"
```

### Recovery

```bash
# 1. Reset local state
bd-cleanup --reset-state

# 2. Manually register and reserve
sqlite3 ~/mcp_agent_mail/storage.sqlite3 "
-- Get or create project
INSERT OR IGNORE INTO projects (human_key, created_ts)
VALUES ('/home/ubuntu', datetime('now'));

-- Get or create agent
INSERT OR IGNORE INTO agents (project_id, name, program, model, created_ts)
SELECT id, 'RecoveryAgent', 'claude-code', 'opus', datetime('now')
FROM projects WHERE human_key = '/home/ubuntu';

-- Create reservation
INSERT INTO file_reservations (project_id, agent_id, path_pattern, exclusive, reason, created_ts, expires_ts)
SELECT p.id, a.id, '**/*', 1, 'recovery', datetime('now'), datetime('now', '+2 hours')
FROM projects p, agents a
WHERE p.human_key = '/home/ubuntu'
AND a.name = 'RecoveryAgent';
"

# 3. Update local state
echo '{"registered": true, "agent_name": "RecoveryAgent", "reservations": ["**/*"]}' > ~/.claude/agent-state.json

# 4. Start claude
claude
```

### Temporary Bypass

For emergencies, bypass enforcement entirely:
```bash
FARMHAND_SKIP_ENFORCEMENT=1 claude
```

**Warning:** This bypasses all safety checks. Only use for recovery.

---

## 7. Complete System Reset

If all else fails, perform a complete reset:

```bash
# 1. Stop services
sudo systemctl stop mcp-agent-mail ollama

# 2. Kill all agents
pkill -f "claude"
ntm kill --all 2>/dev/null || true

# 3. Clean all state
rm -rf ~/.claude/agent-state.json
rm -rf ~/.claude/state-*.json
rm -rf ~/.claude/state-*.lock

# 4. Reset databases (DESTRUCTIVE - loses history)
rm ~/mcp_agent_mail/storage.sqlite3*
# OR just release reservations:
# sqlite3 ~/mcp_agent_mail/storage.sqlite3 "UPDATE file_reservations SET released_ts = datetime('now') WHERE released_ts IS NULL;"

# 5. Restart services
sudo systemctl start mcp-agent-mail ollama

# 6. Verify
bd-cleanup --list
sudo systemctl status mcp-agent-mail ollama

# 7. Resume work
claude
```

---

## Diagnostic Commands Reference

| Command | Purpose |
|---------|---------|
| `bd-cleanup --list` | Show all orphaned items |
| `bd-cleanup --force` | Clean stale items automatically |
| `bd-cleanup --release-all` | Release all reservations |
| `bd-cleanup --reset-state` | Reset local agent state |
| `bd-cleanup --clean-locks` | Remove stale lock files |
| `sudo systemctl status mcp-agent-mail` | Check Agent Mail service |
| `journalctl -u mcp-agent-mail -f` | View Agent Mail logs |
| `sqlite3 <db> "PRAGMA integrity_check;"` | Check database integrity |
| `FARMHAND_SKIP_ENFORCEMENT=1 claude` | Bypass hooks (emergency only) |

---

## Getting Help

1. Check logs: `journalctl -u mcp-agent-mail -f`
2. Run diagnostics: `bd-cleanup --list`
3. Check GitHub issues: https://github.com/your-org/farmhand/issues
4. If stuck, use bypass: `FARMHAND_SKIP_ENFORCEMENT=1`
