#!/bin/bash
# ============================================================
# 00_install_llamacpp.sh
# Auto-detect and install llama.cpp (llama-server) if missing.
# Also installs huggingface_hub[cli] if huggingface-cli is missing.
# Run once before anything else.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="$HOME/bin"
LLAMACPP_RELEASE_URL="https://github.com/ggml-org/llama.cpp/releases/latest/download/llama-server-linux-x86_64"

echo "========================================================"
echo "  Step 0: Install Dependencies"
echo "========================================================"

# ---- 1. llama-server ----------------------------------------
if command -v llama-server &> /dev/null; then
    echo "  [OK] llama-server already on PATH: $(which llama-server)"
else
    echo "  [INFO] llama-server not found. Installing..."
    
    if [[ "$(uname -s)" == "Darwin" ]] && command -v brew &> /dev/null; then
        echo "  [INFO] macOS detected. Installing llama.cpp via Homebrew..."
        brew install llama.cpp
    else
        echo "  [INFO] Linux/other detected. Installing pre-built binary..."
        mkdir -p "$INSTALL_DIR"
        echo "  Downloading from: $LLAMACPP_RELEASE_URL"
        curl -L --progress-bar "$LLAMACPP_RELEASE_URL" -o "$INSTALL_DIR/llama-server"
        chmod +x "$INSTALL_DIR/llama-server"

        # Add ~/bin to PATH in .bashrc if not already there
        if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
            echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
            echo "  [INFO] Added $INSTALL_DIR to PATH in ~/.bashrc"
        fi

        # Make it available in the current session
        export PATH="$INSTALL_DIR:$PATH"
        echo "  [OK] llama-server installed at $INSTALL_DIR/llama-server"
    fi
fi

# ---- 2. huggingface CLI (hf / huggingface-cli) ------------------
PYTHON_CMD=""
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_CMD="$PROJECT_ROOT/.venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

if command -v hf &> /dev/null; then
    echo "  [OK] hf CLI already on PATH"
elif command -v huggingface-cli &> /dev/null; then
    echo "  [OK] huggingface-cli already on PATH"
elif [ -n "$PYTHON_CMD" ] && "$PYTHON_CMD" -c "import huggingface_hub" &> /dev/null; then
    echo "  [OK] huggingface_hub is available in Python environment ($PYTHON_CMD)."
else
    echo "  [INFO] Hugging Face CLI not found. Installing into active Python environment..."
    if command -v uv &> /dev/null && [ -d "$PROJECT_ROOT/.venv" ]; then
        cd "$PROJECT_ROOT" && uv pip install "huggingface_hub[cli]"
    elif [ -n "$PYTHON_CMD" ]; then
        "$PYTHON_CMD" -m pip install "huggingface_hub[cli]"
    else
        echo "WARNING: Python/uv not found on PATH. Please install huggingface_hub manually."
    fi
fi

echo ""
echo "  All dependencies satisfied."
echo "========================================================"
echo "  Next: bash scripts/01_download_model.sh"
echo "========================================================"
