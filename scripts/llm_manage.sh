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
ENV_INDICATOR="default"

if [ -n "$MODEL_REPO" ] && [ -n "$MODEL_FILE" ]; then
    ENV_INDICATOR="env"
else
    MODEL_REPO="$DEFAULT_REPO"
    MODEL_FILE="$DEFAULT_FILE"
fi

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
            "Download configured model ($MODEL_FILE) ($ENV_INDICATOR)"
            "Select and download a model preset"
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
                2)
                    # Find correct python interpreter
                    PYTHON_CMD="python3"
                    if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
                        PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
                    elif command -v uv &> /dev/null; then
                        PYTHON_CMD="uv run python"
                    fi

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

                        echo "  Select a model family/category:"
                        echo ""
                        cat_options=()
                        for ((i=0; i<CAT_COUNT; i++)); do
                            cat_name=$("$PYTHON_CMD" -c "import json; print(json.loads('''$CATEGORIES_JSON''')[$i]['name'])")
                            cat_desc=$("$PYTHON_CMD" -c "import json; print(json.loads('''$CATEGORIES_JSON''')[$i]['description'])")
                            cat_options+=("$cat_name   ($cat_desc)")
                        done
                        cat_options+=("Cancel")

                        SELECTED_CAT=""
                        select cat_opt in "${cat_options[@]}"; do
                            if [[ -z "$cat_opt" && -z "$REPLY" ]]; then
                                echo "Cancelled."
                                exit 0
                            fi
                            if [ "$REPLY" -eq "$((CAT_COUNT + 1))" ]; then
                                echo "Cancelled."
                                exit 0
                            fi
                            if [ "$REPLY" -ge 1 ] && [ "$REPLY" -le "$CAT_COUNT" ]; then
                                SELECTED_CAT=$("$PYTHON_CMD" -c "import json; print(json.loads('''$CATEGORIES_JSON''')[$((REPLY - 1))]['name'])")
                                break
                            else
                                echo -e "  ${RED}Invalid option. Please choose 1–$((CAT_COUNT + 1)).${NC}"
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
                        echo "  Select a model from family '$SELECTED_CAT' to download and set as active in .env:"
                        echo ""
                        
                        presets=()
                        for ((i=0; i<MODEL_COUNT; i++)); do
                            name=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$i]; print(m.get('name', ''))")
                            desc=$("$PYTHON_CMD" -c "import json; m = json.loads('''$FILTERED_MODELS''')[$i]; print(m.get('description', ''))")
                            presets+=("$name   ($desc)")
                        done
                        presets+=("Go Back to Category List")
                        presets+=("Cancel")

                        CHOSEN_MODEL_INDEX=""
                        GO_BACK=false
                        select preset_opt in "${presets[@]}"; do
                            if [[ -z "$preset_opt" && -z "$REPLY" ]]; then
                                echo "Cancelled."
                                exit 0
                            fi
                            if [ "$REPLY" -eq "$((MODEL_COUNT + 1))" ]; then
                                GO_BACK=true
                                break
                            fi
                            if [ "$REPLY" -eq "$((MODEL_COUNT + 2))" ]; then
                                echo "Cancelled."
                                exit 0
                            fi
                            if [ "$REPLY" -ge 1 ] && [ "$REPLY" -le "$MODEL_COUNT" ]; then
                                CHOSEN_MODEL_INDEX=$((REPLY - 1))
                                break
                            else
                                echo -e "  ${RED}Invalid option. Please choose 1–$((MODEL_COUNT + 2)).${NC}"
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

                    # Update .env file using Python helper
                    echo -e "\n  ${CYAN}[i] Updating configuration in .env file...${NC}"
                    touch "$ENV_FILE"

                    "$PYTHON_CMD" -c "
import os
path = '$ENV_FILE'
keys = {
    'HF_REPO': '$SELECTED_REPO',
    'HF_FILE': '$SELECTED_FILE',
    'LOCAL_LLM_MODEL': '$SELECTED_MODEL'
}
lines = []
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
else:
    lines = [f'{k}={v}\n' for k, v in keys.items()]
    
new_lines = []
updated = set()
for line in lines:
    stripped = line.strip()
    if '=' in stripped and not stripped.startswith('#'):
        k = stripped.split('=', 1)[0].strip()
        if k in keys:
            new_lines.append(f'{k}={keys[k]}\n')
            updated.add(k)
            continue
    new_lines.append(line)
    
for k, v in keys.items():
    if k not in updated:
        new_lines.append(f'{k}={v}\n')
        
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
"
                    echo -e "  ${GREEN}✓ .env file updated successfully!${NC}"
                    echo -e "    ${BOLD}HF_REPO:${NC}          $SELECTED_REPO"
                    echo -e "    ${BOLD}HF_FILE:${NC}          $SELECTED_FILE"
                    echo -e "    ${BOLD}LOCAL_LLM_MODEL:${NC}  $SELECTED_MODEL"
                    echo ""

                    # Set parameters for the download case execution
                    MODEL_REPO="$SELECTED_REPO"
                    MODEL_FILE="$SELECTED_FILE"
                    COMMAND="download"
                    break
                    ;;
                3) COMMAND="cleanup";  break ;;
                4) COMMAND="list";     break ;;
                5) echo "Exiting."; exit 0 ;;
                *) echo -e "  ${RED}Invalid option. Please choose 1–5.${NC}" ;;
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
