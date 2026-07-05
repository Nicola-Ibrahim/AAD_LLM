#!/bin/bash
# ============================================================
# 00_install_llamacpp.sh
# Installs llama-cpp-python[server] (pure Python OpenAI-compatible
# inference server) and huggingface_hub for model downloads.
# Run once before anything else.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================================"
echo "  Step 0: Install Dependencies"
echo "========================================================"

# ---- 1. Resolve Python command ---------------------------------
PYTHON_CMD=""
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python interpreter not found. Please install Python 3.8+."
    exit 1
fi

echo "  [INFO] Using Python: $PYTHON_CMD ($("$PYTHON_CMD" --version))"

# ---- Helper: Install package robustly (uv / pip / ensurepip) ------
install_package() {
    local pkg_spec=$1
    shift || true

    if command -v uv &> /dev/null; then
        echo "  [INFO] Installing $pkg_spec using uv..."
        if [ -d "$PROJECT_ROOT/.venv" ]; then
            VIRTUAL_ENV="$PROJECT_ROOT/.venv" uv pip install "$pkg_spec" "$@"
        else
            uv pip install "$pkg_spec" "$@"
        fi
    elif "$PYTHON_CMD" -m pip --version &> /dev/null; then
        echo "  [INFO] Installing $pkg_spec using pip..."
        "$PYTHON_CMD" -m pip install "$pkg_spec" "$@"
    elif "$PYTHON_CMD" -m ensurepip --default-pip &> /dev/null && "$PYTHON_CMD" -m pip --version &> /dev/null; then
        echo "  [INFO] Installed pip via ensurepip. Installing $pkg_spec..."
        "$PYTHON_CMD" -m pip install "$pkg_spec" "$@"
    elif command -v pip3 &> /dev/null; then
        echo "  [INFO] Installing $pkg_spec using pip3..."
        pip3 install "$pkg_spec" "$@"
    elif command -v pip &> /dev/null; then
        echo "  [INFO] Installing $pkg_spec using pip..."
        pip install "$pkg_spec" "$@"
    else
        echo "ERROR: Unable to find pip or uv to install $pkg_spec."
        echo "Please install pip or uv manually."
        exit 1
    fi
}

# ---- 2. llama-cpp-python[server] --------------------------------
# Pure Python OpenAI-compatible inference server — no C++ binary needed.
if "$PYTHON_CMD" -c "import llama_cpp" &> /dev/null; then
    echo "  [OK] llama-cpp-python is already installed."
else
    echo "  [INFO] Installing llama-cpp-python[server]..."
    install_package "llama-cpp-python[server]" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
    echo "  [OK] llama-cpp-python[server] installed successfully."
fi

# ---- 3. huggingface_hub (for model downloads) -------------------
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
echo "  Next: bash scripts/01_download_model.sh"
echo "========================================================"
