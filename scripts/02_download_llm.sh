#!/bin/bash
# ============================================================
# 02_download_llm.sh
# Downloads configured GGUF model from Hugging Face.
# ============================================================

set -euo pipefail
export PYTHONWARNINGS="ignore"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Auto-load environment variables from .env if present
if [ -r "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

MODEL_REPO="${1:-${HF_REPO:-Qwen/Qwen2.5-Coder-7B-Instruct-GGUF}}"
MODEL_FILE="${2:-${HF_FILE:-qwen2.5-coder-7b-instruct-q4_k_m.gguf}}"
TARGET_DIR="$HOME/models"
TARGET_PATH="$TARGET_DIR/$MODEL_FILE"

echo "========================================================"
echo "  Step 2: Download GGUF Model"
echo "========================================================"

mkdir -p "$TARGET_DIR"

if [ -f "$TARGET_PATH" ]; then
    echo "  [OK] Model file already exists at: $TARGET_PATH"
else
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
        echo "  [INFO] huggingface_hub not found. Running 01_setup_env.sh..."
        bash "$SCRIPT_DIR/01_setup_env.sh"
    fi

    echo "  [INFO] Downloading model..."
    echo "  Repo: $MODEL_REPO"
    echo "  File: $MODEL_FILE"
    echo "  Destination: $TARGET_DIR"
    
    CACHE_PATH=$("$PYTHON_CMD" -c "from huggingface_hub import hf_hub_download; print(hf_hub_download(repo_id='$MODEL_REPO', filename='$MODEL_FILE'))")
    
    if [ -f "$CACHE_PATH" ]; then
        ln -sf "$CACHE_PATH" "$TARGET_PATH"
    else
        echo "  [ERROR] Failed to find downloaded model in cache."
        exit 1
    fi
        
    echo "  [OK] Model download completed successfully."
fi

echo "  Model location: $TARGET_PATH"
echo "========================================================"
echo "  Next: bash scripts/03_serve_llm.sh"
echo "========================================================"
