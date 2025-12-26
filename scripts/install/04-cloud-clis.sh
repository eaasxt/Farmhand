#!/usr/bin/env bash
# 04-cloud-clis.sh - Cloud CLI tools
# vault, wrangler, supabase, vercel

# NOTE: Dont use set -e - sourced by install.sh
# set -euo pipefail

echo "[5/9] Installing Cloud CLIs..."

# HashiCorp Vault
if ! command -v vault &>/dev/null; then
    echo "    Installing vault..."
    # Add HashiCorp GPG key and repo
    wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg 2>/dev/null
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list >/dev/null
    sudo apt-get update -qq
    sudo apt-get install -y vault
    echo "    vault installed: $(vault --version)"
else
    echo "    vault already installed: $(vault --version)"
fi

# Cloudflare Wrangler
if ! command -v wrangler &>/dev/null; then
    echo "    Installing wrangler..."
    bun install -g wrangler
    echo "    wrangler installed: $(wrangler --version)"
else
    echo "    wrangler already installed: $(wrangler --version)"
fi

# Supabase CLI (ACFS backport: improved reliability)
if ! command -v supabase &>/dev/null; then
    echo "    Installing supabase..."
    # Prefer Homebrew for stable releases
    if command -v brew &>/dev/null; then
        if brew tap supabase/tap 2>/dev/null && brew install supabase/tap/supabase 2>/dev/null; then
            echo "    supabase installed via Homebrew"
        else
            echo "    WARNING: Homebrew install failed, trying bun..."
            bun install -g supabase 2>/dev/null || echo "    WARNING: supabase installation failed"
        fi
    else
        # Fallback to bun
        bun install -g supabase 2>/dev/null || echo "    WARNING: supabase installation failed"
    fi
    if command -v supabase &>/dev/null; then
        echo "    supabase installed: $(supabase --version)"
    fi
else
    echo "    supabase already installed: $(supabase --version)"
fi

# Vercel CLI
if ! command -v vercel &>/dev/null; then
    echo "    Installing vercel..."
    bun install -g vercel
    echo "    vercel installed: $(vercel --version)"
else
    echo "    vercel already installed: $(vercel --version)"
fi

echo "    Cloud CLIs complete"
