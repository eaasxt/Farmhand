#!/usr/bin/env bash
# 08-shell-config.sh - Shell configuration
# zsh, oh-my-zsh, powerlevel10k, plugins, modern CLI tools

set -euo pipefail

echo "[8/9] Configuring shell environment..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../.."

# Install zsh if not present
if ! command -v zsh &>/dev/null; then
    echo "    Installing zsh..."
    sudo apt-get install -y zsh
fi

# Install Oh My Zsh if not present (ACFS backport: version pinning for stability)
OMZ_COMMIT="d68d445f4b4ffb2d726d4ccf2d62e2cb08a0f5de"  # Pinned stable version
if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
    echo "    Installing Oh My Zsh (pinned to stable commit)..."
    # Use pinned version for reproducible installs
    RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/${OMZ_COMMIT}/tools/install.sh)" || \
    RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
else
    echo "    Oh My Zsh already installed"
fi

# Install Powerlevel10k theme
P10K_DIR="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k"
if [[ ! -d "$P10K_DIR" ]]; then
    echo "    Installing Powerlevel10k..."
    git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$P10K_DIR"
else
    echo "    Powerlevel10k already installed"
fi

# Install zsh plugins
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

if [[ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]]; then
    echo "    Installing zsh-autosuggestions..."
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

if [[ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]]; then
    echo "    Installing zsh-syntax-highlighting..."
    git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
fi

# Install modern CLI tools via Homebrew
echo "    Installing modern CLI tools..."
if command -v brew &>/dev/null; then
    brew install lsd bat lazygit fzf zoxide atuin 2>/dev/null || true
else
    echo "    WARNING: Homebrew not available, some tools may be missing"
    # Fallback installations
    sudo apt-get install -y bat 2>/dev/null || true

    # fzf
    if ! command -v fzf &>/dev/null; then
        git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf 2>/dev/null || true
        ~/.fzf/install --all 2>/dev/null || true
    fi

    # zoxide
    if ! command -v zoxide &>/dev/null; then
        curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | bash 2>/dev/null || true
    fi

    # atuin
    if ! command -v atuin &>/dev/null; then
        curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh 2>/dev/null || true
    fi
fi

# Backup existing configs
if [[ -f "$HOME/.zshrc" ]] && [[ ! -f "$HOME/.zshrc.backup" ]]; then
    cp "$HOME/.zshrc" "$HOME/.zshrc.backup"
    echo "    Backed up existing .zshrc"
fi

# Install zshrc template
echo "    Installing zshrc configuration..."
cp "$REPO_ROOT/config/zshrc.template" "$HOME/.zshrc"

# Install p10k configuration
echo "    Installing Powerlevel10k configuration..."
cp "$REPO_ROOT/config/p10k.zsh" "$HOME/.p10k.zsh"

# Set zsh as default shell (optional, requires password)
if [[ "$SHELL" != *"zsh"* ]]; then
    echo "    NOTE: Run 'chsh -s \$(which zsh)' to set zsh as default shell"
fi

echo "    Shell configuration complete"
echo "    Run 'exec zsh' to start using the new shell"
