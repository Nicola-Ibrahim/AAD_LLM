#!/bin/bash
# ============================================================
# clean.sh
# Management CLI for cleaning project artifacts and log files safely.
#
# Usage:
#   bash scripts/clean.sh [command]
#
# Commands:
#   artifacts        Clean data artifacts (evolution_state, code)
#   logs             Clean application logs (logs/ directory)
#   all              Clean both data artifacts and logs
#   exit             Exit the CLI
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Clean signal handling for interrupts (Ctrl+C)
trap 'echo -e "\n  \033[1;33mInterrupted.\033[0m"; exit 130' INT
trap 'exit 143' TERM

# ─── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Helpers ───────────────────────────────────────────────
print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║        Artifact & Log Cleanup CLI            ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

confirm() {
    local prompt="${1:-Are you sure?}"
    local answer
    while true; do
        read -rp "$(echo -e "${YELLOW}${prompt} [y/N]: ${NC}")" answer || return 1
        answer=$(echo "$answer" | tr '[:upper:]' '[:lower:]' | xargs)
        if [[ "$answer" =~ ^[Yy]$ ]]; then
            return 0
        elif [[ "$answer" =~ ^[Nn]$ ]] || [ -z "$answer" ] || [ "$answer" = "q" ] || [ "$answer" = "quit" ]; then
            return 1
        else
            echo -e "  ${RED}✗ Please enter 'y' for yes or 'n' for no.${NC}"
        fi
    done
}

confirm_type() {
    local word="$1"
    local answer
    while true; do
        read -rp "$(echo -e "${RED}  Type '${word}' to confirm: ${NC}")" answer || return 1
        answer=$(echo "$answer" | xargs)
        if [[ "$answer" == "$word" ]]; then
            return 0
        elif [ "$answer" = "q" ] || [ "$answer" = "quit" ] || [ "$answer" = "exit" ]; then
            return 1
        else
            echo -e "  ${RED}✗ Confirmation text did not match '${word}'. Try again or type 'q' to cancel.${NC}"
        fi
    done
}

clean_artifacts() {
    echo -e "  ${RED}${BOLD}⚠ WARNING: Cleaning Data Artifacts${NC}"
    echo -e "  This will purge all files inside:"
    echo -e "    • ${BOLD}$PROJECT_ROOT/data/evolution_state${NC}"
    echo -e "    • ${BOLD}$PROJECT_ROOT/data/code${NC}"
    echo -e "  IOH logs, benchmark results, and the database are preserved."
    echo ""
    
    if confirm "Are you sure you want to delete these artifact directories?"; then
        if confirm_type "CLEAN"; then
            if [[ -L "$PROJECT_ROOT/data" || -L "$PROJECT_ROOT/data/evolution_state" || -L "$PROJECT_ROOT/data/code" ]]; then
                echo "Refusing to clean symlinked data directories." >&2
                return 1
            fi
            echo -e "\n  ${YELLOW}Cleaning data artifact files...${NC}"
            mkdir -p "$PROJECT_ROOT/data/evolution_state" "$PROJECT_ROOT/data/code"
            find "$PROJECT_ROOT/data/evolution_state" -mindepth 1 -delete
            find "$PROJECT_ROOT/data/code" -mindepth 1 -delete
            echo -e "  ${GREEN}✓ Evolution state and generated code cleaned.${NC}"
        else
            echo -e "  ${YELLOW}Aborted.${NC}"
        fi
    else
        echo -e "  ${YELLOW}Aborted.${NC}"
    fi
}

clean_logs() {
    echo -e "  ${YELLOW}${BOLD}Cleaning Log Files${NC}"
    echo -e "  This will purge log files inside:"
    echo -e "    • ${BOLD}$PROJECT_ROOT/logs${NC}"
    echo ""

    if confirm "Delete log files in $PROJECT_ROOT/logs?"; then
        if [[ -L "$PROJECT_ROOT/logs" ]]; then
            echo "Refusing to clean a symlinked logs directory." >&2
            return 1
        fi
        if [[ -f "$PROJECT_ROOT/logs/server.pid" ]]; then
            local server_pid
            read -r server_pid < "$PROJECT_ROOT/logs/server.pid"
            if [[ "$server_pid" =~ ^[1-9][0-9]*$ ]] && kill -0 "$server_pid" 2>/dev/null; then
                echo "Stop the managed model server before cleaning its logs." >&2
                return 1
            fi
        fi
        if [ -d "$PROJECT_ROOT/logs" ]; then
            find "$PROJECT_ROOT/logs" -mindepth 1 -delete
        fi
        echo -e "  ${GREEN}✓ Log files cleaned.${NC}"
    else
        echo -e "  ${YELLOW}Aborted.${NC}"
    fi
}

# ─── Parse CLI Command ─────────────────────────────────────
COMMAND=""
if [[ $# -gt 0 ]]; then
    case "$1" in
        artifacts|data|logs|all)
            COMMAND="$1"
            shift
            ;;
        -h|--help) sed -n '5,14p' "$0"; exit 0 ;;
        exit|q|quit) exit 0 ;;
        *) echo "Unknown command: $1 (expected artifacts, logs, or all)." >&2; exit 2 ;;
    esac
fi
if [[ $# -gt 0 ]]; then
    echo "Unexpected argument: $1" >&2
    exit 2
fi

# ─── Interactive Menu (if no command given) ────────────────
if [[ -z "$COMMAND" ]]; then
    if [[ -t 0 ]]; then
        while true; do
            print_header
            echo -e "  ${BOLD}Select cleanup scope:${NC}"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo -e "    ${BOLD}1)${NC} Clean data artifacts (evolution_state, code)"
            echo -e "    ${BOLD}2)${NC} Clean log files      (logs/ directory)"
            echo -e "    ${BOLD}3)${NC} Clean ALL           (data artifacts + logs)"
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
                1) COMMAND="artifacts"; break ;;
                2) COMMAND="logs";      break ;;
                3) COMMAND="all";       break ;;
                *)
                    echo -e "  ${RED}✗ ERROR: Invalid choice '$choice'. Please choose a number between 1 and 3.${NC}"
                    sleep 1.5
                    ;;
            esac
        done
    else
        echo -e "  ${RED}✗ ERROR: Command required in non-interactive mode (artifacts, logs, all).${NC}"
        exit 1
    fi
fi

# ─── Execute Command ───────────────────────────────────────
print_header
case "$COMMAND" in
    artifacts|data)
        clean_artifacts
        ;;
    logs)
        clean_logs
        ;;
    all)
        clean_artifacts
        echo ""
        clean_logs
        ;;
    *)
        echo -e "  ${RED}Unknown command: '$COMMAND'${NC}"
        echo "  Valid commands: artifacts, logs, all"
        exit 1
        ;;
esac
