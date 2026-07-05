#!/bin/bash
# ============================================================
# 01_install_dependencies.sh
# Installs llama-cpp-python[server] and huggingface_hub.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Auto-load environment variables
source "$SCRIPT_DIR/00_load_env.sh" 2>/dev/null || true

echo "========================================================"
echo "  Step 1: Install Dependencies"
echo "========================================================"

PYTHON_CMD=""
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python interpreter not found."
    exit 1
fi

echo "  [INFO] Using Python: $PYTHON_CMD ($("$PYTHON_CMD" --version))"

install_package() {
    local pkg_spec=$1
    shift || true

    if command -v uv &> /dev/null && [ -d "$PROJECT_ROOT/.venv" ]; then
        VIRTUAL_ENV="$PROJECT_ROOT/.venv" uv pip install "$pkg_spec" "$@"
    elif "$PYTHON_CMD" -m pip --version &> /dev/null; then
        "$PYTHON_CMD" -m pip install "$pkg_spec" "$@"
    elif "$PYTHON_CMD" -m ensurepip --default-pip &> /dev/null; then
        "$PYTHON_CMD" -m pip install "$pkg_spec" "$@"
    else
        pip install "$pkg_spec" "$@"
    fi
}

if "$PYTHON_CMD" -c "import llama_cpp" &> /dev/null; then
    echo "  [OK] llama-cpp-python is already installed."
else
    echo "  [INFO] Installing llama-cpp-python[server]..."
    install_package "llama-cpp-python[server]" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
    echo "  [OK] llama-cpp-python[server] installed successfully."
fi

if "$PYTHON_CMD" -c "import huggingface_hub" &> /dev/null; then
    echo "  [OK] huggingface_hub is already installed."
else
    echo "  [INFO] Installing huggingface_hub[cli]..."
    install_package "huggingface_hub[cli]"
    echo "  [OK] huggingface_hub installed successfully."
fi

echo ""
echo "  All dependencies satisfied."
echo "========================================================"
echo "  Next: bash scripts/02_download_model.sh"
echo "========================================================"
