# Explicit model selection for synthesis

## Current state

- Phase: implementation and verification complete.
- Baseline: HEAD `53ecf1b`, with staged notebook, analysis and agent-role changes preserved.
- Next action: select the exact provider and model ID in Notebook 02 before running synthesis.
- Verification: 237 focused tests passed with disposable storage and mocked model transports.
  Ruff, notebook compilation, shell syntax and whitespace checks passed.

## Scope and decisions

The application accepts a typed model selection on single synthesis, campaign and
audit calls. Dishka injects an engine factory. Each worker receives the selection
and opens its own client. Environment configuration supplies connection settings.
Scientific settings and existing checkpoint and benchmark artifacts are preserved.

New experiments store a provider-qualified model identity in the existing model
name field. Historical names do not establish provider identity and remain
readable, outside automatic reuse and resume by the explicit selection. No
schema migration or data rewrite was performed. No live provider or synthesis
campaign was run.

## Review and verification

The application, infrastructure and notebook changes were delegated to
`/root/model_application`, `/root/model_infra` and `/root/model_notebook`.
`/root/model_review` independently inspected the unstaged implementation against
the baseline and reported no actionable defects. Role instructions were supplied
through the task assignments.

The focused pytest run covered dependency injection, experiment service,
explicit parameters, failure boundaries, gateway client and throttling, error
reporting, notebook integration and setup, selective reruns, synthesis workflow,
checkpoint pickling and replacement. The full repository suite was not run.
