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

# ─── Locate Python ─────────────────────────────────────────
PYTHON_CMD="python3"
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
fi

# ─── Load Environment ──────────────────────────────────────
ENV_FILE="$PROJECT_ROOT/.env"
if [ -r "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

MODEL_REPO=""
MODEL_FILE=""
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
        while true; do
            print_header
            echo -e "  ${BOLD}Select an operation:${NC}"
            echo -e "  ${CYAN}----------------------------------------------------------------------${NC}"
            echo -e "    ${BOLD}1)${NC} Select and download a model preset"
            echo -e "    ${BOLD}2)${NC} Download from custom Hugging Face repo & file"
            echo -e "    ${BOLD}3)${NC} Delete downloaded models               (cleanup)"
            echo -e "    ${BOLD}4)${NC} List local cached models               (list)"
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
                1)

                    # Interactive Preset Submenu
                    TOML_FILE="$PROJECT_ROOT/scripts/llms.toml"
                    if [ ! -f "$TOML_FILE" ]; then
                        echo -e "  ${RED}✗ ERROR: Preset file not found: $TOML_FILE${NC}"
                        exit 1
                    fi

                    # Loop to support Back/Cancel actions
                    while true; do
                        print_header
                        echo "  Loading model presets from scripts/llms.toml..."
                        
                        # Load categories dynamically using Python
                        CATEGORIES_JSON=$("$PYTHON_CMD" -c "
import json
path = '$TOML_FILE'

def parse_toml_fallback(content):
    data = {}
    current_section = None
    current_obj = None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[[') and line.endswith(']]'):
            header = line[2:-2].strip()
            parts = header.split('.')
            section = parts[0]
            if section not in data:
                data[section] = {'llms': []}
            current_obj = {}
            data[section]['llms'].append(current_obj)
            current_section = None
        elif line.startswith('[') and line.endswith(']'):
            header = line[1:-1].strip()
            if header not in data:
                data[header] = {'llms': []}
            current_section = header
            current_obj = None
        elif '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('\"').strip('\'')
            if current_obj is not None:
                current_obj[k] = v
            elif current_section is not None:
                data[current_section][k] = v
    return data

try:
    import tomllib
    with open(path, 'rb') as f:
        data = tomllib.load(f)
except ImportError:
    with open(path, 'r', encoding='utf-8') as f:
        data = parse_toml_fallback(f.read())

# Keep track of categories and their descriptions
categories = []
for cat_name, cat_data in data.items():
    desc = cat_data.get('description', '')
    categories.append({'name': cat_name, 'description': desc})
print(json.dumps(categories))
")

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
                        echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to cancel."
                        echo ""

                        SELECTED_CAT=""
                        while true; do
                            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" cat_choice
                            cat_choice=$(echo "$cat_choice" | tr '[:upper:]' '[:lower:]' | xargs)
                            
                            if [ -z "$cat_choice" ] || [ "$cat_choice" = "q" ] || [ "$cat_choice" = "quit" ] || [ "$cat_choice" = "exit" ] || [ "$cat_choice" = "cancel" ]; then
                                echo -e "  ${YELLOW}Cancelled.${NC}"
                                exit 0
                            fi
                            
                            if [[ "$cat_choice" =~ ^[0-9]+$ ]] && [ "$cat_choice" -ge 1 ] && [ "$cat_choice" -le "$CAT_COUNT" ]; then
                                SELECTED_CAT=$("$PYTHON_CMD" -c "import json; print(json.loads('''$CATEGORIES_JSON''')[$((cat_choice - 1))]['name'])")
                                break
                            else
                                echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and $CAT_COUNT.${NC}"
                            fi
                        done

                        # Fetch filtered models for the chosen category
                        FILTERED_MODELS=$("$PYTHON_CMD" -c "
import json
path = '$TOML_FILE'

def parse_toml_fallback(content):
    data = {}
    current_section = None
    current_obj = None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[[') and line.endswith(']]'):
            header = line[2:-2].strip()
            parts = header.split('.')
            section = parts[0]
            if section not in data:
                data[section] = {'llms': []}
            current_obj = {}
            data[section]['llms'].append(current_obj)
            current_section = None
        elif line.startswith('[') and line.endswith(']'):
            header = line[1:-1].strip()
            if header not in data:
                data[header] = {'llms': []}
            current_section = header
            current_obj = None
        elif '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('\"').strip('\'')
            if current_obj is not None:
                current_obj[k] = v
            elif current_section is not None:
                data[current_section][k] = v
    return data

try:
    import tomllib
    with open(path, 'rb') as f:
        data = tomllib.load(f)
except ImportError:
    with open(path, 'r', encoding='utf-8') as f:
        data = parse_toml_fallback(f.read())

selected_cat = '$SELECTED_CAT'
filtered = data.get(selected_cat, {}).get('llms', [])
print(json.dumps(filtered))
")

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
                        echo -e "    - Press ${YELLOW}Enter${NC} or type ${YELLOW}'q'${NC} to cancel."
                        echo ""

                        CHOSEN_MODEL_INDEX=""
                        GO_BACK=false
                        while true; do
                            read -rp "$(echo -e "  ${BOLD}Your choice:${NC} ")" preset_choice
                            preset_choice=$(echo "$preset_choice" | tr '[:upper:]' '[:lower:]' | xargs)
                            
                            if [ -z "$preset_choice" ] || [ "$preset_choice" = "q" ] || [ "$preset_choice" = "quit" ] || [ "$preset_choice" = "exit" ] || [ "$preset_choice" = "cancel" ]; then
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
                                echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and $MODEL_COUNT.${NC}"
                            fi
                        done

                        if [ "$GO_BACK" = true ]; then
                            continue
                        fi

                        # If we have a chosen model, read its details and break the main loop
                        SELECTED_REPO=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$CHOSEN_MODEL_INDEX]; print(m.get('repo', ''))")
                        SELECTED_FILE=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$CHOSEN_MODEL_INDEX]; print(m.get('file', ''))")
                        SELECTED_MODEL=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$CHOSEN_MODEL_INDEX]; print(m.get('model', ''))")
                        break
                    done

                    # Set parameters for the download case execution
                    MODEL_REPO="$SELECTED_REPO"
                    MODEL_FILE="$SELECTED_FILE"
                    COMMAND="download"
                    break
                    ;;
                2)
                    echo ""
                    echo -e "  ${BOLD}Enter Hugging Face Repository ID (e.g. Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF):${NC}"
                    read -rp "  Repository: " custom_repo
                    echo -e "  ${BOLD}Enter GGUF Filename (e.g. qwen2.5-coder-1.5b-instruct-q4_k_m.gguf):${NC}"
                    read -rp "  Filename: " custom_file

                    if [ -z "$custom_repo" ] || [ -z "$custom_file" ]; then
                        echo -e "  ${RED}✗ ERROR: Repository and filename cannot be empty.${NC}"
                        exit 1
                    fi

                    MODEL_REPO="$custom_repo"
                    MODEL_FILE="$custom_file"
                    COMMAND="download"
                    break
                    ;;
                3) COMMAND="cleanup";  break ;;
                4) COMMAND="list";     break ;;
                *)
                    echo -e "  ${RED}✗ ERROR: Invalid choice. Please choose a number between 1 and 4.${NC}"
                    echo ""
                    sleep 1
                    ;;
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
        
        # 1. Check if model attributes are configured
        if [ -z "$MODEL_REPO" ] || [ -z "$MODEL_FILE" ]; then
            echo -e "  ${RED}✗ ERROR: No active LLM model selected.${NC}" >&2
            echo -e "    Please select or download a preset first using option 2," >&2
            echo -e "    or download a custom model using option 3." >&2
            echo "" >&2
            exit 1
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
        echo "  Valid commands: download, cleanup, list, select"
        exit 1
        ;;
esac
