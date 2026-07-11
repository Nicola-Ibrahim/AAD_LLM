#!/bin/bash
# ============================================================
# slurm_submit.sh
# SLURM Job Submission Script for HPC Clusters.
# Automatically spins up the local inference server, runs the
# experiment, and cleans up the server upon completion.
# ============================================================
#
# Submit to queue:
#   sbatch scripts/slurm_submit.sh
# ============================================================

#SBATCH --job-name=llamea_bbob
#SBATCH --output=logs/slurm_%j.log
#SBATCH --error=logs/slurm_%j.log
#SBATCH --time=24:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=16
#SBATCH --nodes=1

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Auto-load environment variables from .env if present
if [ -r "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

MODEL_FILE="${HF_FILE:-qwen2.5-coder-1.5b-instruct-q4_k_m.gguf}"
MODEL_PATH="$HOME/models/$MODEL_FILE"

HOST="${LLM_SERVER_HOST:-0.0.0.0}"
PORT="${LLM_SERVER_PORT:-1234}"
N_CTX="${LLM_SERVER_N_CTX:-8192}"
N_THREADS="${LLM_SERVER_N_THREADS:-${SLURM_CPUS_PER_TASK:-8}}"

echo "Job started on: $(date)"
echo "Running on node: $(hostname)"
echo "CPUs allocated: ${SLURM_CPUS_PER_TASK:-16}"

if [ ! -f "$MODEL_PATH" ]; then
    echo "  [INFO] Model file not found at: $MODEL_PATH"
    bash scripts/llm_manage.sh download
fi

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

echo "Starting llama-cpp-python server on $HOST:$PORT (n_ctx=$N_CTX, n_threads=$N_THREADS)..."
mkdir -p logs

"$PYTHON_CMD" -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --host "$HOST" \
    --port "$PORT" \
    --n_ctx "$N_CTX" \
    --n_threads "$N_THREADS" \
    > logs/model_server_slurm.log 2>&1 &

SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

cleanup() {
    echo "Cleaning up local model server (PID $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null || true
    echo "Job finished on: $(date)"
}
trap cleanup EXIT

echo -n "Waiting for server to become responsive"
for i in {1..30}; do
    if curl -s "http://localhost:$PORT/v1/models" &>/dev/null; then
        echo ""
        echo "Server is ready! Starting experiment..."
        break
    fi
    echo -n "."
    sleep 2
done

"$PYTHON_CMD" src/main.py

echo "LLaMEA experiment run completed successfully!"
