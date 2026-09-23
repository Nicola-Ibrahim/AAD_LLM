# LLaMEA Noisy BBOB Optimization Algorithm Evolution

`aad-llm` is a research framework for automated algorithm discovery. It uses
[LLaMEA](https://github.com/XuYuey/LLM-Evolutionary-Algorithm) to evolve Python
implementations of continuous black-box optimizers, evaluates them on BBOB
(Black-Box Optimization Benchmarking) functions with configurable noise, and
then independently compares discovered champions with classical optimizers.

The project is notebook-first: configure an experimental matrix, synthesize
candidate algorithms with an LLM, benchmark saved champions, and analyse the
resulting traces statistically.

## What happens in an experiment

```text
Experiment configuration
  -> LLM generates or improves an optimizer implementation
  -> candidate executes in a guarded evaluation harness
  -> returned solution is validated and scored on the clean BBOB objective
  -> code and iteration telemetry are persisted
  -> best champion is independently benchmarked against CMA-ES, DE, and PSO
  -> ECDF metrics, hypothesis tests, and figures are produced
```

Generated algorithms receive only a black-box objective function, an evaluation
budget, and the problem dimension. The evaluator validates the returned point's
shape and bounds, then re-evaluates it on the un-noised objective. This makes
selection depend on the true quality of the returned solution rather than a
lucky noisy observation or a self-reported fitness value.

## Quick start

Requirements: Python 3.11–3.13 and either `uv` (recommended) or a standard
Python environment. A configured LLM provider is also required for synthesis.

### Local development with `uv`

```bash
uv sync --all-extras
uv run jupyter notebook
```

### Standard Python or remote Jupyter server

```bash
bash scripts/env.sh
jupyter notebook
```

Open the notebooks in the order below. The synthesis configuration has a large
default experiment matrix and a nominal one-million-evaluation candidate budget;
adjust `configs/synthesis.toml` before running a quick experiment.

## Notebook workflow

1. [01_noise.ipynb](notebooks/01_noise.ipynb) — inspect BBOB landscapes and
   heteroscedastic noise behaviour.
2. [02_synthesis.ipynb](notebooks/02_synthesis.ipynb) — run LLaMEA synthesis
   campaigns across the configured problem matrix.
3. [03_evaluation.ipynb](notebooks/03_evaluation.ipynb) — independently run
   champions and classical baselines over repeated trials.
4. [04_audit.ipynb](notebooks/04_audit.ipynb) — audit matrix coverage, pending
   work, failures, and resumable runs.
5. [05_analysis.ipynb](notebooks/05_analysis.ipynb) — perform non-parametric
   statistical analysis and create thesis/publication figures.

## Configuration

| File | Purpose |
| --- | --- |
| `configs/synthesis.toml` | Synthesis matrix, noise conditions, prompt strategies, budgets, retries, and process concurrency. |
| `configs/benchmark.toml` | Independent trial count, evaluation budget multiplier, timeout, and classical baselines. |
| `configs/problems.toml` | BBOB problem descriptions and groupings. |
| `configs/llms.toml` | Available local-model presets. |
| `.env` | Active LLM provider and local model/server settings. |

The default synthesis matrix covers BBOB functions 1, 8, 11, 15, and 21 across
2D, 3D, 5D, and 10D; clean and heteroscedastic-noise conditions; explicit and
implicit prompts; and several prompt strategies.

## LLM providers and local server

The LLM client supports configured providers, including OpenAI-compatible APIs
and local model servers. To use the bundled `llama.cpp` workflow:

```bash
bash scripts/env.sh
bash scripts/llm.sh start
```

Use `bash scripts/llm.sh` for the available model-server and model-download
commands. See [model configuration](docs/configuration/model_configuration.md)
for provider settings and presets.

## Persistence, recovery, and maintenance

- SQLite metadata is stored at `data/db.sqlite3` by default.
- Generated candidate source files and evolution checkpoint state are stored
  beneath `data/`.
- Synthesis checkpoints support warm-starting interrupted experiments; completed
  sessions clean up their checkpoint archive.
- Benchmark traces and analysis outputs are written under `results/`.

Manage the database or migration state with:

```bash
bash scripts/db.sh
bash scripts/db.sh upgrade
```

Clean generated artifacts and logs with:

```bash
bash scripts/clean.sh
```

## Project layout

```text
src/
  evolution/       LLM-driven algorithm synthesis: domain rules, campaigns,
                   LLaMEA adapter, BBOB/noise adapter, prompt construction,
                   and synthesis persistence
  benchmarking/    champion/baseline evaluation, trace processing, ECDF and
                   statistical analysis services
  shared/          configuration, SQLite infrastructure, and guarded dynamic
                   algorithm execution
notebooks/         interactive research workflow
configs/           synthesis, benchmark, problem, and LLM settings
data/              SQLite database, generated code, and checkpoints
results/           benchmark traces, tables, and figures
scripts/           environment, model-server, database, and cleanup helpers
tests/             unit and integration tests
docs/              architecture and methodology documentation
```

## Testing and quality checks

```bash
uv run pytest
uv run ruff check .
```

If Poe the Poet is installed, the equivalent project tasks are `poe test`,
`poe lint`, and `poe check`.

## Further documentation

- [System architecture](docs/architecture/system_architecture.md)
- [Execution and recovery flow](docs/architecture/execution_flow.md)
- [LLaMEA adapter architecture](docs/architecture/llamea_architecture.md)
- [Evaluator methodology](docs/evaluator_methodology.md)
