#!/bin/bash
# ============================================================
# env.sh
# Initializes the environment, checks environment variables, and installs dependencies.
#
# Usage:
#   bash scripts/env.sh [command]
#
# Commands:
#   fresh     Fresh install (wipe .venv, clean all uv cache, sync)
#   sync      Force sync (clean only package cache, sync)
#   quick     Quick sync (no cache clean, just sync)
#   inspect   Inspect current environment without any changes
#   gpu       GPU / CUDA status check only
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║           Environment Setup Manager          ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

# ─── Ensure .env exists ────────────────────────────────────
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "  ${CYAN}[i] Creating default .env file...${NC}"
    printf "%s\n" \
        "# ---------------------------------------------------------------------" \
        "# Local LLaMA.cpp Server / LM Studio Configuration" \
        "# ---------------------------------------------------------------------" \
        "LLM_PROVIDER=local" \
        "DATABASE_URL=sqlite:///data/db.sqlite3" \
        "# Model selection is managed on server startup — use: bash scripts/llm_server.sh start" \
        "LOCAL_LLM_BASE_URL=http://localhost:1234/v1" \
        "LOCAL_LLM_API_KEY=not-needed" \
        "" \
        "# Local Server Runtime Configuration" \
        "LLM_SERVER_HOST=0.0.0.0" \
        "LLM_SERVER_PORT=1234" \
        "LLM_SERVER_N_CTX=8192" \
        "LLM_SERVER_N_THREADS=8" > "$PROJECT_ROOT/.env"
    echo -e "  ${GREEN}✓ Default .env file created.${NC}"
fi

# Auto-load environment variables from .env if present
if [ -r "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# ─── Parse CLI Command ─────────────────────────────────────
COMMAND=""
if [[ $# -gt 0 ]]; then
    case "$1" in
        fresh|sync|quick|inspect|gpu)
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
            echo -e "    ${BOLD}1)${NC} Fresh Install   — Wipe .venv, purge uv cache, full sync"
            echo -e "    ${BOLD}2)${NC} Force Sync      — Purge package cache, sync in existing .venv"
            echo -e "    ${BOLD}3)${NC} Quick Sync      — Sync only (no cache clearing, fastest)"
            echo -e "    ${BOLD}4)${NC} Inspect Env     — Show env health, packages, Python, CUDA status"
            echo -e "    ${BOLD}5)${NC} GPU Status      — Show GPU memory and occupancy only"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo ""
            echo -e "  ${BOLD}Options:${NC}"
            echo -e "    - Type the number of the option to execute (e.g. ${CYAN}'3'${NC})."
            echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to exit."
            echo ""

            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice
            choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

            if [ -z "$choice" ] || [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
                echo -e "  ${YELLOW}Exiting.${NC}"
                exit 0
            fi

            case "$choice" in
                1) COMMAND="fresh";   break ;;
                2) COMMAND="sync";    break ;;
                3) COMMAND="quick";   break ;;
                4) COMMAND="inspect"; break ;;
                5) COMMAND="gpu";     break ;;
                *)
                    echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and 5.${NC}"
                    echo ""
                    sleep 1
                    ;;
            esac
        done
    else
        # Non-interactive: default to quick sync
        COMMAND="quick"
    fi
fi

# ─── Helper: Resolve Python ────────────────────────────────
resolve_python() {
    if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        echo "$PROJECT_ROOT/.venv/bin/python"
    elif command -v python3 &>/dev/null; then
        echo "python3"
    elif command -v python &>/dev/null; then
        echo "python"
    else
        echo ""
    fi
}

# ─── Helper: GPU Status ────────────────────────────────────
show_gpu_status() {
    echo ""
    echo -e "${BOLD}========================================================${NC}"
    echo -e "  ${CYAN}${BOLD}GPU / CUDA Status${NC}"
    echo -e "${BOLD}========================================================${NC}"
    if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
        echo -e "  ${GREEN}✓ Nvidia GPU & CUDA Driver detected${NC}"
        echo ""
        # Compact summary: GPU name, memory used/total, GPU utilization
        nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu \
            --format=csv,noheader,nounits 2>/dev/null | while IFS=',' read -r name mem_used mem_total gpu_util temp; do
            echo -e "  ${BOLD}GPU:${NC}          ${name# }"
            echo -e "  ${BOLD}Memory:${NC}       ${mem_used# } MiB / ${mem_total# } MiB used"
            echo -e "  ${BOLD}GPU Util:${NC}     ${gpu_util# }%"
            echo -e "  ${BOLD}Temperature:${NC}  ${temp# }°C"
        done
        echo ""
        # Show running processes table
        echo -e "  ${BOLD}Running GPU Processes:${NC}"
        local procs
        procs=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null || true)
        if [ -n "$procs" ]; then
            echo "$procs" | while IFS=',' read -r pid pname pmem; do
                echo -e "    ${CYAN}PID ${pid# }${NC}  ${pname# }  (${pmem# })"
            done
        else
            echo -e "    ${YELLOW}No GPU compute processes running.${NC}"
        fi
    else
        echo -e "  ${CYAN}[i] No Nvidia GPU / CUDA driver detected on this system.${NC}"
    fi
    echo ""
}

