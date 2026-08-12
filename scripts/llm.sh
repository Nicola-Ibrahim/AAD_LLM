#!/bin/bash
# ============================================================
# llm.sh
# Management CLI for local LLM model serving, downloading, and cache management.
#
# Usage:
#   bash scripts/llm.sh [command]
#
# Commands:
#   start            Start the server in the background (default in non-interactive)
#   stop             Stop the running server cleanly
#   status           Check server status and query responsiveness
#   download         Select and download GGUF models from Hugging Face
#   list             List all downloaded models and their cache sizes
#   cleanup          Interactively scan and delete downloaded models
#   exit             Exit the CLI
# ============================================================

set -euo pipefail
export PYTHONWARNINGS="ignore"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/server.pid"
LOG_FILE="$LOG_DIR/model_server.log"
TARGET_DIR="$HOME/models"
HF_CACHE_DIR="$HOME/.cache/huggingface/hub"

# Clean signal handling for interrupts (Ctrl+C)
trap 'echo -e "\n  \033[1;33mExiting.\033[0m"; exit 0' INT

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
N_GPU_LAYERS="${LLM_SERVER_N_GPU_LAYERS:-0}"
VERBOSE="${LLM_SERVER_VERBOSE:-False}"

MODEL_REPO="${MODEL_REPO:-}"
MODEL_FILE="${MODEL_FILE:-}"

# ─── Locate Python ─────────────────────────────────────────
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
fi

PRESETS_PY="$SCRIPT_DIR/utils/llm_presets.py"

# ─── Helpers ───────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║        LLM Server & Model Manager            ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

format_kb() {
    local kb=$1
    "$PYTHON_CMD" -c "
kb = float('$kb')
if kb >= 1048576:
    print(f'{kb/1048576:.2f} GB')
elif kb >= 1024:
    print(f'{kb/1024:.2f} MB')
else:
    print(f'{kb} KB')
" 2>/dev/null || echo "${kb} KB"
}

show_pid_stats() {
    local pid=$1
    if kill -0 "$pid" 2>/dev/null; then
        local cpu="" mem="" rss="" vsz="" elapsed="" started=""
        read -r cpu mem rss vsz < <(ps -p "$pid" -o %cpu=,%mem=,rss=,vsz= 2>/dev/null || true)
        read -r elapsed started < <(ps -p "$pid" -o etime=,lstart= 2>/dev/null || true)
        
        if [ -n "$rss" ]; then
            local rss_formatted
            rss_formatted=$(format_kb "$rss")
            local vsz_formatted
            vsz_formatted=$(format_kb "$vsz")
            
            echo -e "      ${BOLD}CPU Usage:${NC}        $cpu%"
            echo -e "      ${BOLD}System RAM (RSS):${NC} $rss_formatted ($mem% of system total)"
            echo -e "      ${BOLD}Virtual Mem:${NC}      $vsz_formatted"

            if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
                local gpu_mem
                gpu_mem=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null | grep "^[[:space:]]*$pid," | cut -d',' -f2 | xargs || true)
                if [ -n "$gpu_mem" ]; then
                    echo -e "      ${BOLD}GPU Memory:${NC}       $gpu_mem"
                else
                    echo -e "      ${BOLD}GPU Memory:${NC}       0 MiB (Not running on GPU)"
                fi
            elif [ "$(uname -s)" = "Darwin" ]; then
                echo -e "      ${BOLD}GPU Memory:${NC}       (Shared/Unified Memory on macOS)"
            fi

            echo -e "      ${BOLD}Start Time:${NC}       $started"
            echo -e "      ${BOLD}Uptime:${NC}           $elapsed"
        fi

        if [ -f "$LOG_FILE" ]; then
            local offloaded_layers
            offloaded_layers=$(grep -i "offloaded" "$LOG_FILE" | tail -n 1 | sed -E 's/.*offloaded (.*)/\1/' || true)
            if [ -n "$offloaded_layers" ]; then
                echo -e "      ${BOLD}GPU Offloading:${NC}   $offloaded_layers"
            fi
            
            local ctx_size
            ctx_size=$(grep -E -i "n_ctx|context" "$LOG_FILE" | head -n 5 | grep -E -o "n_ctx[[:space:]]*=[[:space:]]*[0-9]+" | tail -n 1 | sed -E 's/n_ctx[[:space:]]*=[[:space:]]*//' || true)
            if [ -n "$ctx_size" ]; then
                echo -e "      ${BOLD}Model Context:${NC}    $ctx_size tokens"
            fi
        fi
    fi
}

