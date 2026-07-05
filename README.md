# LLaMEA Noisy BBOB Optimization Algorithm Evolution

This repository implements a framework to automatically evolve novel, continuous black-box optimization algorithms tailored to handle additive Gaussian noise on BBOB (Black-Box Optimization Benchmarking) landscapes using LLaMEA (Large Language Model Evolutionary Algorithm).

The evolution experiments run either locally or on remote HPC cluster environments, using a unified definition of task prompts, noise injection layers, and evaluation routines.

## Installation

This project is managed with [uv](https://github.com/astral-sh/uv). 

To install the project and its dependencies using `uv` (recommended):
```bash
uv sync --all-extras
```

Or using standard `pip` (Conda / Jupyter Server):
```bash
# Make sure you are inside the project folder
pip install -r requirements.txt
```

## Environment Configuration (Jupyter Server)

On Jupyter servers, `.env` files are hidden by default in the file browser. Creating a `.env` file is **optional** (all scripts use sensible defaults), but if you wish to set custom variables, you can copy & paste either snippet below:

### Jupyter Notebook Python Cell
Run this code inside any notebook cell to generate `.env` automatically:
```python
# Copy and run in Jupyter Notebook cell:
with open(".env", "w") as f:
    f.write("LLM_PROVIDER=local\n")
    f.write("HF_REPO=Qwen/Qwen2.5-Coder-7B-Instruct-GGUF\n")
    f.write("HF_FILE=qwen2.5-coder-7b-instruct-q4_k_m.gguf\n")
    f.write("LOCAL_LLM_MODEL=qwen2.5-coder-7b-instruct-q4_k_m\n")
    f.write("LOCAL_LLM_BASE_URL=http://localhost:8080/v1\n")
    f.write("LOCAL_LLM_API_KEY=not-needed\n")
```

### Jupyter Terminal Shell Command
Paste into your terminal session to export environment variables directly:
```bash
# Copy and run in Terminal:
export LLM_PROVIDER="local"
export HF_REPO="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
export HF_FILE="qwen2.5-coder-7b-instruct-q4_k_m.gguf"
export LOCAL_LLM_MODEL="qwen2.5-coder-7b-instruct-q4_k_m"
export LOCAL_LLM_BASE_URL="http://localhost:8080/v1"
export LOCAL_LLM_API_KEY="not-needed"
```

## Running the Notebooks

Launch Jupyter Notebook:
```bash
uv run jupyter notebook
```
Then navigate to [notebooks/01_noise_analysis.ipynb](notebooks/01_noise_analysis.ipynb) to configure, verify, and prototype your setup interactively.

## Starting the Local Model Server

To run the optimization pipeline locally without relying on external APIs or tools like LMStudio, this project includes a built-in automated LLM server (powered by `llama.cpp` and `huggingface_hub`).

1. **Load Environment**:
   ```bash
   source scripts/00_load_env.sh
   ```
2. **Install Dependencies**:
   ```bash
   bash scripts/01_install_dependencies.sh
   ```
3. **Start the Server**:
   ```bash
   bash scripts/03_serve_model.sh
   ```

**Changing the Model**: By default, the system uses the `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf` model. To use a different model, edit the variables in your `.env` file or set environment variables via `scripts/00_load_env.sh`. 
For a complete explanation of configuration variables and ready-to-use presets, refer to [docs/MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md).

## Running Experiments

### Local Execution
Execute via `uv`:
```bash
uv run aad-llm
```

### HPC SLURM Cluster Execution
To submit a batch job on a SLURM cluster:
```bash
sbatch scripts/04_slurm_submit.sh
```

## Project Structure

- `pyproject.toml` — Dependency and packaging configuration.
- `requirements.txt` — Standard pip requirements file.
- `.env` — Local environment variables and model configuration.
- `docs/` — Documentation:
  - [MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md) — Guide to configuring custom models and quantizations.
- `notebooks/` — Jupyter notebooks:
  - `00_model_test.ipynb` — Quick diagnostic test for local model server connection and response latency.
  - `01_noise_analysis.ipynb` — Noise injection & interactive analysis notebook.
  - `02_llamea_analysis.ipynb` — Single-problem LLaMEA evolution & verification notebook.
  - `03_batch_llamea_experiment.ipynb` — Multi-problem batch LLaMEA evolution notebook.
  - `04_results_dashboard.ipynb` — Stats builder, boxplots, and results dashboard.
- `scripts/` — Execution and orchestration scripts:
  - `00_load_env.sh` — Exports environment variables explicitly.
  - `01_install_dependencies.sh` — Installs llama-cpp-python & huggingface-hub.
  - `02_download_model.sh` — Downloads GGUF model files from Hugging Face.
  - `03_serve_model.sh` — Starts the local model server.
  - `04_slurm_submit.sh` — Batch job script for SLURM cluster execution.
  - `cleanup_models.sh` — Utility to list and interactively delete cached/downloaded models.
  - `stop_server.sh` — Utility to stop running model server instances.
- `src/` — Source code library:
  - `llm/` — LLM provider bindings (`providers.py`) and prompt constants (`prompts.py`).
  - `problems/` — Additive Gaussian noise wrapper around BBOB functions (`bbob.py`).
  - `core/` — Sandbox execution (`evaluator.py`, `executor.py`) and evolutionary runner (`runner.py`).
  - `analysis/` — Results processing and summary logging (`results.py`).
  - `main.py` & `main_experiment.py` — Execution entrypoints.
- `generated_algorithms/` — Evolved python scripts containing the best optimization algorithms.
- `logs/` — Execution logs and model server outputs.

## Running the Command Line Script

After executing `uv sync --all-extras`, configure variables in `src/main.py`:

```python
RUN_ALL_PROBLEMS = False  # Set to True to evolve all 24 problems sequentially
PROBLEM_ID = 1            # BBOB Problem ID (1-24) to run when RUN_ALL_PROBLEMS is False
DIM = 3                   # Search space dimensionality (e.g. 3 or 5)
```

Trigger execution:
```bash
uv run aad-llm
```

Or execute directly:
```bash
uv run python src/main.py
```