# ─── Helper: Inspect Environment ───────────────────────────
show_inspect() {
    echo ""
    echo -e "${BOLD}========================================================${NC}"
    echo -e "  ${CYAN}${BOLD}Environment Health Inspection${NC}"
    echo -e "${BOLD}========================================================${NC}"

    # .venv presence
    if [ -d "$PROJECT_ROOT/.venv" ]; then
        echo -e "  ${GREEN}✓ Virtual environment (.venv) exists${NC}"
    else
        echo -e "  ${RED}✗ No .venv found — run 'Fresh Install' or 'Quick Sync' first${NC}"
    fi

    # Python version
    local python_cmd
    python_cmd=$(resolve_python)
    if [ -n "$python_cmd" ]; then
        local python_ver
        python_ver=$("$python_cmd" --version 2>&1)
        echo -e "  ${GREEN}✓ Python:${NC}         $python_ver  (${python_cmd})"
    else
        echo -e "  ${RED}✗ Python interpreter not found${NC}"
    fi

    # uv presence
    if command -v uv &>/dev/null; then
        local uv_ver
        uv_ver=$(uv --version 2>/dev/null)
        echo -e "  ${GREEN}✓ uv:${NC}             $uv_ver"
    else
        echo -e "  ${YELLOW}[!] uv not found — pip fallback will be used${NC}"
    fi

    # llama-cpp-python GPU support check
    if [ -n "$python_cmd" ] && [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        echo ""
        echo -e "  ${BOLD}llama-cpp-python GPU Build:${NC}"
        local llama_check
        llama_check=$("$python_cmd" -c "
import importlib.util, sys
spec = importlib.util.find_spec('llama_cpp')
if spec is None:
    print('NOT_INSTALLED')
else:
    try:
        from llama_cpp import llama_cpp as lib
        so_path = getattr(lib, '_lib_base_name', 'unknown')
        print('FOUND')
    except OSError as e:
        print(f'LOAD_ERROR:{e}')
    except Exception as e:
        print(f'ERROR:{e}')
" 2>/dev/null || echo "NOT_INSTALLED")
        case "$llama_check" in
            FOUND)
                echo -e "  ${GREEN}✓ llama_cpp importable (library loads cleanly)${NC}" ;;
            NOT_INSTALLED)
                echo -e "  ${RED}✗ llama-cpp-python NOT installed${NC}" ;;
            LOAD_ERROR:*)
                echo -e "  ${RED}✗ llama-cpp-python installed but CUDA runtime error: ${llama_check#LOAD_ERROR:}${NC}" ;;
            *)
                echo -e "  ${YELLOW}[!] llama-cpp-python check returned: $llama_check${NC}" ;;
        esac

        # Check for libcudart inside venv
        local cudart_path
        cudart_path=$(find "$PROJECT_ROOT/.venv" -name "libcudart.so.12" -print -quit 2>/dev/null || true)
        if [ -n "$cudart_path" ]; then
            echo -e "  ${GREEN}✓ libcudart.so.12:${NC}  $cudart_path"
        else
            echo -e "  ${YELLOW}[!] libcudart.so.12 not found in .venv — GPU launch may fail${NC}"
        fi
        
        # Check for libcublas inside venv
        local cublas_path
        cublas_path=$(find "$PROJECT_ROOT/.venv" -name "libcublas.so.12" -print -quit 2>/dev/null || true)
        if [ -n "$cublas_path" ]; then
            echo -e "  ${GREEN}✓ libcublas.so.12:${NC}  $cublas_path"
        else
            echo -e "  ${YELLOW}[!] libcublas.so.12 not found in .venv — GPU launch may fail${NC}"
        fi
    fi

    # .env config check
    echo ""
    echo -e "  ${BOLD}.env Configuration:${NC}"
    if [ -z "${LLM_PROVIDER:-}" ]; then
        echo -e "  ${RED}✗ LLM_PROVIDER is not set${NC}"
    else
        echo -e "  ${GREEN}✓ LLM_PROVIDER:${NC}   ${LLM_PROVIDER}"
    fi
    [ -n "${LOCAL_LLM_BASE_URL:-}" ] && echo -e "  ${GREEN}✓ LLM URL:${NC}        ${LOCAL_LLM_BASE_URL}"
    [ -n "${DATABASE_URL:-}" ]       && echo -e "  ${GREEN}✓ DATABASE_URL:${NC}   ${DATABASE_URL}"

    # Run GPU status as part of inspect
    show_gpu_status
}

