#!/bin/bash
# ============================================================
# llm_manage.sh
# Management CLI for downloading and cleaning up local GGUF models.
#
# Usage:
#   bash scripts/llm_manage.sh [command]
#
# Commands:
#   download         Download configured model from Hugging Face (default)
#   cleanup          Interactively scan and delete downloaded models
#   list             List all downloaded models and their cache sizes
#   exit             Exit the CLI
# ============================================================

set -euo pipefail
export PYTHONWARNINGS="ignore"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── Colors ────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Load Environment ──────────────────────────────────────
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXISTS=false
if [ -r "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    ENV_EXISTS=true
fi

# Fallback defaults
DEFAULT_REPO="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
DEFAULT_FILE="qwen2.5-coder-7b-instruct-q4_k_m.gguf"

MODEL_REPO="${HF_REPO:-}"
MODEL_FILE="${HF_FILE:-}"

TARGET_DIR="$HOME/models"
HF_CACHE_DIR="$HOME/.cache/huggingface/hub"

print_header() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║           LLM Model Cache Manager            ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

# ─── Parse CLI Command ─────────────────────────────────────
COMMAND=""
if [[ $# -gt 0 ]]; then
    case "$1" in
        download|cleanup|list)
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
            "Download configured model      (download)"
            "Delete downloaded models       (cleanup)"
            "List local cached models       (list)"
            "Exit"
        )
        COLUMNS=1
        select opt in "${options[@]}"; do
            if [[ -z "$opt" && -z "$REPLY" ]]; then
                echo "No selection made. Exiting."
                exit 0
            fi
            case $REPLY in
                1) COMMAND="download"; break ;;
                2) COMMAND="cleanup";  break ;;
                3) COMMAND="list";     break ;;
                4) echo "Exiting."; exit 0 ;;
                *) echo -e "  ${RED}Invalid option. Please choose 1–4.${NC}" ;;
            esac
        done
    else
        # Non-interactive: default to download
        COMMAND="download"
    fi
fi

# ─── Locate Python ─────────────────────────────────────────
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
fi

# ─── Find Models Helper ────────────────────────────────────
scan_models() {
    # Sets global arrays
    MODEL_PATHS=()
    MODEL_NAMES=()
    MODEL_SIZES=()

    # 1. Scan ~/models directory
    if [ -d "$TARGET_DIR" ]; then
        while IFS= read -r item; do
            [ -z "$item" ] && continue
            MODEL_PATHS+=("$item")
            MODEL_NAMES+=("Local Link/File: $(basename "$item")")
            MODEL_SIZES+=("$(du -sh "$item" 2>/dev/null | cut -f1)")
        done < <(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 2>/dev/null || true)
    fi

    # 2. Scan ~/.cache/huggingface/hub directory
    if [ -d "$HF_CACHE_DIR" ]; then
        while IFS= read -r item; do
            [ -z "$item" ] && continue
            local clean_name
            clean_name=$(basename "$item" | sed 's/^models--//' | sed 's/--/\//g')
            MODEL_PATHS+=("$item")
            MODEL_NAMES+=("Hugging Face Cache: $clean_name")
            MODEL_SIZES+=("$(du -sh "$item" 2>/dev/null | cut -f1)")
        done < <(find "$HF_CACHE_DIR" -mindepth 1 -maxdepth 1 -name "models--*" 2>/dev/null || true)
    fi
}

