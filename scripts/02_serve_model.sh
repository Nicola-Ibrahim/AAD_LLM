#!/bin/bash
# ============================================================
# 02_serve_model.sh
# Starts llama-server (llama.cpp) in the background to serve
# the Qwen model. Recommends running from the project root.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/server.pid"
PORT=1234

# Ensure local bin is in PATH
export PATH="$HOME/bin:$PATH"

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



MODEL_FILE=$(load_env_var "HF_FILE" "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf")
MODEL_PATH="$HOME/models/$MODEL_FILE"

echo "========================================================"
echo "  Step 2: Serve Local Model Server"
echo "========================================================"

mkdir -p "$LOG_DIR"

# 1. Check if model exists; if not, automatically download it
if [ ! -f "$MODEL_PATH" ]; then
    echo "  [INFO] Model file not found at: $MODEL_PATH"
    echo "  [INFO] Triggering automatic download..."
    bash "$SCRIPT_DIR/01_download_model.sh"
fi

# 2. Check if a server is already running on this port
if lsof -i :$PORT &>/dev/null; then
    echo "  [INFO] A process is already running on port $PORT."
    echo "  Checking if it is llama-server..."
    if curl -s http://localhost:$PORT/v1/models &>/dev/null; then
        echo "  [OK] An OpenAI-compatible API is already active on port $PORT."
        exit 0
    else
        echo "ERROR: Port $PORT is occupied by another application. Choose a different port or kill it."
        exit 1
    fi
fi

# 3. Start llama-server in the background
echo "  [INFO] Starting llama-server on port $PORT..."
echo "  Model: $MODEL_PATH"
echo "  Log:   $LOG_DIR/model_server.log"
echo ""

# Start the server with standard context size of 8192 for LLaMEA optimization
# --threads auto will use available CPU cores
nohup llama-server \
    -m "$MODEL_PATH" \
    --port "$PORT" \
    -c 8192 \
    --threads 8 \
    > "$LOG_DIR/model_server.log" 2>&1 &

SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"
echo "  Server PID: $SERVER_PID"
echo "  PID saved to: $PID_FILE"

# 4. Wait for server to become responsive
echo -n "  Waiting for server to start"
for i in {1..30}; do
    if curl -s http://localhost:$PORT/v1/models &>/dev/null; then
        echo ""
        echo "  [OK] Server is ready and responsive!"
        curl -s http://localhost:$PORT/v1/models | grep -o '"id":[^,]*' || true
        echo "========================================================"
        echo "  Server is active on http://localhost:$PORT/v1"
        echo "  Next: Run 'uv run aad-llm' or execute Jupyter notebooks"
        echo "========================================================"
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo "WARNING: Server did not respond within 60 seconds. Check logs at:"
echo "  $LOG_DIR/model_server.log"
echo "========================================================"
exit 1
