# JohnDeere VM Bootstrap

Quick setup for a fully-configured Claude Code development VM with multi-agent coordination.

---

## FOR CLAUDE CODE: Autonomous Bootstrap Instructions

**If you are Claude Code reading this on a fresh VM, follow these steps exactly to bootstrap the environment.**

### Pre-flight Check

First, verify what's already installed:

```bash
# Run these checks and note what's missing
command -v git && echo "git: OK" || echo "git: MISSING"
command -v curl && echo "curl: OK" || echo "curl: MISSING"
command -v brew && echo "brew: OK" || echo "brew: MISSING"
command -v bun && echo "bun: OK" || echo "bun: MISSING"
command -v uv && echo "uv: OK" || echo "uv: MISSING"
command -v bd && echo "bd: OK" || echo "bd: MISSING"
command -v bv && echo "bv: OK" || echo "bv: MISSING"
command -v qmd && echo "qmd: OK" || echo "qmd: MISSING"
command -v ollama && echo "ollama: OK" || echo "ollama: MISSING"
systemctl is-active mcp-agent-mail 2>/dev/null && echo "mcp-agent-mail: RUNNING" || echo "mcp-agent-mail: NOT RUNNING"
systemctl is-active ollama 2>/dev/null && echo "ollama service: RUNNING" || echo "ollama service: NOT RUNNING"
test -f ~/.beads/beads.db && echo "beads db: OK" || echo "beads db: MISSING"
test -f ~/CLAUDE.md && echo "CLAUDE.md: OK" || echo "CLAUDE.md: MISSING"
```

### Step 1: System Dependencies

```bash
# Update apt and install essentials
sudo apt-get update
sudo apt-get install -y build-essential curl git unzip wget ca-certificates gnupg lsb-release sqlite3
```

### Step 2: Homebrew (if missing)

```bash
# Check if brew exists
if ! command -v brew &>/dev/null; then
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi
```

### Step 3: Bun (if missing)

```bash
if ! command -v bun &>/dev/null; then
    curl -fsSL https://bun.sh/install | bash
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
fi
```

### Step 4: uv (if missing)

```bash
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
```

### Step 5: bd (Beads CLI)

```bash
mkdir -p ~/.local/bin ~/.beads

if ! command -v bd &>/dev/null; then
    # Download from steveyegge/beads releases
    curl -fsSL -o ~/.local/bin/bd "https://github.com/steveyegge/beads/releases/download/v0.29.0/bd_linux_amd64" || \
    curl -fsSL -o ~/.local/bin/bd "https://github.com/steveyegge/beads/releases/download/v0.29.0/bd-linux-amd64"
    chmod +x ~/.local/bin/bd
fi

# Initialize beads if needed
export BEADS_DB=~/.beads/beads.db
if [ ! -f ~/.beads/beads.db ]; then
    ~/.local/bin/bd init 2>/dev/null || true
fi
```

### Step 6: bv (Beads Viewer)

```bash
if ! command -v bv &>/dev/null; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    # Try homebrew first
    brew tap dicklesworthstone/beads 2>/dev/null && brew install beads-viewer 2>/dev/null || {
        # Fallback: download binary
        curl -fsSL "https://github.com/Dicklesworthstone/beads_viewer/releases/download/v0.10.2/beads_viewer_linux_amd64.tar.gz" | tar -xz -C /tmp
        mv /tmp/bv ~/.local/bin/bv
        chmod +x ~/.local/bin/bv
    }
fi
```

### Step 7: qmd (Markdown Search)

```bash
if ! command -v qmd &>/dev/null; then
    export PATH="$HOME/.bun/bin:$PATH"
    bun install -g https://github.com/tobi/qmd

    # Create wrapper script
    cat > ~/.local/bin/qmd << 'EOF'
#!/bin/bash
exec "$HOME/.bun/bin/bun" "$HOME/.bun/install/global/node_modules/qmd/qmd.ts" "$@"
EOF
    chmod +x ~/.local/bin/qmd
fi
```

### Step 8: Ollama

```bash
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Enable and start service
sudo systemctl enable ollama
sudo systemctl start ollama

# Wait for Ollama to be ready
for i in {1..30}; do
    curl -s http://localhost:11434/api/version &>/dev/null && break
    sleep 1
done

# Pull required models
ollama pull embeddinggemma:latest
ollama pull ExpedientFalcon/qwen3-reranker:0.6b-q8_0
ollama pull qwen3:0.6b
```

### Step 9: MCP Agent Mail

