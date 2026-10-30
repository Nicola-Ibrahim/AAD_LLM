# AAD_LLM project guidance

AAD_LLM uses LLaMEA to synthesize Python optimizers, benchmarks fixed champions
on noisy BBOB conditions, and analyses the recorded results. Development agents
assist with this repository; they are separate from synthesis workers and the
LLMs being studied.

## Start here

- Read the task file named in the request and inspect the relevant implementation.
- For substantial new work, use the [task template](.codex/workflow/templates/task.md)
  and [workflow guide](.codex/workflow/README.md). Small fixes need no task record.
- Follow the requested phase: investigation and planning do not authorize implementation.
- Inspect the working tree before edits. Preserve unrelated and staged changes;
  do not stage, commit, reset, switch branches or rewrite history unless requested.

## Ownership and boundaries

- `src/evolution/` owns synthesis, campaigns, prompts, candidate feedback and scoring policy.
- `src/benchmark/` owns champion selection, benchmark trials, resumption and analysis.
- `src/shared/` owns common scientific/runtime capabilities and supporting adapters.
- Application workflows coordinate injected collaborators. Domain code owns
  scientific rules; infrastructure owns databases, files and external systems.
- Shared code must not depend on either context. Core application/domain modules
  must not import infrastructure or the other context. See the documented
  read-only synthesis-data integration in benchmark infrastructure.
- Dishka providers prepare dependencies; workflows receive ready collaborators.
  Do not add service locators, generic repositories, mixins or forwarding-only APIs.
- Required dependencies are explicit. Use `None` only for meaningful absence;
  validate untrusted input at boundaries instead of repeatedly coercing typed data.
- Analysis use cases return calculated data. Notebook plotting helpers own Plotly
  presentation and image export; they must not perform scientific calculations.

Consult the [documentation map](docs/README.md) and
[architecture](docs/architecture/system_architecture.md) for current details.
When implementation and documentation disagree, report the discrepancy rather
than silently choosing a scientific interpretation.

## Preserve the research

- Do not silently change objective gaps, penalties, targets, interpolation,
  aggregation, bootstrap settings, instances/seeds, budgets or timeout policy.
- Read current call parameters, database records and provenance separately.
  Current defaults are not evidence of historical experimental settings.
- Preserve databases, champion code, checkpoints, traces, archives and figures.
  Do not launch campaigns, paid API calls, migrations, cleanup or regeneration
  merely to verify a code/documentation change; follow the user's authorized scope.
- A missing checkpoint cannot be reconstructed from final errors alone. Never
  silently replace an experiment or delete partial work to make resumption pass.
- Keep provider/storage failures separate from scientific candidate failures.
  Infrastructure translates relevant external exceptions and preserves causes;
  application/host boundaries report failures once. Avoid low-level progress logs
  and duplicated reports. Follow the [failure policy](docs/operations/error_handling_and_logging.md).
- Preserve notebook outputs unless refreshing or clearing them is requested.
- Do not expose `.env`, API keys, authorization headers or private response bodies
  in reports, prompts, logs, task records or commits.

## Verification and coordination

- Python must remain compatible with 3.11; follow the project's type hints and Ruff rules.
- Run focused checks appropriate to the change. Improve tests for meaningful
  behavior; do not distort valid backend behavior to satisfy brittle assertions.
- Use `.venv/bin/ruff check .` and `.venv/bin/ruff format . --check` for read-only
  checks. Run pytest with isolated study storage using the workflow guide.
- For substantial independent investigations, delegation is useful when supported.
  Give each agent an objective, scope, ownership and expected evidence. Avoid
  overlapping edits. Review dependent implementation after it is ready.
- `investigator` and `reviewer` are read-only roles by instruction, not separate
  permission sandboxes. The main agent implements and integrates findings.
- Never claim independent review unless another agent performed it. If delegation
  is unavailable, label the review as a self-review and record the limitation.
- Record material decisions and actual verification in the task file. Report
  outcomes, remaining limits and the next action without inventing test results.
