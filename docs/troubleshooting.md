# Troubleshooting

## Common Issues

### bd: command not found

The `bd` binary needs to be downloaded manually if the automatic download fails:

```bash
# Download from GitHub releases (check for latest version)
# See: https://github.com/steveyegge/beads/releases
curl -fsSL -o ~/.local/bin/bd \
  https://github.com/steveyegge/beads/releases/latest/download/bd-linux-amd64
chmod +x ~/.local/bin/bd

# Verify
bd --version
```

### bv: command not found

Install via Homebrew:

```bash
brew tap dicklesworthstone/beads
brew install beads-viewer
```

### MCP Agent Mail not connecting

1. Check service status:
```bash
sudo systemctl status mcp-agent-mail
```

2. Check logs:
```bash
sudo journalctl -u mcp-agent-mail -f
```

3. Verify token matches in Claude Code settings:
```bash
# Get the token from MCP Agent Mail
cat ~/mcp_agent_mail/.env

# Check Claude Code config
cat ~/.config/claude-code/settings.json | grep -A5 mcp-agent-mail
```

4. Restart the service:
```bash
sudo systemctl restart mcp-agent-mail
```

### Ollama models not loading

1. Check Ollama service:
```bash
sudo systemctl status ollama
```

2. Pull models manually:
```bash
ollama pull embeddinggemma:latest
ollama pull ExpedientFalcon/qwen3-reranker:0.6b-q8_0
ollama pull qwen3:0.6b
```

3. List installed models:
```bash
ollama list
```

### qmd search returns no results

1. Ensure Ollama is running:
```bash
sudo systemctl status ollama
```

2. Check qmd status:
```bash
qmd status
```

3. Re-index your documents:
```bash
cd ~/your-project
qmd add .
```

### PATH not set correctly

Add to your `~/.bashrc`:

```bash
export PATH="/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
export BUN_INSTALL="$HOME/.bun"
export BEADS_DB=/home/ubuntu/.beads/beads.db
```

Then reload:
```bash
source ~/.bashrc
```

## Service Management

```bash
# Check all services
sudo systemctl status mcp-agent-mail ollama

# Restart services
sudo systemctl restart mcp-agent-mail
sudo systemctl restart ollama

# View logs
sudo journalctl -u mcp-agent-mail -n 50
sudo journalctl -u ollama -n 50

# Enable services on boot
sudo systemctl enable mcp-agent-mail ollama
```

## Useful Ports

| Service | Port | URL |
|---------|------|-----|
| MCP Agent Mail | 8765 | http://127.0.0.1:8765/mail |
| Ollama | 11434 | http://127.0.0.1:11434 |

## Complete Reinstall

If all else fails:

```bash
# Stop services
sudo systemctl stop mcp-agent-mail ollama

# Remove installations
rm -rf ~/mcp_agent_mail ~/.beads ~/.bun

# Reinstall
cd ~/Farmhand
./scripts/install.sh
```

## Hook Failures

### "Agent not registered" - Edit/Write blocked

The reservation-checker hook blocks file edits until you register with Agent Mail:

```python
# Register first
register_agent(
    project_key="/home/ubuntu",
    program="claude-code",
    model="opus-4.5"
)
```

Or set the AGENT_NAME environment variable before starting claude:

```bash
export AGENT_NAME="MyAgent"
claude
```

### "File not reserved" - Edit/Write blocked

The reservation-checker hook requires file reservations before editing:

```python
file_reservation_paths(
    project_key="/home/ubuntu",
    agent_name="<your-agent-name>",
    paths=["path/to/file.py"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<issue-id>"
)
```

### "File reserved by another agent"

Another agent has the file reserved. Options:

1. **Wait** - The reservation will expire based on TTL
2. **Coordinate** - Send a message asking for release:
   ```python
   send_message(
       project_key="/home/ubuntu",
       sender_name="<your-name>",
       to=["<other-agent>"],
       subject="File access request",
       body_md="Need access to <file>. Can you release?"
   )
   ```
3. **Force release** - Use bd-cleanup (stale reservations only):
   ```bash
   bd-cleanup --list     # Check stale reservations
   bd-cleanup --force    # Release stale (>4h old)
   ```

### TodoWrite is blocked

The todowrite-interceptor hook redirects to beads:

```bash
# Instead of TodoWrite, use:
bd create --title="Task description" --type=task
bd update <id> --status=in_progress
bd close <id> --reason="Done"
bd ready  # List available work
```

### Hooks not loading

1. Check settings.json exists:
   ```bash
   cat ~/.claude/settings.json
   ```

2. Verify hooks are executable:
   ```bash
   ls -la ~/.claude/hooks/
   chmod +x ~/.claude/hooks/*.py
   ```

3. Test hooks manually:
   ```bash
   echo '{"tool_name":"Edit","tool_input":{"file_path":"/test.py"}}' | \
     python ~/.claude/hooks/reservation-checker.py
   ```

4. Check for Python errors:
   ```bash
   python ~/.claude/hooks/reservation-checker.py < /dev/null 2>&1
   ```

### Bypassing hooks (emergency only)

For experienced users who need to bypass enforcement temporarily:

```bash
export FARMHAND_SKIP_ENFORCEMENT=1
claude
# Edit files without reservations
unset FARMHAND_SKIP_ENFORCEMENT
```

**Use sparingly** - hooks protect against multi-agent conflicts.

### State file corruption

If agent state becomes corrupted:

```bash
# Reset local state only
bd-cleanup --reset-state

# Or manually:
rm ~/.claude/agent-state.json
rm ~/.claude/state-*.json
```

### Health monitoring

The mcp-health-check timer runs every 5 minutes. Check status:

```bash
systemctl --user status mcp-health-check.timer
journalctl --user -u mcp-health-check -n 20

# Manual health check
mcp-health-check
```
