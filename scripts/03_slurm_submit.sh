#!/bin/bash
# ============================================================
# 03_slurm_submit.sh
# SLURM Job Submission Script for HPC Clusters.
# Automatically spins up the local inference server, runs the
# experiment, and cleans up the server upon completion.
# ============================================================
#
# Submit to queue:
#   sbatch scripts/03_slurm_submit.sh
#
# Check job status:
#   squeue --me
# ============================================================

#SBATCH --job-name=llamea_bbob
#SBATCH --output=logs/slurm_%j.log
#SBATCH --error=logs/slurm_%j.log
#SBATCH --time=24:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=16
#SBATCH --nodes=1

set -euo pipefail

# Print current node details
echo "Job started on: $(date)"
echo "Running on node: $(hostname)"
echo "CPUs allocated: $SLURM_CPUS_PER_TASK"
echo "Allocated memory: 32G"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PORT=8080

# 1. Load any system modules if needed (e.g. if the cluster uses modules)
# module load python || true



# Function to load a variable from environment or .env
load_env_var() {
    local var_name=$1
    local default_val=${2:-""}

    if [ -n "${!var_name:-}" ]; then
        echo "${!var_name}"
        return
    fi

    local env_file="$PROJECT_ROOT/.env"
    if [ -f "$env_file" ]; then
        local val
        val=$(grep -E "^${var_name}=" "$env_file" | head -n 1 | cut -d'=' -f2- | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        if [ -n "$val" ]; then
            echo "$val"
            return
        fi
    fi
    echo "$default_val"
}

MODEL_FILE=$(load_env_var "HF_FILE" "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf")
MODEL_PATH="$HOME/models/$MODEL_FILE"

# 3. Verify model file exists; if not, automatically download it
if [ ! -f "$MODEL_PATH" ]; then
    echo "  [INFO] Model file not found at: $MODEL_PATH"
    echo "  [INFO] Triggering automatic download on compute node..."
    bash scripts/01_download_model.sh
fi

# 4. Start local llama-server on the allocated compute node
echo "Starting llama.cpp server in the background..."
mkdir -p logs

llama-server \
    -m "$MODEL_PATH" \
    --port "$PORT" \
    -c 8192 \
    --threads "$SLURM_CPUS_PER_TASK" \
    > logs/model_server_slurm.log 2>&1 &

SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Clean up server on job exit (success, failure, or timeout cancellation)
cleanup() {
    echo "Cleaning up local model server (PID $SERVER_PID)..."
    kill "$SERVER_PID" || true
    echo "Job finished on: $(date)"
}
trap cleanup EXIT

# 5. Wait for the model server to become responsive
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

# 6. Run the experiment synchronously within the SLURM job allocation
python src/main_experiment.py

echo "LLaMEA experiment run completed successfully!"
