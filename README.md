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
   bash scripts/01_setup_env.sh
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
   bash scripts/01_setup_env.sh
   ```
2. **Start the Server**:
   ```bash
   bash scripts/03_serve_llm.sh
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
sbatch scripts/04_slurm_submit.sh
```

## Database Migrations
We use a relational SQLite database schema with a split-storage strategy (storing lightweight metadata in SQLite and saving heavy Python code files as disk blobs). 

If you make modifications to the data schemas, you can trigger database initialization or schema migrations directly from the command line:
```bash
# Run migrations on the default database (experiments/results.db)
poe migrate

# Or target a custom database file
poe migrate --db-path path/to/your/custom_database.db
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
  - `01_setup_env.sh` — Initializes environment, checks env vars, and syncs dependencies via uv.
  - `02_download_llm.sh` — Downloads GGUF model files from Hugging Face.
  - `03_serve_llm.sh` — Starts the local model server.
  - `04_slurm_submit.sh` — Batch job script for SLURM cluster execution.
  - `cleanup_models.sh` — Utility to list and interactively delete cached/downloaded models.
  - `stop_server.sh` — Utility to stop running model server instances.
  - `migrate.sh` — Utility script to check schema and run database migrations.
- `src/` — Source code library:
  - `llm/` — LLM provider bindings (`providers.py`) and prompt constants (`prompts.py`).
  - `problems/` — Additive Gaussian noise wrapper around BBOB functions (`bbob.py`).
  - `core/` — Sandbox execution (`evaluator.py`, `executor.py`) and evolutionary runner (`runner.py`).
  - `schema/` — Pydantic models and data schemas.
  - `storage/` — Results summary persistence/loading, SQLite relational mapper, and code blob writer.
- `experiments/` — Evolved python scripts containing the best optimization algorithms, conversation history, and evaluation results.
- `logs/` — Execution logs and model server outputs.

