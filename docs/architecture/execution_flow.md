# Synthesis execution and recovery

[Documentation map](../README.md) · [Project README](../../README.md)

## Campaign planning

[build_synthesis_campaign](../../src/bootstrap/synthesis.py) loads synthesis
configuration, creates the database/repositories and runtime adapters, and returns
a `SynthesisCampaignCoordinator`. The notebook calls `run_campaign()`.

The coordinator delegates task construction to
[CampaignPlanner](../../src/evolution/application/campaign/plan.py).
The planner reads experiments and uses `CampaignAuditor` to group their state.
It respects targeted IDs, `auto_resume`, `skip_completed`, repeat count and the
other configured recovery gates. Fresh tasks create experiment records before
dispatch; resume tasks retain the experiment ID and recorded iteration count.

The process dispatcher calls the module-level
[run_synthesis_worker](../../src/evolution/infra/concurrency/worker.py).
Each worker creates its own database/repository, invokes
`SingleSynthesisUseCase.execute()`, and disposes the database in a `finally` block.

## Session execution

`SingleSynthesisUseCase` invokes `LLaMEAEngine`, which constructs a
[LLaMEASession](../../src/evolution/infra/engines/llamea/runner.py).
The session builds prompts and an evaluator and runs LLaMEA with one parent,
one offspring, elitism, and sequential candidate evaluation within that session.
Campaign sessions can run concurrently in different workers.

The infrastructure evaluator calls the application candidate-evaluation use case.
The shared executor runs generated code; evolution's domain scoring policy
constructs fitness. Iteration telemetry is persisted through the synthesis
repository. See [evaluation protocol](../evaluation_protocol.md) for the
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
[evaluation protocol](../evaluation_protocol.md).
