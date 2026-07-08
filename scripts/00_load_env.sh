#!/bin/bash
# ============================================================
# 00_load_env.sh
# Explicitly exports all project environment variables in Bash.
# Works in JupyterHub terminal and remote servers without needing
# to open or read a .env file on disk.
#
# Usage:
#   source scripts/00_load_env.sh
# ============================================================

# Warn if executed directly in a subshell instead of sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "========================================================"
    echo "WARNING: Running script directly in a subshell."
    echo "To export variables to your active terminal session, run:"
    echo ""
    echo "  source scripts/00_load_env.sh"
    echo "========================================================"
    echo ""
fi

# 1. Local LLaMA Server Configuration
export LLM_PROVIDER="local"
export HF_REPO="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
export HF_FILE="qwen2.5-coder-7b-instruct-q4_k_m.gguf"
export LOCAL_LLM_MODEL="qwen2.5-coder-7b-instruct-q4_k_m"
export LOCAL_LLM_BASE_URL="http://localhost:1234/v1"
export LOCAL_LLM_API_KEY="not-needed"

# 2. Server Runtime Configuration
export LLM_SERVER_HOST="0.0.0.0"
export LLM_SERVER_PORT="1234"
export LLM_SERVER_N_CTX="8192"
export LLM_SERVER_N_THREADS="8"

# 3. Optionally override from .env file if readable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo ".")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." 2>/dev/null && pwd || echo ".")"
ENV_FILE="$PROJECT_ROOT/.env"

if [ -r "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE" 2>/dev/null || true
    set +a
fi
