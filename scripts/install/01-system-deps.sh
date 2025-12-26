#!/usr/bin/env bash
# NOTE: Dont use set -e - sourced by install.sh
# set -euo pipefail

# System dependencies: apt packages, Homebrew, Bun, uv

echo "==> Updating apt..."
sudo apt-get update

echo "==> Installing essential packages..."
sudo apt-get install -y \
    build-essential \
    curl \
    git \
    unzip \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    sqlite3

# Homebrew (Linuxbrew)
if ! command -v brew &>/dev/null; then
    echo "==> Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add to current session
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

    # Add to bashrc if not already there
    if ! grep -q 'linuxbrew' ~/.bashrc; then
        echo '' >> ~/.bashrc
        echo '# Homebrew' >> ~/.bashrc
        echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
    fi
else
    echo "==> Homebrew already installed"
fi

# Bun
if ! command -v bun &>/dev/null; then
    echo "==> Installing Bun..."
    curl -fsSL https://bun.sh/install | bash

    # Add to PATH for current session
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
else
    echo "==> Bun already installed"
fi

# uv (Python package manager)
if ! command -v uv &>/dev/null; then
    echo "==> Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "==> uv already installed"
fi

# Ensure ~/.local/bin exists
mkdir -p ~/.local/bin

echo "==> System dependencies installed"