# ─── Parse CLI Command ─────────────────────────────────────
COMMAND=""
if [[ $# -gt 0 ]]; then
    case "$1" in
        start|stop|status|download|cleanup|list)
            COMMAND="$1"
            shift
            ;;
    esac
fi

# ─── Top-Level Interactive Menu (if no command given) ─────
if [[ -z "$COMMAND" ]]; then
    if [[ -t 0 ]]; then
        while true; do
            print_header
            echo -e "  ${CYAN}${BOLD}Active Configuration Settings:${NC}"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo -e "    • ${BOLD}API Endpoint:${NC}  http://$HOST:$PORT/v1"
            echo -e "    • ${BOLD}Context Size:${NC}  $N_CTX tokens"
            echo -e "    • ${BOLD}CPU Threads:${NC}   $N_THREADS"
            echo -e "    • ${BOLD}GPU Offload:${NC}   $N_GPU_LAYERS layers (-1 = auto, 0 = CPU only)"
            echo -e "    • ${BOLD}Log File:${NC}      $LOG_FILE"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo -e "    ${YELLOW}Tip: Customize these settings in your .env file.${NC}"
            echo ""
            echo -e "  ${BOLD}Select an operation:${NC}"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo -e "    ${BOLD}1)${NC} Start LLM Server         (start)"
            echo -e "    ${BOLD}2)${NC} Stop LLM Server          (stop)"
            echo -e "    ${BOLD}3)${NC} Check Server Status      (status)"
            echo -e "    ${BOLD}4)${NC} Download LLM Model       (download)"
            echo -e "    ${BOLD}5)${NC} List Cached Models       (list)"
            echo -e "    ${BOLD}6)${NC} Delete Cached Models     (cleanup)"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo ""
            echo -e "  ${BOLD}Options:${NC}"
            echo -e "    - Type the number of the option to execute (e.g. ${CYAN}'1'${NC})."
            echo -e "    - Press ${YELLOW}Enter${NC}, type ${YELLOW}'q'${NC}, or press ${YELLOW}Ctrl+C${NC} to exit."
            echo ""

            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice || { echo -e "\n  ${YELLOW}Exiting.${NC}"; exit 0; }
            choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

            if [ -z "$choice" ] || [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
                echo -e "  ${YELLOW}Exiting.${NC}"
                exit 0
            fi

            case "$choice" in
                1) COMMAND="start";    break ;;
                2) COMMAND="stop";     break ;;
                3) COMMAND="status";   break ;;
                4) COMMAND="download"; break ;;
                5) COMMAND="list";     break ;;
                6) COMMAND="cleanup";  break ;;
                *)
                    echo -e "  ${RED}✗ ERROR: Invalid choice '$choice'. Please choose a number between 1 and 6.${NC}"
                    sleep 1.5
                    ;;
            esac
        done
    else
        COMMAND="start"
    fi
fi

