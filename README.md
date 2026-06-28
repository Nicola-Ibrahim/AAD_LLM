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

Launch Jupyter Notebook locally:
```bash
uv run jupyter notebook
```
Then navigate to `notebooks/01_llamea_bbob.ipynb` to configure and prototype your setup.

## Project Structure

- `pyproject.toml` — Dependency and packaging configuration.
- `src/aad_llm/` — Source code library:
  - `prompts.py` — Pythonic string constants (`TASK_PROMPT_TEMPLATE`, `EXAMPLE_PROMPT`, `FORMAT_PROMPT`) representing evolution prompts.
  - `noisy_bbob.py` — Additive Gaussian noise wrapper around BBOB problems.
  - `evaluator.py` — Evaluation hook that executes LLM-generated code safely within a sandbox.
  - `runner.py` — Definition of helper functions to execute LLaMEA iterations.
  - `main.py` — Command-line entrypoint for execution.
- `generated_algorithms/` — Evolved python scripts containing the best optimization algorithms found.
- `logs/` — Directory containing experiment logs of LLaMEA evolution history.

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
