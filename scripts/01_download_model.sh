#!/bin/bash
# ============================================================
# 01_download_model.sh
# Downloads the 4-bit quantized Qwen2.5-Coder-7B-Instruct GGUF model
# from HuggingFace using huggingface-cli.
# ============================================================

set -euo pipefail

# Disable Rust/Xet downloaders as they hang on this macOS/network environment
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_XET_HIGH_PERFORMANCE=1
export HF_HUB_DISABLE_XET=1

# Silence python deprecation warnings during download
export PYTHONWARNINGS="ignore"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Function to load a variable from .env
load_env_var() {
    local var_name=$1
    local default_val=${2:-""}
    local env_file="$PROJECT_ROOT/.env"
    if [ -f "$env_file" ]; then
        local val
        val=$(grep -E "^${var_name}=" "$env_file" | head -n 1 | cut -d'=' -f2- | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        if [ -n "$val" ]; then
            echo "$val"
            return
        fi
    fi
    echo "$default_val"
}

# If no .env exists yet, copy the example
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "  [INFO] .env not found. Copying .env.example to .env..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
fi

MODEL_REPO=$(load_env_var "HF_REPO" "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF")
MODEL_FILE=$(load_env_var "HF_FILE" "qwen2.5-coder-7b-instruct-q4_k_m.gguf")
TARGET_DIR="$HOME/models"
TARGET_PATH="$TARGET_DIR/$MODEL_FILE"

echo "========================================================"
echo "  Step 1: Download Qwen2.5 Coder Model"
echo "========================================================"

# Make sure target directory exists
mkdir -p "$TARGET_DIR"

if [ -f "$TARGET_PATH" ]; then
    echo "  [OK] Model file already exists at: $TARGET_PATH"
else
    # Resolve the CLI command (prefer hf, fallback to huggingface-cli, check both PATH and .venv)
    CLI_CMD=""
    if command -v hf &> /dev/null; then
        CLI_CMD="hf"
    elif [ -f "$PROJECT_ROOT/.venv/bin/hf" ]; then
        CLI_CMD="$PROJECT_ROOT/.venv/bin/hf"
    elif command -v huggingface-cli &> /dev/null; then
        CLI_CMD="huggingface-cli"
    elif [ -f "$PROJECT_ROOT/.venv/bin/huggingface-cli" ]; then
        CLI_CMD="$PROJECT_ROOT/.venv/bin/huggingface-cli"
    fi

    if [ -z "$CLI_CMD" ]; then
        echo "ERROR: Hugging Face CLI (hf or huggingface-cli) not found."
        echo "Please install it using: uv pip install huggingface_hub"
        exit 1
    fi

    echo "  [INFO] Model not found. Downloading..."
    echo "  Repo: $MODEL_REPO"
    echo "  File: $MODEL_FILE"
    echo "  Destination: $TARGET_DIR"
    # Use python directly to reliably get the path without warnings
    CACHE_PATH=$("$PROJECT_ROOT/.venv/bin/python" -c "from huggingface_hub import hf_hub_download; print(hf_hub_download(repo_id='$MODEL_REPO', filename='$MODEL_FILE'))")
    
    if [ -f "$CACHE_PATH" ]; then
        ln -sf "$CACHE_PATH" "$TARGET_PATH"
    else
        echo "  [ERROR] Failed to find the downloaded model in cache."
        exit 1
    fi
        
    echo ""
    echo "  [OK] Model download completed successfully."
fi

echo "  Model location: $TARGET_PATH"
echo "========================================================"
echo "  Next: bash scripts/02_serve_model.sh"
echo "========================================================"
