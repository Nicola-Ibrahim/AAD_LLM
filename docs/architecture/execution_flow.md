# Synthesis execution and recovery

[Documentation map](../README.md) · [Project README](../../README.md)

## Independent application workflows

The application exposes independently usable entry points:

- `CampaignAudit.inspect(...)` reads synthesis coverage without planning tasks,
  creating experiments or dispatching workers.

- `SynthesisCampaign.run(...)` discovers and schedules a
  matrix of experiments, including existing skip/recovery behavior and workers.
- `Synthesis.run(...)` creates one new experiment for one
  condition and executes its complete evolutionary loop in the calling process.
  Calling it again creates another experiment; use the campaign for automatic
  discovery, skipping and recovery.

Resolve each workflow from the same `EvolutionProvider` and existing workflow
scope. No local model client, repository or objective object needs to be created
in the notebook:

```python
from evolution.application.synthesis.service import Synthesis

synthesis = services.get(Synthesis)
result = synthesis.run(
    problem_id=15,
    dim=10,
    noise_std=0.1,
    noise_model="heteroscedastic",
    mode="explicit",
    prompt_strategy="baseline",
    budget=100_000,
    iterations=10,
    timeout_seconds=30.0,
    synthesis_seed=43,
)
```

The model name comes from the connected engine. `instance_id` defaults to 1 and
is fixed throughout the loop. The seed is explicit; this does not introduce a
rotating instance schedule. Logging and error reporting remain inside workflows.

Application files are grouped by their owner:

```text
evolution/application/
├── campaign/
│   ├── service.py           # Campaign API
│   ├── result.py            # Aggregate campaign result
│   ├── planner.py           # Fresh, resumed and replacement work
│   ├── audit.py             # Read-only synthesis coverage
│   ├── conditions.py        # Condition types, identity and classification
│   ├── settings.py          # Validated matrix and scheduling settings
│   └── experiment_task.py   # Picklable worker payload
├── synthesis/
│   ├── service.py           # Generate one optimizer
│   ├── settings.py          # Synthesis settings
│   ├── result.py            # Synthesis result
│   └── candidate_evaluation.py  # Per-candidate evaluation, using domain scoring
├── maintenance/
│   ├── duplicate_cleanup.py # Duplicate maintenance workflow
│   └── cleanup_types.py     # Cleanup plans, records and results
├── interfaces/
└── exceptions.py
```

Session and cleanup contracts stay separate from their services because engine/
storage interfaces also import those contracts. This avoids circular imports.
Settings are validated application data, not configuration-file readers. Session
and candidate-evaluation budgets are required explicitly; campaign execution
continues to pass its declared budget without changing scientific defaults in
the notebook.

## Campaign planning

[SynthesisCampaign](../../src/evolution/application/campaign/service.py)
is resolved once during notebook setup through `EvolutionProvider`.
Notebook 02 calls `campaign.run(...)` directly with explicit study keyword arguments and
calls `audit.inspect(...)` separately for coverage, and owns the workflow scope
until setup is replaced or the kernel shuts down.
The parameters are defined visibly,
are keyword-only and are Pydantic-validated before planning or writes.
Worker count is automatic; model identity comes from the connected LLM.
No container or framework dependency enters application/domain code.

The coordinator delegates task construction to
[CampaignPlanner](../../src/evolution/application/campaign/planner.py).
The planner reads current experiments and groups their state using the same pure
condition-classification functions as `CampaignAudit`. Neither workflow calls
the other. The audit and campaign share injected repositories and explicit study
parameters, not a cached audit report or mutable settings.
It respects targeted IDs, `auto_resume`, `skip_completed`, repeat count and the
other configured recovery gates. Fresh tasks create experiment records before
dispatch; resume tasks retain the experiment ID and recorded iteration count.

`ExperimentWorkerPool` is the application interface; `ProcessWorkerPool` supplies
the multiprocessing implementation. The campaign passes prepared experiment
tasks to `worker_pool.execute(...)`, which waits for the workers' results.
The pool calls the module-level
[run_synthesis_worker](../../src/evolution/infra/concurrency/worker.py).
Each worker opens a process-local Dishka scope, resolves its database/repository and invokes
`Synthesis.execute()`, and disposes the database in a `finally` block.
`execute()` accepts an already-registered experiment for worker/recovery execution;
`run()` handles registration for the independent entry point. A dedicated
worker provider reuses the serialized engine instead of creating another LLM client.

## Session execution

`Synthesis` invokes `LLaMEAEngine`, which constructs a
[LLaMEASession](../../src/evolution/infra/engines/llamea/runner.py).
The session builds prompts and an evaluator and runs LLaMEA with one parent,
one offspring, elitism, and sequential candidate evaluation within that session.
Campaign sessions can run concurrently in different workers.

The pool submits work up to its worker capacity and stops admitting new tasks
after a terminal provider/storage failure. Already-running tasks finish normally.
Provider failures pass through LLaMEA's catches as workflow errors rather than
candidate penalties. See [error handling and logs](../operations/error_handling_and_logging.md).

The infrastructure evaluator calls the application candidate-evaluation use case.
The shared executor runs generated code; evolution's domain scoring policy
constructs fitness. Iteration telemetry is persisted through the synthesis
repository. See [evaluation protocol](../benchmark_protocol.md) for the
actual return, timeout, budget and scoring behavior.

## Checkpoint recovery

Session checkpoints use:

```text
data/evolution_state/{dim}D/std_{noise}/f{problem_id}/experiment_{id}/llamea_config.pkl
```

If this checkpoint exists, the session loads it through
[load_synthesis_checkpoint](../../src/evolution/infra/engines/llamea/checkpoint.py),
reattaches the current evaluator and LLM client, and restores the archive logger
path. This reader also handles historical relocated type names. It does not invoke
`LLaMEA.warm_start()`. Checkpoints are trusted local pickle files, not safe input
from arbitrary sources.

If loading fails, the session logs a warning and initializes a fresh LLaMEA engine.
Therefore a database resume task alone does not guarantee restoration of the
previous population; a usable checkpoint is required.

A successful loop marks the experiment completed and saves its summary, then
removes the temporary session archive before processing the session result.
A loop exception marks the experiment failed, records the exception and re-raises.
Recovery decisions subsequently depend on configured retry/resumption gates.
Candidate code, champion exports and benchmark traces have separate lifecycles;
session checkpoint cleanup does not remove them.

## Independent benchmark resumption

Benchmark recovery is separate from synthesis checkpoints. Workload discovery,
trial resumption and read-only coverage audit consume the shared benchmark
condition-status policy, including schema/hash validity and historical skipped
tails. Partial valid trials resume; stale results do not count as reusable coverage.
See [system architecture](system_architecture.md) and
[evaluation protocol](../benchmark_protocol.md).
