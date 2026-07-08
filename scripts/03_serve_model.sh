#!/bin/bash
# ============================================================
# 03_serve_model.sh
# Starts llama-cpp-python server in the foreground.
# Press Ctrl+C at any time to stop the server.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT"
PID_FILE="$PROJECT_ROOT/.server.pid"

# Auto-load environment variables from .env if present
if [ -r "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

MODEL_FILE="${HF_FILE:-qwen2.5-coder-7b-instruct-q4_k_m.gguf}"
MODEL_PATH="$HOME/models/$MODEL_FILE"

HOST="${LLM_SERVER_HOST:-0.0.0.0}"
PORT="${LLM_SERVER_PORT:-1234}"
N_CTX="${LLM_SERVER_N_CTX:-8192}"
N_THREADS="${LLM_SERVER_N_THREADS:-8}"

echo "========================================================"
echo "  Step 3: Serve Local Model Server"
echo "========================================================"

mkdir -p "$LOG_DIR"

if [ ! -f "$MODEL_PATH" ]; then
    echo "  [INFO] Model file not found at: $MODEL_PATH"
    echo "  [INFO] Triggering automatic download..."
    bash "$SCRIPT_DIR/02_download_model.sh"
fi

if lsof -i :$PORT &>/dev/null; then
    echo "  [INFO] A process is already running on port $PORT."
    if curl -s "http://localhost:$PORT/v1/models" &>/dev/null; then
        echo "  [OK] Server is already active on port $PORT."
        exit 0
    else
        echo "ERROR: Port $PORT is occupied. Kill the occupying process first."
        exit 1
    fi
fi

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

cleanup() {
    if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo ""
        echo "  [INFO] Stopping model server (PID $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null || true
        rm -f "$PID_FILE"
        echo "  [OK] Model server stopped cleanly."
    fi
}
trap cleanup INT TERM

echo "  [INFO] Starting server on $HOST:$PORT using $PYTHON_CMD..."
echo "  Model: $MODEL_PATH"
echo "  Context: $N_CTX | Threads: $N_THREADS"
echo "  Log:   $LOG_DIR/model_server.log"
echo ""

"$PYTHON_CMD" -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --n_ctx "$N_CTX" \
    --n_threads "$N_THREADS" \
    > "$LOG_DIR/model_server.log" 2>&1 &

SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"
echo "  Server PID: $SERVER_PID"

echo -n "  Waiting for server to start"
for i in {1..30}; do
    if curl -s "http://localhost:$PORT/v1/models" &>/dev/null; then
        echo ""
        echo "  [OK] Server is ready and responsive!"
        echo "========================================================"
        echo "  Server is active on http://$HOST:$PORT/v1"
        echo "  Keep this terminal open while running experiments."
        echo "  Press Ctrl+C at any time to stop the server."
        echo "========================================================"
        wait "$SERVER_PID"
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
