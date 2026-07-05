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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Function to load a variable from environment or .env
load_env_var() {
    local var_name=$1
    local default_val=${2:-""}

    if [ -n "${!var_name:-}" ]; then
        echo "${!var_name}"
        return
    fi

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



MODEL_REPO="${1:-$(load_env_var "HF_REPO" "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF")}"
MODEL_FILE="${2:-$(load_env_var "HF_FILE" "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf")}"
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
    # Resolve Python command (prefer .venv, fallback to active Conda / system python)
    PYTHON_CMD=""
    if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "ERROR: Python interpreter not found."
        exit 1
    fi

    if ! "$PYTHON_CMD" -c "import huggingface_hub" &> /dev/null; then
        echo "ERROR: huggingface_hub package is not installed."
        echo "Please install it using: pip install huggingface_hub  (or uv pip install huggingface_hub)"
        exit 1
    fi

    echo "  [INFO] Model not found. Downloading..."
    echo "  Repo: $MODEL_REPO"
    echo "  File: $MODEL_FILE"
    echo "  Destination: $TARGET_DIR"
    # Use python directly to reliably get the path without warnings
    CACHE_PATH=$("$PYTHON_CMD" -c "from huggingface_hub import hf_hub_download; print(hf_hub_download(repo_id='$MODEL_REPO', filename='$MODEL_FILE'))")
    
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