# ─── Execute ───────────────────────────────────────────────
case "$COMMAND" in
    fresh)
        echo ""
        echo -e "${BOLD}========================================================${NC}"
        echo -e "  ${CYAN}${BOLD}Step 1: Fresh Install${NC}"
        echo -e "${BOLD}========================================================${NC}"
        if [ -d "$PROJECT_ROOT/.venv" ]; then
            echo -e "  ${YELLOW}[!] Deleting existing .venv...${NC}"
            rm -rf "$PROJECT_ROOT/.venv"
        fi
        if command -v uv &>/dev/null; then
            echo -e "  ${CYAN}[i] Cleaning ALL uv cache...${NC}"
            uv cache clean
            echo -e "  ${CYAN}[i] Syncing all dependencies from scratch...${NC}"
            uv sync --all-extras
            echo -e "  ${GREEN}✓ Fresh install complete.${NC}"
        else
            local python_cmd
            python_cmd=$(resolve_python)
            echo -e "  ${YELLOW}[!] uv not found. Using pip...${NC}"
            "$python_cmd" -m pip install --upgrade pip
            "$python_cmd" -m pip install -e "$PROJECT_ROOT[gemini,notebook]"
            echo -e "  ${GREEN}✓ pip install complete.${NC}"
        fi
        show_gpu_status
        ;;

    sync)
        echo ""
        echo -e "${BOLD}========================================================${NC}"
        echo -e "  ${CYAN}${BOLD}Step 1: Force Sync (Purge Package Cache)${NC}"
        echo -e "${BOLD}========================================================${NC}"
        if command -v uv &>/dev/null; then
            echo -e "  ${CYAN}[i] Purging llama-cpp-python from uv cache...${NC}"
            uv cache clean llama-cpp-python
            echo -e "  ${CYAN}[i] Syncing all dependencies...${NC}"
            uv sync --all-extras
            echo -e "  ${GREEN}✓ Force sync complete.${NC}"
        else
            echo -e "  ${RED}✗ uv not found. Cannot force sync without uv.${NC}"
            exit 1
        fi
        show_gpu_status
        ;;

    quick)
        echo ""
        echo -e "${BOLD}========================================================${NC}"
        echo -e "  ${CYAN}${BOLD}Step 1: Quick Sync${NC}"
        echo -e "${BOLD}========================================================${NC}"
        if command -v uv &>/dev/null; then
            echo -e "  ${CYAN}[i] Running uv sync (no cache clearing)...${NC}"
            uv sync --all-extras
            echo -e "  ${GREEN}✓ Quick sync complete.${NC}"
        else
            local python_cmd
            python_cmd=$(resolve_python)
            echo -e "  ${YELLOW}[!] uv not found. Using pip...${NC}"
            "$python_cmd" -m pip install -e "$PROJECT_ROOT[gemini,notebook]"
            echo -e "  ${GREEN}✓ pip install complete.${NC}"
        fi
        show_gpu_status
        ;;

    inspect)
        show_inspect
        ;;

    gpu)
        show_gpu_status
        ;;

    *)
        echo -e "  ${RED}Unknown command: '$COMMAND'${NC}"
        echo "  Valid commands: fresh, sync, quick, inspect, gpu"
        exit 1
        ;;
esac

echo -e "  ${GREEN}${BOLD}Done.${NC}"
echo -e "${BOLD}========================================================${NC}"
echo -e "  ${BOLD}Next:${NC} ${YELLOW}bash scripts/llm_server.sh start${NC}"
echo -e "${BOLD}========================================================${NC}"
