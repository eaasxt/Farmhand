#!/usr/bin/env bash
# NOTE: Dont use set -e - sourced by install.sh
# set -euo pipefail

# Install Ollama and required models

# Load timeout wrapper for robust operations
_SCRIPT_DIR_06="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT_06="$(dirname "$(dirname "$_SCRIPT_DIR_06")")"
source "$_REPO_ROOT_06/lib/timeout-wrapper.sh" 2>/dev/null || {
    echo "Warning: timeout-wrapper.sh not found, using fallback methods"
}

echo "==> Installing Ollama..."

# Install Ollama if not present with network retry
if ! command -v ollama &>/dev/null; then
    echo "    Downloading Ollama installer..."
    
    # Use timeout wrapper if available, otherwise fallback to basic curl
    if declare -f network_retry >/dev/null 2>&1; then
        network_retry 3 2 curl -fsSL https://ollama.com/install.sh | sh
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
else
    echo "    Ollama already installed"
fi

# IMPROVED: Robust service startup with health check
echo "==> Starting Ollama service..."
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl start ollama 2>/dev/null || {
    # If systemd fails, start manually in background
    echo "    systemctl failed, starting manually..."
    ollama serve &
    sleep 5
}

# IMPROVED: Use wait_for_service with longer timeout
echo "==> Waiting for Ollama to be ready..."
if declare -f wait_for_service >/dev/null 2>&1; then
    # Use robust health check (2 minute timeout)
    wait_for_service "Ollama" "curl -s http://localhost:11434/api/version" 120 5
else
    # Fallback to original logic but with longer timeout
    echo "    Using fallback startup check..."
    for i in {1..60}; do  # Increased from 30 to 60 seconds
        if curl -s http://localhost:11434/api/version &>/dev/null; then
            echo "    ✓ Ollama ready after ${i}s"
            break
        fi
        sleep 2
        if [[ $((i % 15)) -eq 0 ]]; then
            echo "    ... still waiting for Ollama (${i}s elapsed)"
        fi
    done
fi

# IMPROVED: Model downloads with timeout and progress tracking
# Models required for qmd (semantic search)
declare -a MODELS=(
    "embeddinggemma:latest"
    "ExpedientFalcon/qwen3-reranker:0.6b-q8_0" 
    "qwen3:0.6b"
)

declare -a MODEL_NAMES=(
    "embedding model (embeddinggemma)"
    "reranker model (qwen3-reranker)"
    "small LLM for qmd (qwen3:0.6b)"
)

echo "==> Pulling required models..."

failed_models=()
for i in "${!MODELS[@]}"; do
    model="${MODELS[i]}"
    name="${MODEL_NAMES[i]}"
    
    echo "==> Pulling $name..."
    
    # Use timeout wrapper if available (5 minute timeout per model)
    if declare -f ollama_pull_with_timeout >/dev/null 2>&1; then
        if ollama_pull_with_timeout "$model" 300; then
            echo "    ✓ Successfully pulled $model"
        else
            echo "    ✗ Failed to pull $model"
            failed_models+=("$model")
        fi
    else
        # Fallback with basic timeout
        echo "    Using fallback download method..."
        if timeout 300 ollama pull "$model"; then
            echo "    ✓ Successfully pulled $model"
        else
            echo "    ✗ Warning: Could not pull $model (timeout or failure)"
            failed_models+=("$model")
        fi
    fi
    
    # Brief pause between downloads to avoid overwhelming the service
    sleep 2
done

# Report results
echo "==> Ollama setup complete"

if [[ ${#failed_models[@]} -eq 0 ]]; then
    echo "    ✓ All models downloaded successfully"
else
    echo "    ⚠ Some models failed to download:"
    for model in "${failed_models[@]}"; do
        echo "      - $model"
    done
    echo ""
    echo "    You can retry failed downloads manually:"
    for model in "${failed_models[@]}"; do
        echo "      ollama pull $model"
    done
fi

echo ""
echo "Available models:"
ollama list

# Create recovery script for failed downloads
if [[ ${#failed_models[@]} -gt 0 ]]; then
    recovery_script="$HOME/.farmhand/retry-ollama-downloads.sh"
    mkdir -p "$(dirname "$recovery_script")"
    
    cat > "$recovery_script" << RECOVERY_EOF
#!/bin/bash
# Auto-generated Ollama model recovery script
# Run this to retry failed model downloads

echo "Retrying failed Ollama model downloads..."

RECOVERY_EOF
    
    for model in "${failed_models[@]}"; do
        echo "ollama pull $model" >> "$recovery_script"
    done
    
    chmod +x "$recovery_script"
    echo "    Recovery script created: $recovery_script"
fi

