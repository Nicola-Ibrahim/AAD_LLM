#!/bin/bash
# ============================================================
# llm_server.sh
# Management CLI for local llama-cpp-python model server.
#
# Usage:
#   bash scripts/llm_server.sh [command]
#
# Commands:
#   start            Start the server in the background (default)
#   stop             Stop the running server cleanly
#   restart          Stop and restart the server
#   status           Check server status and query responsiveness
#   exit             Exit the CLI
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/server.pid"
LOG_FILE="$LOG_DIR/model_server.log"

# ─── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Load Environment ──────────────────────────────────────
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

# Function to load variable from .env or env
load_env_var() {
    local var_name=$1
    local default_val=${2:-""}
    if [ -n "${!var_name:-}" ]; then
        echo "${!var_name}"
    else
        echo "$default_val"
    fi
}

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║           Local LLM Server Manager           ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

# ─── Parse CLI Command ─────────────────────────────────────
COMMAND=""
if [[ $# -gt 0 ]]; then
    case "$1" in
        start|stop|restart|status)
            COMMAND="$1"
            shift
            ;;
    esac
fi

# ─── Interactive Menu (if no command given) ────────────────
if [[ -z "$COMMAND" ]]; then
    if [[ -t 0 ]]; then
        print_header
        echo "  Select an operation:"
        echo ""
        options=(
            "Start LLM Server         (start)"
            "Stop LLM Server          (stop)"
            "Restart LLM Server       (restart)"
            "Check Server Status      (status)"
            "Exit"
        )
        COLUMNS=1
        select opt in "${options[@]}"; do
            if [[ -z "$opt" && -z "$REPLY" ]]; then
                echo "No selection made. Exiting."
                exit 0
            fi
            case $REPLY in
                1) COMMAND="start";   break ;;
                2) COMMAND="stop";    break ;;
                3) COMMAND="restart"; break ;;
                4) COMMAND="status";  break ;;
                5) echo "Exiting."; exit 0 ;;
                *) echo -e "  ${RED}Invalid option. Please choose 1–5.${NC}" ;;
            esac
        done
    else
        # Non-interactive: default to start
        COMMAND="start"
    fi
fi

# ─── Locate Python ─────────────────────────────────────────
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
fi

