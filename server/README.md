# 🖥️ UPB Jupyter Server & HPC Cluster Execution Guide

This folder contains the complete toolset, orchestration scripts, and notebooks to execute LLaMEA-driven evolution of black-box optimization algorithms on noisy BBOB functions using a local LLM server.

Rather than relying on cloud APIs, the server executes models locally via a background `llama-server` (`llama.cpp`), downloading files directly from Hugging Face.

---

## 📁 Directory Layout

```
server/
├── README.md                       # Main manual (this file)
├── .env.server.example             # Template for local cluster variables
├── docs/
│   └── MODEL_CONFIGURATION.md      # Detailed custom model and quantization guide
├── notebooks/
│   ├── 01_interactive_workspace.ipynb # Verification, playground, and manual prototyping
│   └── 02_results_dashboard.ipynb  # Stats builder, boxplots, and algorithm inspector
└── scripts/
    ├── 00_install_llamacpp.sh      # Compiles/installs llama-server & huggingface-cli
    ├── 01_download_model.sh        # Pulls GGUF files dynamically from Hugging Face
    ├── 02_serve_model.sh           # Starts the local model server (with auto-download)
    ├── 03_run_experiment.sh        # Executes LLaMEA experiment loop in background (nohup)
    └── 04_slurm_submit.sh          # Batch job configuration for cluster allocations
```

---

## 🚀 Setup & Running on Jupyter Server (CPU-only)

Follow these steps sequentially to setup and run interactively on the Jupyter server:

### Step 1: Install Dependencies
Open a Terminal in Jupyter and run the installer:
```bash
bash server/scripts/00_install_llamacpp.sh
```
*This downloads the latest pre-compiled `llama-server` binary to `~/bin/` and configures it in your `PATH`.*

### Step 2: Configure Environment
Copy the environment variables template to your root folder:
```bash
cp server/.env.server.example .env
```
*Open `.env` in your Jupyter editor and verify `LLM_PROVIDER=lmstudio` is active.*

### Step 3: Launch Local Model Server
Start the background model inference server:
```bash
bash server/scripts/02_serve_model.sh
```
> **Note:** If the configured model is missing from `~/models/`, this script will automatically trigger the download for you from Hugging Face before starting the server.

### Step 4: Verify & Prototype Interactively
Open [server/notebooks/01_interactive_workspace.ipynb](notebooks/01_interactive_workspace.ipynb) in Jupyter and execute the cells. This validates that:
1. The model server is responding on localhost.
2. The BBOB objective calculations work correctly.
3. Plotly graphics render successfully.

### Step 5: Start Experiment Run (Background)
To run the full LLaMEA experiment loop without keeping your browser window open, launch the background run script:
```bash
bash server/scripts/03_run_experiment.sh
```
*This runs the experiment runner inside a background `nohup` process. It will continue running even if you log out or disconnect.*

---

## ⚙️ How to Change or Customize the Model

You do **not** need to edit any `.sh` shell scripts to work with different models. All scripts read variables directly from your root `.env` file:

```ini
# Config variables inside .env
HF_REPO=Qwen/Qwen2.5-Coder-7B-Instruct-GGUF
HF_FILE=qwen2.5-coder-7b-instruct-q4_k_m.gguf
LLM_STUDIO_MODEL=qwen2.5-coder-7b-instruct-q4_k_m
```

For full details on configuring variables, presets for other model sizes, and a guide to choosing the correct GGUF quantization level, read the **[docs/MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md)** guide.

---

## ⚡ Running on a SLURM Cluster Node

If you are running the experiment on an HPC cluster node using SLURM batch job submission:

1.  Follow **Step 2** to copy and configure your `.env` variables.
2.  Submit the job to the queue:
    ```bash
    sbatch server/scripts/04_slurm_submit.sh
    ```
*This handles everything automatically: it allocates the resources, downloads the model if missing, starts the model server, executes the experiment loop synchronously, and shuts down the model server when done.*

---

## 📊 Monitoring and Visualising Results

*   **Console Logs**: Check the LLaMEA runner output live by running:
    ```bash
    tail -f logs/experiment_run.log
    ```
*   **Automatic Resuming**: Progress checkpoints are saved dynamically to `results/bbob_<id>_rep_<rep>.json`. If a run is interrupted, it will automatically resume from the last completed repetition.
*   **Thesis Results Dashboard**: Open [server/notebooks/02_results_dashboard.ipynb](notebooks/02_results_dashboard.ipynb) to view statistics tables, print AOCC scores, render publication-ready boxplots, and review the code of the best algorithms.
