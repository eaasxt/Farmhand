# Troubleshooting

## Common Issues

### bd: command not found

The `bd` binary needs to be downloaded manually if the automatic download fails:

```bash
# Download from GitHub releases
curl -fsSL -o ~/.local/bin/bd \
  https://github.com/Dicklesworthstone/beads/releases/download/v0.2.0/bd-linux-amd64
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
cd ~/JohnDeere
./scripts/install.sh
```
