# LLaMEA Noisy BBOB Optimization Algorithm Evolution

This repository implements a framework to automatically evolve novel, continuous black-box optimization algorithms tailored to handle additive Gaussian noise on BBOB (Black-Box Optimization Benchmarking) landscapes using LLaMEA (Large Language Model Evolutionary Algorithm).

The evolution experiments run either locally or on remote HPC cluster environments, using a unified definition of task prompts, noise injection layers, and evaluation routines.

## Installation

This project is managed with [uv](https://github.com/astral-sh/uv). 

To install the project and its dependencies:
```bash
uv sync --all-extras
```

Copy the environment configuration template to create your `.env` file:
```bash
cp .env.example .env
```

## Running the Notebooks

Launch Jupyter Notebook:
```bash
uv run jupyter notebook
```
Then navigate to [notebooks/01_interactive_workspace.ipynb](notebooks/01_interactive_workspace.ipynb) to configure, verify, and prototype your setup interactively.

## Starting the Local Model Server

To run the optimization pipeline locally without relying on external APIs or tools like LMStudio, this project includes a built-in automated LLM server (powered by `llama.cpp` and `huggingface_hub`).

1. **Install Server Dependencies**:
   ```bash
   bash scripts/00_install_llamacpp.sh
   ```
2. **Download & Start the Server**:
   ```bash
   bash scripts/02_serve_model.sh
   ```

**Changing the Model**: By default, the system uses the `Qwen2.5-Coder-7B-Instruct-GGUF` model. To use a different model (e.g., the smaller 1.5B version for fast local testing), edit the variables in your `.env` file. 
For a complete explanation of configuration variables and ready-to-use presets, refer to [docs/MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md).

## Running Experiments

### Background Local Execution
To run the full experiment runner in the background (preventing loss of progress on connection drops):
```bash
bash scripts/03_run_experiment.sh
```

### HPC SLURM Cluster Execution
To submit a batch job on a SLURM cluster:
```bash
sbatch scripts/04_slurm_submit.sh
```

## Project Structure

- `pyproject.toml` — Dependency and packaging configuration.
- `.env` — Local environment variables and model configuration.
- `.env.example` — Environment variable template.
- `docs/` — Documentation:
  - [MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md) — Guide to configuring custom models and quantizations.
- `notebooks/` — Jupyter notebooks:
  - `01_interactive_workspace.ipynb` — Interactive playground & verification.
  - `02_llamea_analysis.ipynb` — Analysis & prototyping notebook.
  - `03_results_dashboard.ipynb` — Stats builder, boxplots, and results dashboard.
- `scripts/` — Execution and orchestration scripts:
  - `00_install_llamacpp.sh` — Compiles/installs llama-server & huggingface-cli.
  - `01_download_model.sh` — Downloads GGUF model files from Hugging Face.
  - `02_serve_model.sh` — Starts the local model server.
  - `03_run_experiment.sh` — Runs experiment loop in background (nohup).
  - `04_slurm_submit.sh` — Batch job script for SLURM cluster execution.
- `src/aad_llm/` — Source code library:
  - `prompts.py` — Task prompts and formatting templates for algorithm evolution.
  - `noisy_bbob.py` — Additive Gaussian noise wrapper around BBOB functions.
  - `evaluator.py` — Sandbox execution and evaluation of LLM-generated code.
  - `runner.py` — Execution logic for LLaMEA evolutionary loop.
  - `main_experiment.py` — Experiment loop with checkpointing.
- `generated_algorithms/` — Evolved python scripts containing the best optimization algorithms.
- `logs/` — Execution logs and model server outputs.

## Running the Command Line Script

After executing `uv sync --all-extras`, configure variables in `src/aad_llm/main.py`:

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
uv run python src/aad_llm/main.py
```
