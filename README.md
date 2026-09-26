# LLaMEA Noisy BBOB Optimization Algorithm Evolution

`aad-llm` is a research framework for automated algorithm discovery. It uses
[LLaMEA](https://github.com/XuYuey/LLM-Evolutionary-Algorithm) to evolve Python
implementations of continuous black-box optimizers, evaluates them on BBOB
(Black-Box Optimization Benchmarking) functions with configurable noise, and
then independently compares discovered champions with classical optimizers.

The project is notebook-first: configure an experimental matrix, synthesize
candidate algorithms with an LLM, benchmark saved champions, and analyse the
resulting traces statistically.

## Architecture diagrams

Two complementary, C4-inspired views show the same system at different depths.
“Level 0” and “Level 1” below are project-specific overview/detail labels, not
the standard C4 system-context/container levels.

### Level 0 — Workflow overview

The compact view introduces the main workflows and supporting capabilities.

[![Workflow overview: synthesis, benchmarking, audit and analysis with supporting runtime and persistence](docs/architecture/system_overview.svg)](docs/architecture/system_overview.svg)

[Open full-size overview](docs/architecture/system_overview.svg)

### Level 1 — Detailed system view

The detailed view expands the workflows into their components, relationships,
and code links for an in-depth understanding of the project.

[![Detailed system diagram: synthesis, benchmarking and audit, analysis and transfer, candidate execution, and experiment persistence](docs/architecture/system_diagram.svg)](docs/architecture/system_diagram.svg)

[Open full-size detailed diagram](docs/architecture/system_diagram.svg) ·
[Editable Mermaid source](docs/architecture/system_diagram.mmd) ·
[Context ownership and dependency rules](docs/architecture/system_architecture.md)

Both views preserve the original palette and background. Arrows describe workflow and
data access, not Python imports; analysis is part of benchmarking, not a third
bounded context. Both SVGs render independently of GitHub's theme.

<details>
<summary>View Mermaid diagram source</summary>

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#f2e6ff", "clusterBkg": "#f7f7f7", "clusterBorder": "#dedede", "lineColor": "#333333", "edgeLabelBackground": "#f2e6ff", "fontFamily": "Arial, Helvetica, sans-serif", "primaryTextColor": "#111111"}, "flowchart": {"curve": "basis", "htmlLabels": true, "wrappingWidth": 1000}, "look": "classic", "fontFamily": "Arial, Helvetica, sans-serif", "markdownAutoWrap": false, "themeCSS": ".label, .nodeLabel, .edgeLabel, .cluster-label { font-family: Arial, Helvetica, sans-serif !important; }"}}%%
flowchart TD

subgraph group_synthesis["Algorithm synthesis"]
  node_campaign["Synthesis campaign<br/>[run.py]"]
  node_campaign_plan["Campaign planning<br/>[plan.py]"]
  node_synth_config["Synthesis configuration<br/>[repository.py]"]
  node_single_synthesis["Synthesis session<br/>[run.py]"]
end

subgraph group_runtime["Candidate execution"]
  node_llamea["LLaMEA adapter<br/>[runner.py]"]
  node_prompts["Prompt construction<br/>[builder.py]"]
  node_llm_client["LLM provider client<br/>[client.py]"]
  node_candidate_evaluator["Candidate evaluator<br/>[evaluator.py]"]
  node_guarded_executor["Guarded execution<br/>[executor.py]"]
  node_problem_factory["BBOB problem factory<br/>[factory.py]"]
  node_noise_model["Noise model<br/>[noise_model.py]"]
end

subgraph group_benchmark["Benchmarking and audit"]
  node_evaluation["Champion and baseline trials<br/>[run.py]"]
  node_baselines["Classical optimizers<br/>[baselines.py]"]
  node_champions["Champion selection"]
  node_audit["Coverage and run audit<br/>[audit.py]"]
end

subgraph group_analysis["Analysis and transfer"]
  node_analysis["Statistical analysis<br/>[report.py]"]
  node_analysis_services["ECDF and statistics<br/>[ecdf.py]"]
  node_transfer["Noise and transfer analysis<br/>[transfer.py]"]
  node_figures["Analysis figures<br/>[summary.py]"]
end

subgraph group_persistence["Experiment persistence"]
  node_code_store["Candidate code store<br/>[repository.py]"]
  node_synthesis_store[("Synthesis records<br/>[repository.py]")]
  node_database[("SQLite database<br/>[engine.py]")]
  node_trace_repo["Benchmark traces"]
end

node_researcher(("Notebook researcher"))
node_llm_service{{"LLM provider"}}

node_researcher -->|"starts campaign"| node_campaign
node_researcher -->|"runs trials"| node_evaluation
node_researcher -->|"audits coverage"| node_audit
node_researcher -->|"analyses results"| node_analysis
node_campaign -->|"plans matrix"| node_campaign_plan
node_campaign -->|"loads settings"| node_synth_config
node_campaign -->|"dispatches sessions"| node_single_synthesis
node_single_synthesis -->|"runs synthesis"| node_llamea
node_llamea -->|"builds prompts"| node_prompts
node_llamea -->|"requests generations"| node_llm_client
node_llm_client -->|"calls provider"| node_llm_service
node_llamea -->|"evaluates candidates"| node_candidate_evaluator
node_candidate_evaluator -->|"executes candidate"| node_guarded_executor
node_candidate_evaluator -->|"creates objective"| node_problem_factory
node_problem_factory -->|"applies noise"| node_noise_model
node_single_synthesis -->|"persists code"| node_code_store
node_single_synthesis -->|"records iterations"| node_synthesis_store
node_evaluation -->|"runs baselines"| node_baselines
node_evaluation -->|"writes traces"| node_trace_repo
node_champions -->|"reads candidates"| node_synthesis_store
node_audit -->|"checks trace coverage"| node_trace_repo
node_analysis -->|"reads traces"| node_trace_repo
node_analysis -->|"computes metrics"| node_analysis_services
node_analysis -->|"presents results"| node_figures
node_transfer -.->|"writes isolated traces"| node_trace_repo

click node_campaign "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/application/campaign/run.py"
click node_campaign_plan "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/application/campaign/plan.py"
click node_synth_config "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/infra/storage/synthesis_config/repository.py"
click node_single_synthesis "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/application/synthesis/run.py"
click node_llamea "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/infra/engines/llamea/runner.py"
click node_prompts "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/infra/engines/llamea/prompts/builder.py"
click node_llm_client "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/infra/llm/client.py"
click node_candidate_evaluator "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/infra/engines/llamea/evaluator.py"
click node_guarded_executor "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/shared/infra/execution/executor.py"
click node_problem_factory "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/shared/infra/problems/factory.py"
click node_noise_model "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/shared/domain/noise_model.py"
click node_code_store "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/infra/storage/code/repository.py"
click node_synthesis_store "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/evolution/infra/storage/synthesis/repository.py"
click node_database "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/shared/infra/database/engine.py"
click node_evaluation "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/application/evaluation/run.py"
click node_baselines "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/infra/solvers/baselines.py"
click node_champions "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/application/select_champions.py"
click node_trace_repo "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/infra/io/trace_repository.py"
click node_audit "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/application/evaluation/audit.py"
click node_analysis "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/application/analysis/report.py"
click node_analysis_services "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/domain/services/ecdf.py"
click node_transfer "https://github.com/nicola-ibrahim/aad_llm/blob/main/src/benchmarking/domain/services/transfer.py"
click node_figures "https://github.com/nicola-ibrahim/aad_llm/blob/main/notebooks/analysis/plotting/summary.py"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_campaign,node_campaign_plan,node_synth_config,node_single_synthesis toneBlue
class node_llamea,node_prompts,node_llm_client,node_candidate_evaluator,node_guarded_executor,node_problem_factory,node_noise_model toneAmber
class node_evaluation,node_baselines,node_champions,node_audit toneMint
class node_analysis,node_analysis_services,node_transfer,node_figures toneRose
class node_code_store,node_synthesis_store,node_database,node_trace_repo,node_researcher,node_llm_service toneIndigo
```

</details>

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
5. [05_analysis.ipynb](notebooks/analysis/05_analysis.ipynb) — native reliability
   tables and the three primary thesis PNGs.
6. [06_performance_profiles.ipynb](notebooks/analysis/06_performance_profiles.ipynb)
   — exploratory performance, strategy ablations, and detailed convergence/ECDF sweeps.
7. [07_generalization.ipynb](notebooks/analysis/07_generalization.ipynb) — frozen-champion
   noise robustness and cross-function transfer.

The three analysis notebooks run independently. Their shared Plotly builders live
in `notebooks/analysis/plotting/`; calculations remain in the domain engines.
Successful PNG exports are cached per workflow and per figure. Run only the
sections you need, use condition filters for smaller sweeps, and set
`FORCE_EXPORT = True` only when you deliberately want to regenerate images.

Noise robustness and cross-function generalization are separate secondary
analyses, outside the native champion ranking. Cross-function evaluation is
opt-in, uses frozen clean champions, and writes isolated transfer traces.
See [the evaluation protocol](docs/transfer_evaluation.md) for execution switches,
scoring, storage, and thesis interpretation.

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
                   LLaMEA adapter, prompt construction,
                   and synthesis persistence
  benchmarking/    champion/baseline evaluation, trace processing, ECDF and
                   statistical analysis services
  shared/          shared BBOB/noise mathematics, objective capabilities, SQLite,
                   IOH adapters, and guarded algorithm execution
notebooks/         interactive research workflow and figure/report presentation
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
