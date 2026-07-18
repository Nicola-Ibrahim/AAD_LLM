#!/bin/bash
# ============================================================
# env.sh
# Initializes the environment, checks environment variables, and installs dependencies.
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

# Check if .env exists, create if not
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

print_header

SETUP_MODE="2" # Default to 2 (Quick Sync) if non-interactive
if [[ -t 0 ]]; then
    while true; do
        echo -e "  ${BOLD}Select environment setup mode:${NC}"
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        echo -e "    ${BOLD}1)${NC} Fresh Install  (Delete old .venv, clean uv cache, sync)"
        echo -e "    ${BOLD}2)${NC} Quick Sync     (Clean uv cache, sync in existing .venv)"
        echo -e "    ${BOLD}3)${NC} Skip Install   (Only run configuration and GPU checks)"
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        echo ""
        echo -e "  ${BOLD}Options:${NC}"
        echo -e "    - Type the number of the option to execute (e.g. ${CYAN}'2'${NC})."
        echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to exit."
        echo ""

        read -rp "$(echo -e "  ${BOLD}Your choice [default: 2]:${NC} ")" choice
        choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

        if [ -z "$choice" ]; then
            SETUP_MODE="2"
            break
        elif [ "$choice" = "q" ] || [ "$choice" = "quit" ] || [ "$choice" = "exit" ]; then
            echo -e "  ${YELLOW}Exiting.${NC}"
            exit 0
        fi

        case "$choice" in
            1|2|3)
                SETUP_MODE="$choice"
                break
                ;;
            *)
                echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and 3.${NC}"
                echo ""
                sleep 1
                ;;
        esac
    done
fi

echo ""
echo -e "${BOLD}========================================================${NC}"
echo -e "  ${CYAN}${BOLD}Step 1: Install Dependencies${NC}"
echo -e "${BOLD}========================================================${NC}"

if [ "$SETUP_MODE" = "3" ]; then
    echo -e "  ${CYAN}[i] Skipping dependency installation/sync as requested.${NC}"
else
    if [ "$SETUP_MODE" = "1" ]; then
        echo -e "  ${CYAN}[i] Performing Fresh Install...${NC}"
        if [ -d "$PROJECT_ROOT/.venv" ]; then
            echo -e "  ${YELLOW}[!] Deleting existing virtual environment (.venv)...${NC}"
            rm -rf "$PROJECT_ROOT/.venv"
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
        echo -e "  ${RED}✗ ERROR: Python interpreter not found.${NC}"
        exit 1
    fi

    echo -e "  ${CYAN}[i] Using Python: $PYTHON_CMD ($("$PYTHON_CMD" --version))${NC}"

    if command -v uv &> /dev/null; then
        echo -e "  ${CYAN}[i] uv detected. Cleaning cache and synchronizing environment...${NC}"
        uv cache clean
        uv sync --all-extras
        echo -e "  ${GREEN}✓ uv environment successfully synchronized.${NC}"
    else
        echo -e "  ${YELLOW}[!] uv not found. Falling back to pip installation...${NC}"
        # Fallback to standard pip setup
        "$PYTHON_CMD" -m pip install --upgrade pip
        "$PYTHON_CMD" -m pip install -e "$PROJECT_ROOT[gemini,notebook]" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
        echo -e "  ${GREEN}✓ Dependencies installed successfully via pip.${NC}"
    fi
fi

# Check LLM_PROVIDER is configured
echo ""
echo -e "  ${CYAN}[i] Verifying configuration environment variables...${NC}"
if [ -z "${LLM_PROVIDER:-}" ]; then
    echo -e "  ${RED}✗ WARNING: LLM_PROVIDER is missing from .env file.${NC}"
else
    echo -e "  ${GREEN}✓ Environment configurations verified: provider=${LLM_PROVIDER}.${NC}"
fi

# Check CUDA / GPU existence and occupancy
echo ""
echo -e "${BOLD}========================================================${NC}"
echo -e "  ${CYAN}${BOLD}Step 2: Check GPU / CUDA Status${NC}"
echo -e "${BOLD}========================================================${NC}"
if command -v nvidia-smi &>/dev/null; then
    if nvidia-smi &>/dev/null; then
        echo -e "  ${GREEN}✓ Nvidia GPU & CUDA Driver detected.${NC}"
        echo -e "  ${BOLD}Current GPU occupancy details:${NC}"
        nvidia-smi
    else
        echo -e "  ${RED}✗ WARNING: nvidia-smi tool is present but failed to communicate with the driver.${NC}"
    fi
else
    echo -e "  ${CYAN}[i] No Nvidia GPU / CUDA driver detected on this system.${NC}"
fi

echo ""
echo -e "  ${GREEN}${BOLD}All dependencies satisfied.${NC}"
echo -e "${BOLD}========================================================${NC}"
echo -e "  ${BOLD}Next:${NC} ${YELLOW}bash scripts/llm_manage.sh${NC}"
echo -e "${BOLD}========================================================${NC}"
