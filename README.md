# LLaMEA Noisy BBOB Optimization Algorithm Evolution

This repository implements a framework to automatically evolve novel, continuous black-box optimization algorithms tailored to handle additive Gaussian noise on BBOB (Black-Box Optimization Benchmarking) landscapes using LLaMEA (Large Language Model Evolutionary Algorithm).

The actual evolution experiments run on the Paderborn University remote server, with this codebase acting as the unified definition of the task prompts, noise injection layers, and evaluation routines.

## Installation

This project is managed with [uv](https://github.com/astral-sh/uv). 

To install the project and its dependencies:
```bash
uv sync --all-extras
```

## Running the Notebooks

Launch Jupyter Notebook:
```bash
uv run jupyter notebook
```
Then navigate to [server/notebooks/01_interactive_workspace.ipynb](server/notebooks/01_interactive_workspace.ipynb) to configure, verify, and prototype your setup interactively.

## Starting the Local Model Server

To run the optimization pipeline locally without relying on external tools like LMStudio, this project includes a built-in automated LLM server (powered by `llama.cpp` and `huggingface_hub`).

To install all dependencies, automatically download the configured model, and start the local server in the background, simply run:
```bash
./start_llm.sh
```

**Changing the Model**: By default, the system uses the `Qwen2.5-Coder-7B-Instruct-GGUF` model. To use a different model (e.g., the smaller 1.5B version for fast local testing), you only need to edit the variables in your `.env` file. 
For a complete explanation of the configuration variables and ready-to-use model presets, please refer to the detailed guide at [server/docs/MODEL_CONFIGURATION.md](server/docs/MODEL_CONFIGURATION.md).

## Project Structure

- `pyproject.toml` — Dependency and packaging configuration.
- `src/aad_llm/` — Source code library:
  - `prompts.py` — Pythonic string constants (`TASK_PROMPT_TEMPLATE`, `EXAMPLE_PROMPT`, `FORMAT_PROMPT`) representing evolution prompts.
  - `noisy_bbob.py` — Additive Gaussian noise wrapper around BBOB problems.
  - `evaluator.py` — Evaluation hook that executes LLM-generated code safely within a sandbox.
  - `runner.py` — Definition of helper functions to execute LLaMEA iterations.
  - `main_experiment.py` — Multi-repetition experiment loop with resumption checkpointing.
- `server/` — Deployment files for the UPB Jupyter Server and HPC SLURM cluster:
  - `README.md` — Complete step-by-step setup guide for the server environment.
  - `docs/MODEL_CONFIGURATION.md` — Guide to configuring custom models and quantizations.
  - `notebooks/` — Interactive workspace and thesis stats results dashboard.
  - `scripts/` — Model installation, download, serving, and SLURM submission scripts.
- `generated_algorithms/` — Evolved python scripts containing the best optimization algorithms found.
- `logs/` — Directory containing logs of LLaMEA evolution history and model server outputs.

## Running the Command Line Script

After executing `uv sync --all-extras`, the script is configured by editing the variables in the `EXPERIMENT CONFIGURATION` block inside `src/aad_llm/main.py`:

```python
RUN_ALL_PROBLEMS = False  # Set to True to evolve all 24 problems sequentially
PROBLEM_ID = 1            # BBOB Problem ID (1-24) to run when RUN_ALL_PROBLEMS is False
DIM = 3                   # Search space dimensionality (e.g. 3 or 5)
...
```

Once configured, trigger execution using the registered command:
```bash
uv run aad-llm
```

Or execute it directly using python:
```bash
uv run python src/aad_llm/main.py
```
