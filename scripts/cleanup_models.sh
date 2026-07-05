#!/bin/bash
# ============================================================
# cleanup_models.sh
# Scans for downloaded models in ~/models and ~/.cache/huggingface/hub,
# displays disk space usage, and interactively prompts for deletion.
# ============================================================

set -euo pipefail

TARGET_DIR="$HOME/models"
HF_CACHE_DIR="$HOME/.cache/huggingface/hub"

echo "========================================================"
echo "  Model Cleanup Utility"
echo "========================================================"
echo ""

# Collect model directories/files into an array
declare -a MODEL_PATHS=()
declare -a MODEL_NAMES=()
declare -a MODEL_SIZES=()

# 1. Check ~/models directory
if [ -d "$TARGET_DIR" ]; then
    while IFS= read -r item; do
        [ -z "$item" ] && continue
        MODEL_PATHS+=("$item")
        MODEL_NAMES+=("Symlink/File: $(basename "$item")")
        MODEL_SIZES+=("$(du -sh "$item" 2>/dev/null | cut -f1)")
    done < <(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 2>/dev/null || true)
fi

# 2. Check ~/.cache/huggingface/hub directory
if [ -d "$HF_CACHE_DIR" ]; then
    while IFS= read -r item; do
        [ -z "$item" ] && continue
        clean_name=$(basename "$item" | sed 's/^models--//' | sed 's/--/\//g')
        MODEL_PATHS+=("$item")
        MODEL_NAMES+=("HF Cache: $clean_name")
        MODEL_SIZES+=("$(du -sh "$item" 2>/dev/null | cut -f1)")
    done < <(find "$HF_CACHE_DIR" -mindepth 1 -maxdepth 1 -name "models--*" 2>/dev/null || true)
fi

TOTAL_COUNT=${#MODEL_PATHS[@]}

if [ "$TOTAL_COUNT" -eq 0 ]; then
    echo "  [OK] No downloaded models found in ~/models or Hugging Face cache."
    echo "========================================================"
    exit 0
fi

echo "  Found $TOTAL_COUNT model(s):"
echo "--------------------------------------------------------"
for i in "${!MODEL_PATHS[@]}"; do
    num=$((i + 1))
    printf "  %2d) %-50s [%s]\n" "$num" "${MODEL_NAMES[$i]}" "${MODEL_SIZES[$i]}"
    echo "      Path: ${MODEL_PATHS[$i]}"
done
echo "--------------------------------------------------------"

# Non-interactive mode flag
if [[ "${1:-}" == "--list" ]] || [[ "${1:-}" == "-l" ]]; then
    echo "  Run without --list flag to interactively delete models."
    echo "========================================================"
    exit 0
fi

echo ""
echo "Options:"
echo "  - Type 'all' (or 'a') to delete ALL listed models."
echo "  - Type space/comma separated numbers (e.g. '1 3' or '1,3') to delete specific models."
echo "  - Press Enter or type 'q' to cancel."
echo ""
read -rp "Your choice: " choice

choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]' | xargs)

if [ -z "$choice" ] || [ "$choice" == "q" ] || [ "$choice" == "quit" ]; then
    echo "Cancelled. No models were removed."
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
        if [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] && [ "$n" -le "$TOTAL_COUNT" ]; then
            idx=$((n - 1))
            TO_DELETE+=("$idx")
        else
            echo "Invalid selection: '$n'. Skipping."
        fi
    done
fi

if [ "${#TO_DELETE[@]}" -eq 0 ]; then
    echo "No valid models selected for deletion."
    exit 0
fi

echo ""
echo "Deleting selected models..."
for idx in "${TO_DELETE[@]}"; do
    path="${MODEL_PATHS[$idx]}"
    name="${MODEL_NAMES[$idx]}"
    echo "  Removing: $name ($path)"
    rm -rf "$path"
done

echo ""
echo "  [OK] Selected model(s) removed successfully."
echo "========================================================"
