# LLaMEA Noisy BBOB Optimization Algorithm Evolution

This repository implements a framework to automatically evolve novel, continuous black-box optimization algorithms tailored to handle additive Gaussian noise on BBOB (Black-Box Optimization Benchmarking) landscapes using LLaMEA (Large Language Model Evolutionary Algorithm).

The evolution experiments run either locally or on remote HPC cluster environments, using a unified definition of task prompts, noise injection layers, and evaluation routines.

## Installation & Setup

We support two tracks for environment setup and execution: **Local Development (with `uv`)** and **Jupyter Server / Standard Python (with shell scripts)**.

---

### Track A: Local Development (with `uv`)
Use this track if you are running locally and have [uv](https://github.com/astral-sh/uv) installed.

1. **Install Dependencies:**
   ```bash
   uv sync --all-extras
   ```
2. **Run Jupyter Notebook:**
   ```bash
   uv run jupyter notebook
   ```
3. **Trigger database migrations (if needed):**
   ```bash
   poe migrate
   ```

---

### Track B: Jupyter Server / Standard Python (with shell scripts)
Use this track if you are running on a remote Jupyter Server, custom Conda environment, or don't use `uv`.

1. **Install Dependencies & Configure Environment:**
   Run the dedicated script which automatically checks/creates your `.env` configuration file, checks/syncs dependencies, and installs all packages using your active environment's `pip` or `uv`:
   ```bash
   bash scripts/env.sh
   ```
2. **Run Jupyter Notebook:**
   ```bash
   jupyter notebook
   ```

---

## Running the Notebooks
Open your Jupyter interface and navigate to the `notebooks/` directory to run code:
* [notebooks/00_model_test.ipynb](notebooks/00_model_test.ipynb) — Verify connection to your LLM provider.
* [notebooks/02_llamea_evolution.ipynb](notebooks/02_llamea_evolution.ipynb) — Run single-problem or multi-problem batch LLaMEA evolution.
* [notebooks/03_results_analysis.ipynb](notebooks/03_results_analysis.ipynb) — Query the SQLite database, analyze stats, and plot results.


## Starting the Local Model Server

To run the optimization pipeline locally without relying on external APIs or tools like LMStudio, this project includes a built-in automated LLM server (powered by `llama.cpp` and `huggingface_hub`).

1. **Install Dependencies**:
   ```bash
     bash scripts/env.sh
    ```
 2. **Start the Server**:
    ```bash
    bash scripts/llm_server.sh
   ```

**Changing the Model**: By default, the system uses the `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf` model. To use a different model, edit the variables in your `.env` file. 
For a complete explanation of configuration variables and ready-to-use presets, refer to [docs/MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md).

## Running Experiments

### Notebook-Driven Execution
All experiment execution and analysis are driven interactively from Jupyter Notebooks. The legacy command-line script entrypoint (`src/main.py`) has been removed. 

1. Launch Jupyter Notebook:
   ```bash
   uv run jupyter notebook
   ```
2. Open and run the evolution notebooks sequentially in `notebooks/`.

### HPC SLURM Cluster Execution
To submit a batch job on a SLURM cluster:
```bash
sbatch scripts/slurm_submit.sh
```

## Database Migrations
We use a relational SQLite database schema with a split-storage strategy (storing lightweight metadata in SQLite and saving heavy Python code files as disk blobs). 

If you make modifications to the data schemas, you can trigger database initialization or schema migrations directly from the command line:
```bash
# Run the interactive database management CLI
bash scripts/db.sh

# Or execute a command directly (e.g. upgrade, status, reset)
bash scripts/db.sh upgrade
```

## Project Structure

- `pyproject.toml` — Dependency and packaging configuration.
- `.env` — Local environment variables and model configuration.
- `docs/` — Documentation:
  - [MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md) — Guide to configuring custom models and quantizations.
- `notebooks/` — Jupyter notebooks:
  - `00_model_test.ipynb` — Quick diagnostic test for local model server connection and response latency.
  - `01_noise_analysis.ipynb` — Noise injection & interactive analysis notebook.
  - `02_llamea_evolution.ipynb` — Single and batch multi-problem LLaMEA evolutionary search pipeline.
  - `03_results_analysis.ipynb` — Comprehensive database analysis dashboard, stats builder, and interactive plots.
- `scripts/` — Execution and orchestration scripts:
  - `env.sh` — Initializes environment, checks env vars, and syncs dependencies via uv.
  - `llm_manage.sh` — Interactive CLI to download configured GGUF model, list cached models, or delete them.
  - `llm_server.sh` — Interactive CLI to start, stop, or check the status of the local model server.
  - `slurm_submit.sh` — Batch job script for SLURM cluster execution.
  - `db.sh` — Interactive CLI to manage database migrations, clear table data, reset DB, and show stats.
- `src/` — Source code library:
  - `llm/` — LLM provider bindings (`client.py`) and prompt constants (`prompts.py`).
  - `problems/` — Additive Gaussian noise wrapper around BBOB functions (`bbob.py`).
  - `core/` — Sandbox execution (`evaluator.py`, `executor.py`) and evolutionary runner (`runner.py`).
  - `schema/` — Pydantic models and data schemas.
  - `storage/` — Results summary persistence/loading, SQLite relational mapper, and code blob writer.
- `data/` — Storage folder for runtime files:
  - `db.sqlite3` — The relational SQLite database file storing experiment metrics.
  - `code/` — Evolved python scripts containing the generated optimization algorithms.
- `logs/` — Execution logs and model server outputs.