```bash
if [ ! -d ~/mcp_agent_mail ]; then
    git clone https://github.com/Dicklesworthstone/mcp_agent_mail.git ~/mcp_agent_mail
fi

cd ~/mcp_agent_mail

# Install Python 3.14 and dependencies
uv python install 3.14 2>/dev/null || true
uv sync

# Generate bearer token if needed
if [ ! -f .env ] || ! grep -q 'HTTP_BEARER_TOKEN=' .env; then
    TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "HTTP_BEARER_TOKEN=$TOKEN" > .env
fi

# Get the token for later
TOKEN=$(grep 'HTTP_BEARER_TOKEN=' .env | cut -d'=' -f2)
```

### Step 10: Systemd Services

```bash
# Create MCP Agent Mail service
sudo tee /etc/systemd/system/mcp-agent-mail.service << 'EOF'
[Unit]
Description=MCP Agent Mail Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/mcp_agent_mail
Environment="PATH=/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HOME=/home/ubuntu"
ExecStart=/bin/bash -c 'source /home/ubuntu/.local/bin/env && /home/ubuntu/mcp_agent_mail/scripts/run_server_with_token.sh'
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mcp-agent-mail
sudo systemctl start mcp-agent-mail
```

### Step 11: Claude Code Configuration

```bash
mkdir -p ~/.config/claude-code

# Get token from MCP Agent Mail
TOKEN=$(grep 'HTTP_BEARER_TOKEN=' ~/mcp_agent_mail/.env | cut -d'=' -f2)

# Create settings.json
cat > ~/.config/claude-code/settings.json << EOF
{
  "mcpServers": {
    "mcp-agent-mail": {
      "type": "http",
      "url": "http://127.0.0.1:8765/mcp/",
      "headers": {
        "Authorization": "Bearer $TOKEN"
      }
    }
  }
}
EOF
```

### Step 12: Environment Setup

```bash
# Add to bashrc if not already there
if ! grep -q 'BEADS_DB' ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# JohnDeere Development Environment
export PATH="/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
export BUN_INSTALL="$HOME/.bun"
export BEADS_DB=/home/ubuntu/.beads/beads.db
EOF
fi

# Source it now
export PATH="/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
export BEADS_DB=/home/ubuntu/.beads/beads.db
```

### Step 13: Copy CLAUDE.md

```bash
# Copy CLAUDE.md to home directory
cp ~/JohnDeere/config/CLAUDE.md ~/CLAUDE.md

# Add bearer token to local copy
TOKEN=$(grep 'HTTP_BEARER_TOKEN=' ~/mcp_agent_mail/.env | cut -d'=' -f2)

# Insert token after project structure (use sed or manual edit)
sed -i "/└── CLAUDE.md            # This file/a\\
\\\n**Bearer Token (remote access only):**\\\n\\\n\\\`\\\`\\\`\\\n$TOKEN\\\n\\\`\\\`\\\`\\\n\\\nLocalhost bypasses auth." ~/CLAUDE.md
```

### Step 14: Final Verification

Run each of these and confirm all pass:

```bash
echo "=== VERIFICATION ==="
command -v bd && bd --version
command -v bv && bv --version 2>/dev/null || echo "bv installed"
command -v qmd && echo "qmd: OK"
command -v ollama && ollama --version
systemctl is-active mcp-agent-mail && echo "mcp-agent-mail: RUNNING"
systemctl is-active ollama && echo "ollama: RUNNING"
curl -s http://localhost:8765/health && echo "MCP Agent Mail API: OK"
curl -s http://localhost:11434/api/version && echo "Ollama API: OK"
test -f ~/.beads/beads.db && echo "Beads DB: OK"
test -f ~/CLAUDE.md && echo "CLAUDE.md: OK"
test -f ~/.config/claude-code/settings.json && echo "Claude settings: OK"
ollama list | grep -q embeddinggemma && echo "embeddinggemma model: OK"
echo "=== DONE ==="
```

### Post-Bootstrap

Once verification passes:

1. Read `~/CLAUDE.md` for workflow instructions
2. Run `bd ready` to see available work
3. Run `bd stats` to check project health

---

## What's Included

| Tool | Description |
|------|-------------|
| `bd` (beads) | Issue/task tracking CLI |
| `bv` (beads-viewer) | Graph visualization for issues |
| `qmd` | Markdown semantic search |
| MCP Agent Mail | Multi-agent coordination server |
| Ollama | Local LLM for embeddings/reranking |

## Quick Start (Human)

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
│   ├── systemd/          # Service files
│   └── beads/            # Beads configuration
└── docs/
    └── troubleshooting.md
```

## Requirements

- Ubuntu 22.04+ (tested on Ubuntu 22.04 LTS)
- At least 4GB RAM (8GB recommended for Ollama)
- Internet connection

## Tool Sources

| Tool | Repository |
|------|------------|
| bd | [steveyegge/beads](https://github.com/steveyegge/beads) |
| bv | [Dicklesworthstone/beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) |
| qmd | [tobi/qmd](https://github.com/tobi/qmd) |
| MCP Agent Mail | [Dicklesworthstone/mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail) |

## License

Private repository - internal use only.
