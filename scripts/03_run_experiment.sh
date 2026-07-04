#!/bin/bash
# ============================================================
# 03_run_experiment.sh
# Runs the main experiment runner in the background using nohup.
# This keeps the LLaMEA pipeline running if your browser disconnects.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/experiment.pid"
PORT=8080

echo "========================================================"
echo "  Step 3: Run LLaMEA Thesis Experiment (Background)"
echo "========================================================"

mkdir -p "$LOG_DIR"

# 1. Verify model server is reachable
if ! curl -s http://localhost:$PORT/v1/models &>/dev/null; then
    echo "ERROR: Local model server not responding on port $PORT."
    echo "Please start the server first: bash scripts/02_serve_model.sh"
    exit 1
fi

# 2. Setup .env file if it doesn't exist
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "  [INFO] .env not found. Copying .env.example to .env..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
else
    # Make sure LLM_PROVIDER is configured for local server
    if grep -q "LLM_PROVIDER=gemini" "$PROJECT_ROOT/.env"; then
        echo "WARNING: Your .env is set to 'gemini'. To run locally on the server,"
        echo "please update your .env to use 'LLM_PROVIDER=lmstudio' as shown in .env.example."
        exit 1
    fi
fi

# 3. Start background experiment
echo "  [INFO] Launching LLaMEA experiment runner..."
echo "  Log output: $LOG_DIR/experiment_run.log"
echo ""

cd "$PROJECT_ROOT"
nohup python -m aad_llm.main_experiment > "$LOG_DIR/experiment_run.log" 2>&1 &

EXP_PID=$!
echo "$EXP_PID" > "$PID_FILE"
echo "  [OK] Experiment started successfully!"
echo "  Experiment PID: $EXP_PID"
echo "  PID saved to:   $PID_FILE"
echo ""
echo "  Monitor progress: tail -f logs/experiment_run.log"
echo "  Kill experiment:  kill \$(cat logs/experiment.pid)"
echo "========================================================"