# ─── Execute Command ───────────────────────────────────────
case "$COMMAND" in

    download)
        print_header
        
        # 1. Check if model attributes are set in environment
        if [ -z "$MODEL_REPO" ] || [ -z "$MODEL_FILE" ]; then
            echo -e "  ${YELLOW}! Warning: Model attributes not configured in your .env file.${NC}"
            if [ "$ENV_EXISTS" = true ]; then
                echo -e "    Please define ${BOLD}HF_REPO${NC} and ${BOLD}HF_FILE${NC} in: $ENV_FILE"
            else
                echo -e "    No .env file was found in: $PROJECT_ROOT"
            fi
            echo -e "    Falling back to defaults:"
            echo -e "      ${BOLD}Default Repo:${NC} $DEFAULT_REPO"
            echo -e "      ${BOLD}Default File:${NC} $DEFAULT_FILE"
            echo ""
            
            MODEL_REPO="$DEFAULT_REPO"
            MODEL_FILE="$DEFAULT_FILE"
        fi

        target_path="$TARGET_DIR/$MODEL_FILE"
        mkdir -p "$TARGET_DIR"

        if [ -f "$target_path" ]; then
            echo -e "  ${GREEN}✓ Model file already exists locally:${NC}"
            echo -e "    ${BOLD}Path:${NC} $target_path"
            echo ""
            echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
            echo -e "  ${GREEN}✓ Setup complete! Ready to serve.${NC}"
            echo -e "  ${BOLD}Next:${NC}  bash scripts/llm_server.sh start"
            echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════╝${NC}"
            echo ""
        else
            # Verify huggingface_hub is installed
            if ! "$PYTHON_CMD" -c "import huggingface_hub" &> /dev/null; then
                echo -e "  ${CYAN}[i] huggingface_hub not found. Running setup_env.sh...${NC}"
                bash "$SCRIPT_DIR/setup_env.sh"
            fi

            echo -e "  ${CYAN}[i] Downloading LLM model from Hugging Face...${NC}"
            echo -e "    ${BOLD}Repository:${NC}  $MODEL_REPO"
            echo -e "    ${BOLD}File:${NC}        $MODEL_FILE"
            echo -e "    ${BOLD}Destination:${NC} $TARGET_DIR"
            echo ""

            # Run download
            if CACHE_PATH=$("$PYTHON_CMD" -c "from huggingface_hub import hf_hub_download; print(hf_hub_download(repo_id='$MODEL_REPO', filename='$MODEL_FILE'))"); then
                if [ -f "$CACHE_PATH" ]; then
                    ln -sf "$CACHE_PATH" "$target_path"
                    echo -e "\n  ${GREEN}✓ Model download and link completed successfully!${NC}"
                    echo -e "    ${BOLD}Local Path:${NC} $target_path"
                    echo ""
                    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════╗${NC}"
                    echo -e "  ${GREEN}✓ Setup complete! Ready to serve.${NC}"
                    echo -e "  ${BOLD}Next:${NC}  bash scripts/llm_server.sh start"
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
        ;;

    list)
        print_header
        scan_models
        total_count=${#MODEL_PATHS[@]}
        
        if [ "$total_count" -eq 0 ]; then
            echo -e "  ${GREEN}✓ No downloaded models found in ~/models or Hugging Face cache.${NC}"
            echo ""
            exit 0
        fi

        echo -e "  ${CYAN}[i] Locally cached model files:${NC}"
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        for i in "${!MODEL_PATHS[@]}"; do
            num=$((i + 1))
            printf "    ${BOLD}%2d)${NC} %-52s [${YELLOW}%s${NC}]\n" "$num" "${MODEL_NAMES[$i]}" "${MODEL_SIZES[$i]}"
            echo -e "        ${BOLD}Path:${NC} ${MODEL_PATHS[$i]}"
        done
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        echo ""
        ;;

    cleanup)
        print_header
        scan_models
        total_count=${#MODEL_PATHS[@]}
        
        if [ "$total_count" -eq 0 ]; then
            echo -e "  ${GREEN}✓ No downloaded models found to delete.${NC}"
            echo ""
            exit 0
        fi

        echo -e "  ${CYAN}[i] Found $total_count model(s) in cache:${NC}"
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        for i in "${!MODEL_PATHS[@]}"; do
            num=$((i + 1))
            printf "    ${BOLD}%2d)${NC} %-52s [${YELLOW}%s${NC}]\n" "$num" "${MODEL_NAMES[$i]}" "${MODEL_SIZES[$i]}"
            echo -e "        ${BOLD}Path:${NC} ${MODEL_PATHS[$i]}"
        done
        echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
        echo ""
        
        echo -e "  ${BOLD}Options:${NC}"
        echo -e "    - Type ${CYAN}'all'${NC} (or ${CYAN}'a'${NC}) to delete ALL listed models."
        echo -e "    - Type space or comma separated numbers (e.g. ${CYAN}'1 3'${NC}) to delete specific models."
        echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to cancel."
        echo ""
        read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" choice

        choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

        if [ -z "$choice" ] || [ "$choice" == "q" ] || [ "$choice" == "quit" ]; then
            echo -e "  ${YELLOW}Cancelled. No models were removed.${NC}"
            echo ""
            exit 0
        fi

        TO_DELETE=()

        if [ "$choice" == "all" ] || [ "$choice" == "a" ]; then
            for i in "${!MODEL_PATHS[@]}"; do
                TO_DELETE+=("$i")
            done
        else
            # Parse numbers
            IFS=', ' read -r -a selected_nums <<< "$choice"
            for n in "${selected_nums[@]}"; do
                if [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] && [ "$n" -le "$total_count" ]; then
                    idx=$((n - 1))
                    TO_DELETE+=("$idx")
                else
                    echo -e "  ${RED}! Invalid selection: '$n'. Skipping.${NC}"
                fi
            done
        fi

        if [ "${#TO_DELETE[@]}" -eq 0 ]; then
            echo -e "  ${YELLOW}No valid models selected for deletion.${NC}"
            echo ""
            exit 0
        fi

        echo ""
        echo -e "  ${RED}${BOLD}Deleting selected models...${NC}"
        for idx in "${TO_DELETE[@]}"; do
            path="${MODEL_PATHS[$idx]}"
            name="${MODEL_NAMES[$idx]}"
            echo -e "    ${RED}-${NC} Removing: $name"
            rm -rf "$path"
        done

        echo ""
        echo -e "  ${GREEN}✓ Selected model(s) removed successfully.${NC}"
        echo ""
        ;;

    *)
        echo -e "  ${RED}Unknown command: '$COMMAND'${NC}"
        echo "  Valid commands: download, cleanup, list"
        exit 1
        ;;
esac
