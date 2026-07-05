#!/bin/bash
# ============================================================
# 02_download_model.sh
# Downloads configured GGUF model from Hugging Face.
# ============================================================

set -euo pipefail
export PYTHONWARNINGS="ignore"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Auto-load environment variables
source "$SCRIPT_DIR/00_load_env.sh" 2>/dev/null || true

MODEL_REPO="${1:-${HF_REPO:-Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF}}"
MODEL_FILE="${2:-${HF_FILE:-qwen2.5-coder-1.5b-instruct-q4_k_m.gguf}}"
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
        echo "  [INFO] huggingface_hub not found. Running 01_install_dependencies.sh..."
        bash "$SCRIPT_DIR/01_install_dependencies.sh"
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
echo "  Next: bash scripts/03_serve_model.sh"
echo "========================================================"
