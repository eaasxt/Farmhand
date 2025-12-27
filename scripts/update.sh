#!/usr/bin/env bash
set -euo pipefail

# Update Farmhand tools to latest versions

echo "=== Updating Farmhand Tools ==="

# Update this repo first
echo ""
echo "==> Pulling latest Farmhand repo..."
cd ~/Farmhand
git pull origin main 2>/dev/null || git pull https://github.com/eaasxt/Farmhand.git main

# Update bd
echo ""
echo "==> Checking bd for updates..."
CURRENT_BD=$(~/.local/bin/bd --version 2>/dev/null | grep -oP 'v?\d+\.\d+\.\d+' | head -1 || echo "unknown")
echo "    Current: $CURRENT_BD"
echo "    Check https://github.com/steveyegge/beads/releases for latest"

# Update bv
echo ""
echo "==> Updating bv via Homebrew..."
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" 2>/dev/null || true
brew upgrade beads-viewer 2>/dev/null || echo "    bv already up to date (or not installed via brew)"

# Update qmd
echo ""
echo "==> Updating qmd..."
bun install -g https://github.com/tobi/qmd 2>/dev/null || echo "    qmd update skipped"

# Update MCP Agent Mail
echo ""
echo "==> Updating MCP Agent Mail..."
cd ~/mcp_agent_mail
git pull origin main 2>/dev/null || true
uv sync 2>/dev/null || true
sudo systemctl restart mcp-agent-mail

# Re-copy hooks (in case they were updated)
echo ""
echo "==> Updating hooks..."
mkdir -p ~/.claude/hooks
cp ~/Farmhand/hooks/*.py ~/.claude/hooks/
cp ~/Farmhand/bin/bd-cleanup ~/.local/bin/
chmod +x ~/.claude/hooks/*.py ~/.local/bin/bd-cleanup

# Regenerate settings.json from template (keeps all hooks in sync)
echo ""
echo "==> Updating hook configuration..."
TEMPLATE_FILE=~/Farmhand/config/claude-settings.json
if [[ -f "$TEMPLATE_FILE" ]]; then
    # Backup current settings
    [[ -f ~/.claude/settings.json ]] && cp ~/.claude/settings.json ~/.claude/settings.json.bak
    # Use template with __HOME__ substitution (same as install script)
    sed "s|__HOME__|$HOME|g" "$TEMPLATE_FILE" > ~/.claude/settings.json
    chmod 600 ~/.claude/settings.json
    echo "    Installed settings.json from template"
else
    echo "    WARNING: Template not found at $TEMPLATE_FILE"
    echo "    settings.json not updated - pull Farmhand repo first"
fi

# Update CLAUDE.md
echo ""
echo "==> Updating CLAUDE.md..."
cp ~/Farmhand/config/CLAUDE.md ~/CLAUDE.md
# Re-add bearer token
TOKEN=$(grep 'HTTP_BEARER_TOKEN=' ~/mcp_agent_mail/.env 2>/dev/null | cut -d'=' -f2)
if [ -n "$TOKEN" ]; then
    echo "" >> ~/CLAUDE.md
    echo "## Bearer Token (remote access)" >> ~/CLAUDE.md
    echo "" >> ~/CLAUDE.md
    echo '```' >> ~/CLAUDE.md
    echo "$TOKEN" >> ~/CLAUDE.md
    echo '```' >> ~/CLAUDE.md
    echo "" >> ~/CLAUDE.md
    echo "Localhost bypasses auth." >> ~/CLAUDE.md
fi

# Update Gemini settings (hideWindowTitle prevents NTM pane title conflicts)
echo ""
echo "==> Updating Gemini settings..."
GEMINI_SETTINGS=~/.gemini/settings.json
if command -v gemini &>/dev/null || [[ -d ~/.gemini ]]; then
    mkdir -p ~/.gemini
    if [[ -f "$GEMINI_SETTINGS" ]]; then
        if ! grep -q "hideWindowTitle" "$GEMINI_SETTINGS" 2>/dev/null; then
            if command -v jq &>/dev/null; then
                jq '. + {"ui": {"hideWindowTitle": true}}' "$GEMINI_SETTINGS" > "$GEMINI_SETTINGS.tmp" && \
                    mv "$GEMINI_SETTINGS.tmp" "$GEMINI_SETTINGS"
                echo "    Added hideWindowTitle=true to Gemini settings"
            else
                echo "    WARNING: jq not available, manual fix needed"
            fi
        else
            echo "    Gemini hideWindowTitle already configured"
        fi
    else
        cat > "$GEMINI_SETTINGS" << 'EOF'
{
  "ui": {
    "hideWindowTitle": true
  }
}
EOF
        echo "    Created Gemini settings with hideWindowTitle=true"
    fi
else
    echo "    Gemini not installed, skipping"
fi

echo ""
echo "=== Update Complete ==="
echo "Run './scripts/verify.sh' to verify"
