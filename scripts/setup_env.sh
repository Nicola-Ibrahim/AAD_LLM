#!/bin/bash
# ============================================================
# setup_env.sh
# Initializes the environment, checks environment variables, and installs dependencies.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if .env exists, create if not
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "  [INFO] Creating default .env file..."
    printf "%s\n" \
        "# ---------------------------------------------------------------------" \
        "# Local LLaMA.cpp Server / LM Studio Configuration" \
        "# ---------------------------------------------------------------------" \
        "LLM_PROVIDER=local" \
        "DATABASE_URL=sqlite:///data/db.sqlite3" \
        "HF_REPO=Qwen/Qwen2.5-Coder-7B-Instruct-GGUF" \
        "HF_FILE=qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
        "LOCAL_LLM_MODEL=qwen2.5-coder-7b-instruct-q4_k_m" \
        "LOCAL_LLM_BASE_URL=http://localhost:1234/v1" \
        "LOCAL_LLM_API_KEY=not-needed" \
        "" \
        "# Local Server Runtime Configuration" \
        "LLM_SERVER_HOST=0.0.0.0" \
        "LLM_SERVER_PORT=1234" \
        "LLM_SERVER_N_CTX=8192" \
        "LLM_SERVER_N_THREADS=8" > "$PROJECT_ROOT/.env"
    echo "  [OK] Default .env file created."
fi

# Auto-load environment variables from .env if present
if [ -r "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

echo "========================================================"
echo "  Step 1: Install Dependencies"
echo "========================================================"

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

echo "  [INFO] Using Python: $PYTHON_CMD ($("$PYTHON_CMD" --version))"

if command -v uv &> /dev/null; then
    echo "  [INFO] uv detected. Initializing environment via 'uv sync'..."
    uv sync --all-extras
    echo "  [OK] uv environment successfully synchronized."
else
    echo "  [WARNING] uv not found. Falling back to pip installation..."
    # Fallback to standard pip setup
    "$PYTHON_CMD" -m pip install --upgrade pip
    "$PYTHON_CMD" -m pip install -e "$PROJECT_ROOT[gemini,notebook]" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
    echo "  [OK] Dependencies installed successfully via pip."
fi

# Check model server variables are set
echo "  [INFO] Verifying configuration environment variables..."
if [ -z "${LLM_PROVIDER:-}" ] || [ -z "${HF_REPO:-}" ] || [ -z "${HF_FILE:-}" ]; then
    echo "  [WARNING] Some default model configuration environment variables are missing."
else
    echo "  [OK] Environment configurations verified: provider=${LLM_PROVIDER}, repo=${HF_REPO}, file=${HF_FILE}."
fi

echo ""
echo "  All dependencies satisfied."
echo "========================================================"
echo "  Next: bash scripts/llm_manage.sh"
echo "========================================================"