# ─── Stop Logic ────────────────────────────────────────────
stop_server() {
    local stopped=0
    
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

    local pids
    pids=$(pgrep -f "llama_cpp.server" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo -e "  ${CYAN}[i] Stopping other active model server processes (PIDs: $pids)...${NC}"
        kill $pids 2>/dev/null || true
        stopped=1
    fi

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

    if [ "${N_GPU_LAYERS:-0}" -eq 0 ] && [ -z "${LLM_SERVER_N_GPU_LAYERS:-}" ]; then
        local os_type
        os_type="$(uname -s 2>/dev/null || echo 'Unknown')"
        if [ "$os_type" = "Darwin" ]; then
            echo -e "  ${CYAN}[i] macOS detected. Automatically enabling GPU offloading.${NC}"
            N_GPU_LAYERS=-1
            N_THREADS=2
        elif [ "$os_type" = "Linux" ] && command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
            echo -e "  ${CYAN}[i] Nvidia GPU detected. Automatically enabling CUDA offloading.${NC}"
            N_GPU_LAYERS=-1
            N_THREADS=2
        else
            echo -e "  ${YELLOW}[i] No GPU detected/supported for auto-offload. Defaulting to CPU.${NC}"
            N_GPU_LAYERS=0
        fi
    fi

    MODELS_JSON=$("$PYTHON_CMD" "$PRESETS_PY" scan-models --target-dir "$TARGET_DIR" --hf-cache-dir "$HF_CACHE_DIR" --gguf-only --format json)
    local total_count
    total_count=$("$PYTHON_CMD" -c "import json; print(len(json.loads('''$MODELS_JSON''')))")
    local selected_model=""
    local selected_path=""

    if [[ -t 0 ]]; then
        if [ "$total_count" -gt 0 ]; then
            while true; do
                print_header
                echo -e "  ${CYAN}[i] Available LLM Models (sorted by parameter size):${NC}"
                "$PYTHON_CMD" "$PRESETS_PY" scan-models --target-dir "$TARGET_DIR" --hf-cache-dir "$HF_CACHE_DIR" --gguf-only --format card
                
                echo -e "  ${BOLD}Options:${NC}"
                echo -e "    - Type the number of the model to serve (e.g. ${CYAN}'1'${NC})."
                echo -e "    - Press ${YELLOW}Enter${NC}, type ${YELLOW}'q'${NC}, or press ${YELLOW}Ctrl+C${NC} to cancel."
                echo ""
                
                read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice || { echo -e "\n  ${YELLOW}Cancelled. No model was started.${NC}"; exit 0; }
                choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)
                
                if [ -z "$choice" ] || [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
                    echo -e "  ${YELLOW}Cancelled. No model was started.${NC}"
                    echo ""
                    exit 0
                fi
                
                if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "$total_count" ]; then
                    selected_model=$("$PYTHON_CMD" -c "import json; print(json.loads('''$MODELS_JSON''')[$((choice - 1))]['name'])")
                    selected_path=$("$PYTHON_CMD" -c "import json; print(json.loads('''$MODELS_JSON''')[$((choice - 1))]['path'])")
                    break
                else
                    echo -e "  ${RED}✗ ERROR: Invalid choice '$choice'. Please choose a number between 1 and $total_count.${NC}"
                    sleep 1.5
                fi
            done
        else
            echo -e "  ${RED}✗ ERROR: No GGUF model files found.${NC}"
            echo -e "  Scanned locations:"
            echo -e "    • ${BOLD}$TARGET_DIR${NC}"
            echo -e "    • ${BOLD}$HF_CACHE_DIR${NC}"
            echo -e ""
            echo -e "  Please download a model first using scripts/llm.sh download."
            exit 1
        fi
    else
        if [ -n "${HF_FILE:-}" ]; then
            selected_model="$HF_FILE"
            selected_path="$TARGET_DIR/$selected_model"
        elif [ "$total_count" -gt 0 ]; then
            selected_model=$("$PYTHON_CMD" -c "import json; print(json.loads('''$MODELS_JSON''')[0]['name'])")
            selected_path=$("$PYTHON_CMD" -c "import json; print(json.loads('''$MODELS_JSON''')[0]['path'])")
            echo -e "  ${CYAN}[i] Non-interactive mode: Automatically selecting first available model: $selected_model${NC}"
        else
            echo -e "  ${RED}✗ ERROR: No GGUF model files found and no model specified in non-interactive mode.${NC}"
            echo -e "  Scanned locations:"
            echo -e "    • ${BOLD}$TARGET_DIR${NC}"
            echo -e "    • ${BOLD}$HF_CACHE_DIR${NC}"
            exit 1
        fi
    fi

    MODEL_PATH="$selected_path"

    if [ ! -f "$MODEL_PATH" ]; then
        echo -e "  ${RED}✗ ERROR: Model file not found at: $MODEL_PATH${NC}"
        exit 1
    fi

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
    echo -e "    ${BOLD}GPU Layers:${NC} $N_GPU_LAYERS"
    echo -e "    ${BOLD}Verbose:${NC}    $VERBOSE"
    echo -e "    ${BOLD}Log File:${NC}   $LOG_FILE"
    echo ""

    if [ "${N_GPU_LAYERS:-0}" -ne 0 ]; then
        echo -e "  ${CYAN}[i] Resolving CUDA runtime dependencies...${NC}"
        
        local found_in_venv=0
        local site_packages_nvidia
        site_packages_nvidia=$(find "$PROJECT_ROOT/.venv" -path "*/site-packages/nvidia" -type d -print -quit 2>/dev/null || true)
        
        if [ -n "$site_packages_nvidia" ]; then
            local nvidia_libs=""
            for lib_dir in "$site_packages_nvidia"/*/lib; do
                if [ -d "$lib_dir" ]; then
                    nvidia_libs="$lib_dir:$nvidia_libs"
                fi
            done
            if [ -n "$nvidia_libs" ]; then
                echo -e "    ${GREEN}● Found NVIDIA CUDA/cuBLAS libraries in virtual env:${NC} $site_packages_nvidia"
                export LD_LIBRARY_PATH="${nvidia_libs}${LD_LIBRARY_PATH:-}"
                found_in_venv=1
            fi
        fi
        
        if [ "$found_in_venv" -eq 0 ]; then
            local system_found=0
            for path in "/usr/local/cuda/lib64" "/usr/local/cuda/targets/x86_64-linux/lib" "/usr/lib/x86_64-linux-gnu" "/usr/lib64"; do
                if [ -f "$path/libcudart.so.12" ]; then
                    echo -e "    ${GREEN}● Found system CUDA runtime:${NC} $path"
                    export LD_LIBRARY_PATH="$path:${LD_LIBRARY_PATH:-}"
                    system_found=1
                    break
                fi
            done
            if [ "$system_found" -eq 0 ]; then
                echo -e "    ${YELLOW}[!] WARNING: libcudart.so.12 not found in system or virtual env. GPU server launch might fail.${NC}"
            fi
        fi
    fi

    "$PYTHON_CMD" -m llama_cpp.server \
        --model "$MODEL_PATH" \
        --host "$HOST" \
        --port "$PORT" \
        --n_ctx "$N_CTX" \
        --n_threads "$N_THREADS" \
        --n_gpu_layers "$N_GPU_LAYERS" \
        --verbose "$VERBOSE" \
        > "$LOG_FILE" 2>&1 &

    local server_pid=$!
    echo "$server_pid" > "$PID_FILE"
    echo -e "  ${CYAN}[i] Spawned background process with PID: $server_pid${NC}"
    echo -ne "  ${CYAN}[i] Waiting for server to become responsive...${NC} "

    for i in {1..30}; do
        if curl -s "http://localhost:$PORT/v1/models" &>/dev/null; then
            echo ""
            echo ""
            echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
            echo -e "  ${GREEN}✓ Server is ready and responsive!${NC}"
            echo -e "  ${BOLD}API Endpoint:${NC} http://$HOST:$PORT/v1"
            echo -e "  Press ${YELLOW}Ctrl+C${NC} in this shell to view logs, or stop it later using:"
            echo -e "  ${BOLD}bash scripts/llm.sh stop${NC}"
            echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
            echo ""
            
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

# ─── Download Logic ────────────────────────────────────────
download_model() {
    if [[ -z "$MODEL_REPO" || -z "$MODEL_FILE" ]]; then
        if [[ -t 0 ]]; then
            while true; do
                print_header
                echo -e "  ${BOLD}Select download method:${NC}"
                echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
                echo -e "    ${BOLD}1)${NC} Select and download a model preset"
                echo -e "    ${BOLD}2)${NC} Download from custom Hugging Face repo & file"
                echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
                echo ""
                echo -e "  ${BOLD}Options:${NC}"
                echo -e "    - Type the number of the option (e.g. ${CYAN}'1'${NC})."
                echo -e "    - Press ${YELLOW}Enter${NC}, type ${YELLOW}'q'${NC}, or press ${YELLOW}Ctrl+C${NC} to cancel."
                echo ""
                
                read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" dl_choice || { echo -e "\n  ${YELLOW}Cancelled.${NC}"; exit 0; }
                dl_choice=$(echo "$dl_choice" | tr '[:upper:]' '[:lower:]' | xargs)
                
                if [ -z "$dl_choice" ] || [ "$dl_choice" = "q" ] || [ "$dl_choice" = "quit" ] || [ "$dl_choice" = "exit" ]; then
                    echo -e "  ${YELLOW}Cancelled.${NC}"
                    exit 0
                fi
                
                case "$dl_choice" in
                    1)
                        TOML_FILE="$PROJECT_ROOT/configs/llms.toml"

                        while true; do
                            CATEGORIES_JSON=$("$PYTHON_CMD" "$PRESETS_PY" list-categories --toml "$TOML_FILE")
                            CAT_COUNT=$("$PYTHON_CMD" -c "import json; print(len(json.loads('''$CATEGORIES_JSON''')))")
                            if [ "$CAT_COUNT" -eq 0 ]; then
                                echo -e "  ${RED}✗ ERROR: No model categories found in: $TOML_FILE${NC}"
                                exit 1
                            fi

                            print_header
                            echo -e "  ${BOLD}Select a model family/category:${NC}"
                            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
                            for ((i=0; i<CAT_COUNT; i++)); do
                                cat_name=$("$PYTHON_CMD" -c "import json; print(json.loads('''$CATEGORIES_JSON''')[$i]['name'])")
                                cat_desc=$("$PYTHON_CMD" -c "import json; print(json.loads('''$CATEGORIES_JSON''')[$i]['description'])")
                                printf "    ${BOLD}%2d)${NC} %-25s - %s\n" "$((i + 1))" "$cat_name" "$cat_desc"
                            done
                            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
                            echo ""
                            echo -e "  ${BOLD}Options:${NC}"
                            echo -e "    - Type the number of the family (e.g. ${CYAN}'1'${NC})."
                            echo -e "    - Press ${YELLOW}Enter${NC}, type ${YELLOW}'q'${NC}, or press ${YELLOW}Ctrl+C${NC} to cancel."
                            echo ""

                            SELECTED_CAT=""
                            while true; do
                                read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" cat_choice || { echo -e "\n  ${YELLOW}Cancelled.${NC}"; exit 0; }
                                cat_choice=$(echo "$cat_choice" | tr '[:upper:]' '[:lower:]' | xargs)
                                
                                if [ -z "$cat_choice" ] || [ "$cat_choice" = "q" ] || [ "$cat_choice" = "quit" ] || [ "$cat_choice" = "exit" ]; then
                                    echo -e "  ${YELLOW}Cancelled.${NC}"
                                    exit 0
                                fi
                                
                                if [[ "$cat_choice" =~ ^[0-9]+$ ]] && [ "$cat_choice" -ge 1 ] && [ "$cat_choice" -le "$CAT_COUNT" ]; then
                                    SELECTED_CAT=$("$PYTHON_CMD" -c "import json; print(json.loads('''$CATEGORIES_JSON''')[$((cat_choice - 1))]['name'])")
                                    break
                                else
                                    echo -e "  ${RED}✗ ERROR: Invalid choice '$cat_choice'. Please choose a number between 1 and $CAT_COUNT.${NC}"
                                    sleep 1.5
                                fi
                            done

                            FILTERED_MODELS=$("$PYTHON_CMD" "$PRESETS_PY" list-models --category "$SELECTED_CAT" --toml "$TOML_FILE")
                            MODEL_COUNT=$("$PYTHON_CMD" -c "import json; print(len(json.loads('''$FILTERED_MODELS''')))")

                            print_header
                            echo -e "  ${BOLD}Select a model from family '$SELECTED_CAT' to download:${NC}"
                            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
                            for ((i=0; i<MODEL_COUNT; i++)); do
                                name=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$i]; print(m.get('name', ''))")
                                desc=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$i]; print(m.get('description', ''))")
                                printf "    ${BOLD}%2d)${NC} %-35s - %s\n" "$((i + 1))" "$name" "$desc"
                            done
                            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
                            echo ""
                            echo -e "  ${BOLD}Options:${NC}"
                            echo -e "    - Type the number of the model to download."
                            echo -e "    - Type ${YELLOW}'b'${NC} (or ${YELLOW}'back'${NC}) to return to the family list."
                            echo -e "    - Press ${YELLOW}Enter${NC}, type ${YELLOW}'q'${NC}, or press ${YELLOW}Ctrl+C${NC} to cancel."
                            echo ""

                            CHOSEN_MODEL_INDEX=""
                            GO_BACK=false
                            while true; do
                                read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" preset_choice || { echo -e "\n  ${YELLOW}Cancelled.${NC}"; exit 0; }
                                preset_choice=$(echo "$preset_choice" | tr '[:upper:]' '[:lower:]' | xargs)
                                
                                if [ -z "$preset_choice" ] || [ "$preset_choice" = "q" ] || [ "$preset_choice" = "quit" ] || [ "$preset_choice" = "exit" ]; then
                                    echo -e "  ${YELLOW}Cancelled.${NC}"
                                    exit 0
                                fi
                                
                                if [ "$preset_choice" = "back" ] || [ "$preset_choice" = "b" ]; then
                                    GO_BACK=true
                                    break
                                fi
                                
                                if [[ "$preset_choice" =~ ^[0-9]+$ ]] && [ "$preset_choice" -ge 1 ] && [ "$preset_choice" -le "$MODEL_COUNT" ]; then
                                    CHOSEN_MODEL_INDEX=$((preset_choice - 1))
                                    break
                                else
                                    echo -e "  ${RED}✗ ERROR: Invalid choice '$preset_choice'. Please choose a number between 1 and $MODEL_COUNT.${NC}"
                                    sleep 1.5
                                fi
                            done

                            if [ "$GO_BACK" = true ]; then
                                continue
                            fi

                            MODEL_REPO=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$CHOSEN_MODEL_INDEX]; print(m.get('repo', ''))")
                            MODEL_FILE=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$CHOSEN_MODEL_INDEX]; print(m.get('file', ''))")
                            break
                        done
                        break
                        ;;

                    2)
                        while true; do
                            echo ""
                            echo -e "  ${BOLD}Enter Hugging Face Repository ID (e.g. Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF):${NC}"
                            read -rp "  Repository: " custom_repo || { echo -e "\n  ${YELLOW}Cancelled.${NC}"; exit 0; }
                            custom_repo=$(echo "$custom_repo" | xargs)
                            
                            echo -e "  ${BOLD}Enter GGUF Filename (e.g. qwen2.5-coder-1.5b-instruct-q4_k_m.gguf):${NC}"
                            read -rp "  Filename: " custom_file || { echo -e "\n  ${YELLOW}Cancelled.${NC}"; exit 0; }
                            custom_file=$(echo "$custom_file" | xargs)

                            if [ -z "$custom_repo" ] || [ -z "$custom_file" ]; then
                                echo -e "  ${RED}✗ ERROR: Repository and filename cannot be empty. Please try again.${NC}"
                                sleep 1
                            else
                                MODEL_REPO="$custom_repo"
                                MODEL_FILE="$custom_file"
                                break
                            fi
                        done
                        break
                        ;;
                    *)
                        echo -e "  ${RED}✗ ERROR: Invalid choice '$dl_choice'. Please choose 1 or 2.${NC}"
                        sleep 1.5
                        ;;
                esac
            done
        else
            echo -e "  ${RED}✗ ERROR: No active LLM model configured for non-interactive download.${NC}" >&2
            echo -e "    Please specify MODEL_REPO and MODEL_FILE env variables.${NC}" >&2
            exit 1
        fi
    fi

    print_header
    target_path="$TARGET_DIR/$MODEL_FILE"
    mkdir -p "$TARGET_DIR"

    if [ -f "$target_path" ]; then
        echo -e "  ${GREEN}✓ Model file already exists locally:${NC}"
        echo -e "    ${BOLD}Path:${NC} $target_path"
        echo ""
        echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
        echo -e "  ${GREEN}✓ Setup complete! Ready to serve.${NC}"
        echo -e "  ${BOLD}Next:${NC}  bash scripts/llm.sh start"
        echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
        echo ""
    else
        if ! "$PYTHON_CMD" -c "import huggingface_hub" &> /dev/null; then
            echo -e "  ${CYAN}[i] huggingface_hub not found. Running env.sh...${NC}"
            bash "$SCRIPT_DIR/env.sh"
        fi

        echo -e "  ${CYAN}[i] Downloading LLM model from Hugging Face...${NC}"
        echo -e "    ${BOLD}Repository:${NC}  $MODEL_REPO"
        echo -e "    ${BOLD}File:${NC}        $MODEL_FILE"
        echo -e "    ${BOLD}Destination:${NC} $TARGET_DIR"
        echo ""

        if CACHE_PATH=$("$PYTHON_CMD" "$PRESETS_PY" download --repo "$MODEL_REPO" --file "$MODEL_FILE"); then
            if [ -f "$CACHE_PATH" ]; then
                ln -sf "$CACHE_PATH" "$target_path"
                echo -e "\n  ${GREEN}✓ Model download and link completed successfully!${NC}"
                echo -e "    ${BOLD}Local Path:${NC} $target_path"
                echo ""
                echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
                echo -e "  ${GREEN}✓ Setup complete! Ready to serve.${NC}"
                echo -e "  ${BOLD}Next:${NC}  bash scripts/llm.sh start"
                echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
                echo ""
            else
                echo -e "  ${RED}✗ ERROR: Cache path '$CACHE_PATH' does not resolve to a file.${NC}"
                exit 1
            fi
        else
            echo -e "  ${RED}✗ ERROR: Failed to download model using huggingface_hub.${NC}"
            exit 1
        fi
    fi
}

# ─── Execute Command ───────────────────────────────────────
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
        
        active_model=$("$PYTHON_CMD" "$PRESETS_PY" get-active-model --url "http://$HOST:$PORT/v1")
        
        echo -e "    ${BOLD}Active Model:${NC} $active_model"
        echo ""
        echo -e "  ${BOLD}Running Process Info:${NC}"
        
        active=0
        if [ -f "$PID_FILE" ]; then
            pid=""
            pid=$(cat "$PID_FILE")
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                echo -e "    ${GREEN}● Active (PID: $pid from server.pid)${NC}"
                show_pid_stats "$pid"
                active=1
            fi
        fi

        if [ "$active" -eq 0 ]; then
            pids=""
            pids=$(pgrep -f "llama_cpp.server" 2>/dev/null || true)
            if [ -n "$pids" ]; then
                echo -e "    ${GREEN}● Active (PIDs: $pids detected via pgrep)${NC}"
                for p in $pids; do
                    echo -e "      ${CYAN}[PID $p Stats]${NC}"
                    show_pid_stats "$p"
                done
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

    download)
        download_model
        ;;

    list)
        print_header
        "$PYTHON_CMD" "$PRESETS_PY" scan-models --target-dir "$TARGET_DIR" --hf-cache-dir "$HF_CACHE_DIR" --format card
        ;;

    cleanup)
        print_header
        MODELS_JSON=$("$PYTHON_CMD" "$PRESETS_PY" scan-models --target-dir "$TARGET_DIR" --hf-cache-dir "$HF_CACHE_DIR" --format json)
        total_count=$("$PYTHON_CMD" -c "import json; print(len(json.loads('''$MODELS_JSON''')))")
        
        if [ "$total_count" -eq 0 ]; then
            echo -e "  ${GREEN}✓ No downloaded models found to delete.${NC}"
            echo ""
            exit 0
        fi

        while true; do
            "$PYTHON_CMD" "$PRESETS_PY" scan-models --target-dir "$TARGET_DIR" --hf-cache-dir "$HF_CACHE_DIR" --format card
            
            echo -e "  ${BOLD}Options:${NC}"
            echo -e "    - Type ${CYAN}'all'${NC} (or ${CYAN}'a'${NC}) to delete ALL listed models."
            echo -e "    - Type space or comma separated numbers (e.g. ${CYAN}'1 3'${NC}) to delete specific models."
            echo -e "    - Press ${YELLOW}Enter${NC}, type ${YELLOW}'q'${NC}, or press ${YELLOW}Ctrl+C${NC} to cancel."
            echo ""
            
            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice || { echo -e "\n  ${YELLOW}Cancelled. No models were removed.${NC}"; exit 0; }
            choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

            if [ -z "$choice" ] || [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
                echo -e "  ${YELLOW}Cancelled. No models were removed.${NC}"
                echo ""
                exit 0
            fi

            TO_DELETE=()
            INVALID_INPUT=false

            if [ "$choice" = "all" ] || [ "$choice" = "a" ]; then
                for ((i=0; i<total_count; i++)); do
                    TO_DELETE+=("$i")
                done
            else
                IFS=', ' read -r -a selected_nums <<< "$choice"
                for n in "${selected_nums[@]}"; do
                    if [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] && [ "$n" -le "$total_count" ]; then
                        idx=$((n - 1))
                        TO_DELETE+=("$idx")
                    else
                        echo -e "  ${RED}✗ Invalid selection: '$n'.${NC}"
                        INVALID_INPUT=true
                    fi
                done
            fi

            if [ "$INVALID_INPUT" = true ]; then
                echo -e "  ${YELLOW}Please select valid model numbers or 'all'. Try again.${NC}\n"
                sleep 1.5
                continue
            fi

            if [ "${#TO_DELETE[@]}" -eq 0 ]; then
                echo -e "  ${YELLOW}No valid models selected for deletion.${NC}"
                echo ""
                exit 0
            fi

            echo ""
            echo -e "  ${RED}${BOLD}Deleting selected models...${NC}"
            for idx in "${TO_DELETE[@]}"; do
                path=$("$PYTHON_CMD" -c "import json; m = json.loads('''$MODELS_JSON''')[$idx]; print(m['path'])")
                name=$("$PYTHON_CMD" -c "import json; m = json.loads('''$MODELS_JSON''')[$idx]; print(m['display_name'])")
                echo -e "    ${RED}-${NC} Removing: $name"
                rm -rf "$path"
            done

            echo ""
            echo -e "  ${GREEN}✓ Selected model(s) removed successfully.${NC}"
            echo ""
            break
        done
        ;;

    *)
        echo -e "  ${RED}Unknown command: '$COMMAND'${NC}"
        echo "  Valid commands: start, stop, status, download, list, cleanup"
        exit 1
        ;;
esac
