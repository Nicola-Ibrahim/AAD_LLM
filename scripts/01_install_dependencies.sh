#!/bin/bash
# ============================================================
# 01_install_dependencies.sh
# Installs project dependencies, llama-cpp-python[server] and huggingface_hub.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if .env exists, create if not
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "  [INFO] Creating default .env file..."
    printf "%s\n" \
        "# ---------------------------------------------------------------------" \
        "# Local LLaMA.cpp Server / LM Studio Configuration" \
        "# ---------------------------------------------------------------------" \
        "LLM_PROVIDER=local" \
        "HF_REPO=Qwen/Qwen2.5-Coder-7B-Instruct-GGUF" \
        "HF_FILE=qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
        "LOCAL_LLM_MODEL=qwen2.5-coder-7b-instruct-q4_k_m" \
        "LOCAL_LLM_BASE_URL=http://localhost:1234/v1" \
        "LOCAL_LLM_API_KEY=not-needed" \
        "" \
        "# Local Server Runtime Configuration" \
        "LLM_SERVER_HOST=0.0.0.0" \
        "LLM_SERVER_PORT=1234" \
        "LLM_SERVER_N_CTX=8192" \
        "LLM_SERVER_N_THREADS=8" > "$PROJECT_ROOT/.env"
    echo "  [OK] Default .env file created."
fi

# Auto-load environment variables from .env if present
if [ -r "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

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

# Ensure requirements.txt exists or compile it using uv
if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
    if command -v uv &> /dev/null; then
        echo "  [INFO] requirements.txt not found. Using uv to compile dependencies from pyproject.toml..."
        uv pip compile "$PROJECT_ROOT/pyproject.toml" -o "$PROJECT_ROOT/requirements.txt"
    else
        echo "  [WARNING] requirements.txt not found and 'uv' is not installed. Trying to install directly from pyproject.toml..."
    fi
fi

# Install all dependencies from requirements.txt
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "  [INFO] Installing dependencies from requirements.txt..."
    if command -v uv &> /dev/null && [ -d "$PROJECT_ROOT/.venv" ]; then
        VIRTUAL_ENV="$PROJECT_ROOT/.venv" uv pip install -r "$PROJECT_ROOT/requirements.txt"
    elif "$PYTHON_CMD" -m pip --version &> /dev/null; then
        "$PYTHON_CMD" -m pip install -r "$PROJECT_ROOT/requirements.txt"
    else
        pip install -r "$PROJECT_ROOT/requirements.txt"
    fi
elif [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "  [INFO] Installing dependencies from pyproject.toml..."
    if command -v uv &> /dev/null && [ -d "$PROJECT_ROOT/.venv" ]; then
        VIRTUAL_ENV="$PROJECT_ROOT/.venv" uv pip install -e "$PROJECT_ROOT"
    elif "$PYTHON_CMD" -m pip --version &> /dev/null; then
        "$PYTHON_CMD" -m pip install "$PROJECT_ROOT"
    else
        pip install "$PROJECT_ROOT"
    fi
else
    echo "  [ERROR] Neither requirements.txt nor pyproject.toml found."
    exit 1
fi

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
