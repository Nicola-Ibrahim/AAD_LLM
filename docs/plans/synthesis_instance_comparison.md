# Exploratory synthesis instance comparison

Historical handoff recorded on 2026-10-22; status updated on 2026-10-23.
**Retired experiment—not the current implementation.** Synthesis has returned
to one fixed instance per session (instance 1 for fresh sessions); benchmarking
now uses instances 2–21. The scheduling configuration, runtime switching and
sidecar persistence APIs described below have been removed. Keep this note as a
record of the explored design, not as instructions for running current code.
No synthesis or benchmark run was launched while implementing the original change.

## Purpose and agreed limitation

Compare fixed-instance synthesis (A) with synthesis that uses a new instance for
each candidate execution (B). The user explicitly accepted keeping incumbent
fitness from its earlier instance. Consequently, selection compares scores from
different instances: this is an exploratory comparison, not a matched-instance
selection protocol or proof of improved generalization.

## Historical exploratory setup

- Qwen2.5-Coder-32B-Instruct, f15, 10D, noise standard deviation 0.1.
- All four prompt strategies, both Explicit and Implicit modes.
- Ten candidate executions per session, fixed budget of 100,000 per execution.
- Historical setting in the now-removed synthesis configuration file: `evolution.instance_policy = "per_iteration"`.
- Candidate executions use instances 1–10, with noise seed `42 + instance_id`.
- Each candidate executes once; failures consume their instance. Generation
  failures that never reach candidate execution do not consume an instance.
- Incumbents are not re-evaluated and scoring/selection mathematics are unchanged.
- Benchmarking remains 20 trials on held-out instances 11–30, budget 100,000,
  with the existing 30-second generated-champion timeout.

## Changes in the retired implementation

- Configuration/session models accept `fixed` and `per_iteration` policies.
- The LLaMEA evaluator constructs the next instance before candidate execution,
  preserving the candidate-evaluation service's failure/stagnation history.
- Each execution records its actual instance, noise seed, optimum, iteration,
  policy and budget in `iter_N.instance.json` beside the generated program.
  No database schema migration was introduced; the experiment's instance field
  still identifies the starting instance.
- Checkpoint resumption continues the instance schedule, rejects incompatible
  fixed-instance history, and does not count a saved parent as a new execution.
- The session summary uses the selected candidate's own optimum.
- Synthesis notebook/protocol documentation and instance-schedule tests were
  updated. Benchmark execution and analysis mathematics were not changed.

## Preservation and historical starting conditions

The fixed-instance A study is preserved at:

`results/archives/2026-10-22_221126_one_instance/`

That archive includes synthesis data/code, benchmark results, figures,
configuration and source/dependency provenance. Leave it untouched.

At implementation time, the active database still contained eight completed A
experiments (IDs 1–8). Ordinary campaign execution skips completed experiments;
changing the instance policy does not automatically replace them. Starting B
requires deliberate fresh storage or the existing explicit experiment-replacement
API, after checking the actual database/model. Do not hardcode these historical
IDs into configuration or assume a later database still contains the same IDs.

## Historical follow-up checklist (not current execution instructions)

1. Check the actual recorded instance sidecars and completion status.
2. Preserve B's database, generated programs, sidecars, checkpoints and effective
   configuration before replacing any active study.
3. Benchmark selected B champions on instances 11–30 and regenerate analysis
   from those results. Keep A and B artifacts separate; do not merge conditions
   or compare plots from different budgets or benchmark instance sets.
4. Interpret any difference with the retained-incumbent limitation above.
5. Revisit whether to retain this policy or return to fixed-instance synthesis.
   The policy setting was subsequently removed when fixed-instance synthesis
   was restored. Do not resume a varying-instance checkpoint under the restored
   implementation or blindly revert unrelated configuration or user edits.

## Verification at implementation

437 tests passed, including instance scheduling, failure advancement, correct
instance-specific scoring, checkpoint handling and worker pickling. Ruff lint,
format checks, notebook syntax and `git diff --check` passed. No campaigns,
database migrations, benchmark regeneration or archive deletion were performed.
