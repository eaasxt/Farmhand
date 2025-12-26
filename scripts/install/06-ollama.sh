#!/usr/bin/env bash
# NOTE: Dont use set -e - sourced by install.sh
# set -euo pipefail

# Install Ollama and required models

echo "==> Installing Ollama..."

# Install Ollama if not present
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "    Ollama already installed"
fi

# Start Ollama service temporarily to pull models
echo "==> Starting Ollama service..."
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl start ollama 2>/dev/null || {
    # If systemd fails, start manually in background
    ollama serve &
    sleep 3
}

# Wait for Ollama to be ready
echo "==> Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/version &>/dev/null; then
        break
    fi
    sleep 1
done

# Pull required models for qmd
echo "==> Pulling embedding model (embeddinggemma)..."
ollama pull embeddinggemma:latest || echo "    Warning: Could not pull embeddinggemma"

echo "==> Pulling reranker model (qwen3-reranker)..."
ollama pull ExpedientFalcon/qwen3-reranker:0.6b-q8_0 || echo "    Warning: Could not pull reranker"

echo "==> Pulling small LLM for qmd (qwen3:0.6b)..."
ollama pull qwen3:0.6b || echo "    Warning: Could not pull qwen3"

echo "==> Ollama setup complete"
ollama list
