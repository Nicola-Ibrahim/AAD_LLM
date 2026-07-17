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
        start|stop|status)
            COMMAND="$1"
            shift
            ;;
    esac
fi

# ─── Interactive Menu (if no command given) ────────────────
if [[ -z "$COMMAND" ]]; then
    if [[ -t 0 ]]; then
        while true; do
            print_header
            echo -e "  ${BOLD}Select an operation:${NC}"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo -e "    ${BOLD}1)${NC} Start LLM Server         (start)"
            echo -e "    ${BOLD}2)${NC} Stop LLM Server          (stop)"
            echo -e "    ${BOLD}3)${NC} Check Server Status      (status)"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo ""
            echo -e "  ${BOLD}Options:${NC}"
            echo -e "    - Type the number of the option to execute (e.g. ${CYAN}'1'${NC})."
            echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to exit."
            echo ""

            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice
            choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

            if [ -z "$choice" ] || [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
                echo -e "  ${YELLOW}Exiting.${NC}"
                exit 0
            fi

            case "$choice" in
                1) COMMAND="start";   break ;;
                2) COMMAND="stop";    break ;;
                3) COMMAND="status";  break ;;
                *)
                    echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and 3.${NC}"
                    echo ""
                    sleep 1
                    ;;
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

    # 1. Scan TARGET_DIR (~/models) for GGUF files
    local TARGET_DIR="$HOME/models"
    LOCAL_MODELS=()
    LOCAL_PATHS=()
    LOCAL_SIZES=()
    if [ -d "$TARGET_DIR" ]; then
        while IFS= read -r item; do
            [ -z "$item" ] && continue
            LOCAL_PATHS+=("$item")
            LOCAL_MODELS+=("$(basename "$item")")
            LOCAL_SIZES+=("$(du -sh "$item" 2>/dev/null | cut -f1)")
        done < <(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -name "*.gguf" 2>/dev/null || true)
    fi

    local total_count=${#LOCAL_MODELS[@]}
    local selected_model=""

    # Resolve selected model: HF_FILE env var, interactive select, first model, or fallback default
    if [ -n "${HF_FILE:-}" ]; then
        selected_model="$HF_FILE"
    elif [[ -t 0 ]] && [ "$total_count" -gt 0 ]; then
        print_header
        echo -e "  ${CYAN}[i] Found $total_count model(s) in cache:${NC}"
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        for i in "${!LOCAL_MODELS[@]}"; do
            num=$((i + 1))
            printf "    ${BOLD}%2d)${NC} %-52s [${YELLOW}%s${NC}]\n" "$num" "${LOCAL_MODELS[$i]}" "${LOCAL_SIZES[$i]}"
            echo -e "        ${BOLD}Path:${NC} ${LOCAL_PATHS[$i]}"
        done
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        echo ""
        echo -e "  ${BOLD}Options:${NC}"
        echo -e "    - Type the number of the model to serve (e.g. ${CYAN}'1'${NC})."
        echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to cancel."
        echo ""
        
        while true; do
            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice
            choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)
            
            if [ -z "$choice" ] || [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
                echo -e "  ${YELLOW}Cancelled. No model was started.${NC}"
                echo ""
                exit 0
            fi
            
            if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$total_count" ]; then
                selected_model="${LOCAL_MODELS[$((choice - 1))]}"
                break
            else
                echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and $total_count.${NC}"
            fi
        done
    else
        echo -e "  ${RED}✗ ERROR: No active LLM model selected or available.${NC}"
        echo -e "  Please download a model to $TARGET_DIR first."
        exit 1
    fi

    MODEL_PATH="$TARGET_DIR/$selected_model"

    if [ ! -f "$MODEL_PATH" ]; then
        echo -e "  ${RED}✗ ERROR: Model file not found at: $MODEL_PATH${NC}"
        exit 1
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
    status)
        print_header
        echo -e "  ${BOLD}Configured Settings:${NC}"
        echo -e "    ${BOLD}Host:${NC}       $HOST"
        echo -e "    ${BOLD}Port:${NC}       $PORT"
        
        # Query active model from running server
        active_model=$(curl -s "http://localhost:$PORT/v1/models" | "$PYTHON_CMD" -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['data'][0]['id'])
except:
    print('(none/server offline)')
" 2>/dev/null || echo "(none/server offline)")
        
        echo -e "    ${BOLD}Active Model:${NC} $active_model"
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
        echo "  Valid commands: start, stop, status"
        exit 1
        ;;
esac
