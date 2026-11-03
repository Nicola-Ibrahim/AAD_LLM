# AAD_LLM project guidance

## Goal and context

AAD_LLM uses LLaMEA and LLMs to synthesize Python optimizers, benchmarks fixed
champions on noisy BBOB problems, and analyses recorded results. Preserve
reproducibility, scientific validity and recoverable experiments while improving
the software. Development agents are separate from synthesis workers and studied LLMs.

This is a Python modular monolith with notebook entry points and practical DDD /
hexagonal boundaries. There is currently no FastAPI server, frontend, Datadog
integration or production deployment target. Do not describe proposals as implemented.

## Project structure and boundaries

| Location | Owns |
| --- | --- |
| `src/evolution/` | Synthesis, campaigns, prompts, candidate feedback and scoring policy |
| `src/benchmark/` | Champion selection, benchmark trials, resumption and analysis |
| `src/shared/` | Common scientific/runtime capabilities and supporting adapters |
| `notebooks/` | Research entry points; `analysis/plotting/` owns Plotly presentation and image export |
| `tests/`, `scripts/`, `docs/` | Verification, operational helpers and application documentation |
| `.agents/skills/`, `.codex/` | Reusable agent procedures; role definitions, prompts and task records |

Within each context, application code coordinates injected collaborators, domain
code owns scientific rules, and infrastructure owns files, databases and external
systems. Core application/domain code must not import infrastructure or the other
context. Shared code must not import either context. The documented read-only
synthesis-data integration in benchmark infrastructure is an explicit exception.

Use the [documentation map](docs/README.md) for context-specific reading and the
[architecture](docs/architecture/system_architecture.md) for ownership and DI.
Report discrepancies between documentation and implementation before changing
scientific behavior.

## Setup, run and checks

Run from the repository root. Dependencies and tasks are defined in `pyproject.toml`.

| Purpose | Command |
| --- | --- |
| Install locked dependencies, dev tools and notebooks | `uv sync --locked --extra notebook` |
| Open notebook workflows | `uv run jupyter notebook` |
| Inspect an existing environment | `bash scripts/env.sh inspect` |
| Check lint and formatting without edits | `uv run poe check` |
| Sort imports and format code (modifies files) | `uv run poe format` |
| Run tests against disposable storage | Use the harness in [research-verification](.agents/skills/research-verification/SKILL.md) |

There is no separate application build or API-server command. Running synthesis
or benchmarking notebook cells launches experiments; do so only when requested.
Model-server and database operations are documented in `README.md` and `scripts/`.

## Coding conventions

- Keep Python syntax compatible with 3.11. Use explicit parameter/return types.
- Use Pydantic at untrusted input boundaries and typed entities/results internally;
  avoid repeated coercion or validation after the boundary.
- Required constructor collaborators are explicit. Use `None` only for meaningful absence.
- Dishka providers construct dependencies. Avoid service locators, generic repositories,
  mixins and forwarding-only APIs.
- NumPy/pandas own numerical data; analysis use cases return calculated data.
  Plotting helpers must not query repositories or calculate scientific statistics.
- Ruff handles linting, import sorting and formatting: 100 columns, Python 3.11.
  Black is not configured. Use pytest for meaningful behavioral verification.
- Keep infrastructure/provider failures distinct from candidate failures. Preserve
  exception causes and report once at application/host boundaries; follow the
  [failure policy](docs/operations/error_handling_and_logging.md).

## When to use skills

Use the matching skill for its workflow; load additional skills only when the task
needs them. New substantial tasks use `research-change` and the existing task template.
Small fixes need no task record or multi-agent ceremony.

| Task | Skill |
| --- | --- |
| Plan, implement or resume a substantial change | [research-change](.agents/skills/research-change/SKILL.md) |
| Review context boundaries, services or DI; plan architecture changes | [architecture-review](.agents/skills/architecture-review/SKILL.md) |
| Change analysis calculations, curves, statistics or plotting | [analysis-change](.agents/skills/analysis-change/SKILL.md) |
| Work on SQLite, repositories, checkpoints, archives or provenance storage | [research-storage](.agents/skills/research-storage/SKILL.md) |
| Verify code, tests, notebook code or build/tooling changes | [research-verification](.agents/skills/research-verification/SKILL.md) |
| Create or revise a skill | Use `skill-creator` if available in the session |
| API, frontend, Datadog or deployment work | No local skill yet; establish the approved stack and add a focused skill when needed |

The [workflow guide](.codex/workflow/README.md) links reusable prompts, agent roles
and task records. Skills describe procedures; role files describe delegated actors.

## Constraints that apply to every task

- Inspect staged and unstaged changes; preserve unrelated work. Do not stage,
  commit, reset, switch branches or rewrite history without authorization.
- Follow the requested phase. Planning does not authorize implementation.
- Do not silently change objective gaps, penalties, targets, interpolation,
  aggregation, bootstrap settings, instances/seeds, budgets or timeout policy.
- Preserve databases, champion code, checkpoints, traces, archives, figures and
  notebook outputs. Do not launch campaigns, call live providers, migrate, clean
  storage or regenerate results merely to verify a change.
- Current defaults do not establish historical settings: inspect recorded parameters
  and provenance. Never replace an experiment because its checkpoint is missing.
- Never expose `.env`, credentials, authorization headers or private response bodies.
- Report actual checks and limitations. Claim independent review only when another
  agent performed it; otherwise label self-review.