# ─── Stop Logic ────────────────────────────────────────────
stop_server() {
    local stopped=0
    
    # 1. Stop process from PID file
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -e "  ${CYAN}[i] Stopping server from PID file (PID $pid)...${NC}"
            kill "$pid" 2>/dev/null || true
            stopped=1
        fi
        rm -f "$PID_FILE"
    fi

    # 2. Check pgrep for llama_cpp.server
    local pids
    pids=$(pgrep -f "llama_cpp.server" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "  ${CYAN}[i] Stopping other active model server processes (PIDs: $pids)...${NC}"
        kill $pids 2>/dev/null || true
        stopped=1
    fi

    # 3. Check port via lsof
    if command -v lsof &>/dev/null; then
        local port_pid
        port_pid=$(lsof -t -i :"$PORT" 2>/dev/null || true)
        if [ -n "$port_pid" ]; then
            echo -e "  ${CYAN}[i] Stopping process holding port $PORT (PID $port_pid)...${NC}"
            kill "$port_pid" 2>/dev/null || true
            stopped=1
        fi
    fi

    if [ "$stopped" -eq 1 ]; then
        echo -e "  ${GREEN}✓ Model server stopped cleanly.${NC}"
    else
        echo -e "  ${GREEN}✓ No active model server found running.${NC}"
    fi
}

# ─── Start Logic ───────────────────────────────────────────
start_server() {
    mkdir -p "$LOG_DIR"

    # Download model if missing
    if [ ! -f "$MODEL_PATH" ]; then
        echo -e "  ${YELLOW}! Model file not found at: $MODEL_PATH${NC}"
        echo -e "  ${CYAN}[i] Triggering automatic download...${NC}"
        bash "$SCRIPT_DIR/llm_manage.sh" download
    fi

    # Check port conflict
    if lsof -i :$PORT &>/dev/null; then
        echo -e "  ${CYAN}[i] Checking port $PORT occupancy...${NC}"
        if curl -s "http://localhost:$PORT/v1/models" &>/dev/null; then
            echo -e "  ${GREEN}✓ Server is already active and responsive on port $PORT.${NC}"
            echo -e "  No need to launch a new instance."
            echo ""
            return 0
        else
            echo -e "  ${RED}✗ ERROR: Port $PORT is occupied by another process.${NC}"
            echo -e "  Please stop the occupying process first before starting the server."
            echo ""
            exit 1
        fi
    fi

    echo -e "  ${CYAN}[i] Starting llama-cpp-python server...${NC}"
    echo -e "    ${BOLD}Host:${NC}       $HOST"
    echo -e "    ${BOLD}Port:${NC}       $PORT"
    echo -e "    ${BOLD}Model:${NC}      $MODEL_PATH"
    echo -e "    ${BOLD}Context:${NC}    $N_CTX tokens"
    echo -e "    ${BOLD}Threads:${NC}    $N_THREADS"
    echo -e "    ${BOLD}Log File:${NC}   $LOG_FILE"
    echo ""

    # Launch server in background
    "$PYTHON_CMD" -m llama_cpp.server \
        --model "$MODEL_PATH" \
        --host "$HOST" \
        --port "$PORT" \
        --n_ctx "$N_CTX" \
        --n_threads "$N_THREADS" \
        > "$LOG_FILE" 2>&1 &

    local server_pid=$!
    echo "$server_pid" > "$PID_FILE"
    echo -e "  ${CYAN}[i] Spawned background process with PID: $server_pid${NC}"
    echo -ne "  ${CYAN}[i] Waiting for server to become responsive...${NC} "

    # Wait loop
    for i in {1..30}; do
        if curl -s "http://localhost:$PORT/v1/models" &>/dev/null; then
            echo ""
            echo ""
            echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
            echo -e "  ${GREEN}✓ Server is ready and responsive!${NC}"
            echo -e "  ${BOLD}API Endpoint:${NC} http://$HOST:$PORT/v1"
            echo -e "  Press ${YELLOW}Ctrl+C${NC} in this shell to view logs, or stop it later using:"
            echo -e "  ${BOLD}bash scripts/llm_server.sh stop${NC}"
            echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
            echo ""
            
            # Follow logs in the foreground so the user sees progress and can Ctrl+C
            # Trap Ctrl+C to run cleanup (stop) cleanly
            trap stop_server INT TERM
            tail -f "$LOG_FILE" &
            local tail_pid=$!
            wait "$server_pid" 2>/dev/null || true
            kill "$tail_pid" 2>/dev/null || true
            return 0
        fi
        echo -n "•"
        sleep 2
    done

    echo ""
    echo -e "  ${RED}✗ WARNING: Server did not respond within 60 seconds.${NC}"
    echo -e "  Please inspect the log file for initialization errors:"
    echo -e "    ${BOLD}Log path:${NC} $LOG_FILE"
    echo ""
    exit 1
}

# ─── Execute ───────────────────────────────────────────────
case "$COMMAND" in
    start)
        start_server
        ;;
    stop)
        print_header
        stop_server
        ;;
    restart)
        print_header
        echo -e "  ${CYAN}[i] Restarting LLM Server...${NC}"
        stop_server
        echo ""
        start_server
        ;;
    status)
        print_header
        echo -e "  ${BOLD}Configured Settings:${NC}"
        echo -e "    ${BOLD}Host:${NC}       $HOST"
        echo -e "    ${BOLD}Port:${NC}       $PORT"
        echo -e "    ${BOLD}Model:${NC}      $MODEL_PATH"
        echo ""
        echo -e "  ${BOLD}Running Process Info:${NC}"
        
        active=0
        if [ -f "$PID_FILE" ]; then
            pid=""
            pid=$(cat "$PID_FILE")
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                echo -e "    ${GREEN}● Active (PID: $pid from server.pid)${NC}"
                active=1
            fi
        fi

        # Check pgrep if pid file was not active
        if [ "$active" -eq 0 ]; then
            pids=""
            pids=$(pgrep -f "llama_cpp.server" 2>/dev/null || true)
            if [ -n "$pids" ]; then
                echo -e "    ${GREEN}● Active (PIDs: $pids detected via pgrep)${NC}"
                active=1
            fi
        fi

        if [ "$active" -eq 0 ]; then
            echo -e "    ${RED}○ Inactive (No server processes detected)${NC}"
        fi

        echo ""
        echo -e "  ${BOLD}API Responsiveness:${NC}"
        if curl -s --max-time 3 "http://localhost:$PORT/v1/models" &>/dev/null; then
            echo -e "    ${GREEN}✓ Responsive on http://localhost:$PORT/v1${NC}"
        else
            echo -e "    ${RED}✗ Unresponsive or port closed on http://localhost:$PORT/v1${NC}"
        fi
        echo ""
        ;;
    *)
        echo -e "  ${RED}Unknown command: '$COMMAND'${NC}"
        echo "  Valid commands: start, stop, restart, status"
        exit 1
        ;;
esac
