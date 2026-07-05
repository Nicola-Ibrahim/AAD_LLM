#!/bin/bash
# ============================================================
# stop_server.sh
# Stops the local model server process cleanly.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_ROOT/logs/server.pid"

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

PORT=$(load_env_var "LLM_SERVER_PORT" "1234")

STOPPED=0

# 1. Stop process recorded in PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Stopping model server from PID file (PID $PID)..."
        kill "$PID" 2>/dev/null || true
        STOPPED=1
    fi
    rm -f "$PID_FILE"
fi

# 2. Check via pgrep for llama_cpp.server
PIDS=$(pgrep -f "llama_cpp.server" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "Stopping model server processes (PID $PIDS)..."
    kill $PIDS 2>/dev/null || true
    STOPPED=1
fi

# 3. Check via lsof if installed
if command -v lsof &>/dev/null; then
    PORT_PID=$(lsof -t -i :"$PORT" 2>/dev/null || true)
    if [ -n "$PORT_PID" ]; then
        echo "Stopping process on port $PORT (PID $PORT_PID)..."
        kill "$PORT_PID" 2>/dev/null || true
        STOPPED=1
    fi
fi

if [ "$STOPPED" -eq 1 ]; then
    echo "[OK] Model server stopped successfully."
else
    echo "[INFO] No running model server found."
fi
