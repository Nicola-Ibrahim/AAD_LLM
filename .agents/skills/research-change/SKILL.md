---
name: research-change
description: Plan and implement substantial AAD_LLM changes while preserving scientific behavior and recorded experiments. Use for changes spanning research workflows or layers, not routine small edits.
---

# Research-preserving changes

Use the repository's `AGENTS.md` as the source of stable project rules.
Read the named task file. If a substantial task has no record, create one from
[the task template](../../../.codex/workflow/templates/task.md) under
`.codex/workflow/tasks/`; use a descriptive name and preserve previous records.
See [the workflow guide](../../../.codex/workflow/README.md) for navigation and
isolated verification commands.

1. Trace the affected behavior before proposing a change. Record facts separately
   from hypotheses and list the scientific/state behavior that must be preserved.
2. Define observable acceptance criteria and an ordered plan. Identify material
   ambiguities; resolve routine implementation choices within the user's scope.
   If only planning was requested, stop after recording the plan.
3. Implement coherent steps and verify the affected behavior as work proceeds.
   Use characterization checks where ownership or structure changes could alter
   numerical results, candidate selection, serialization or resumption.
4. Delegate bounded independent investigation/review when useful and available.
   Assign explicit scope and evidence expectations; keep edits non-overlapping.
   For substantial changes obtain a separate review when possible. If unavailable,
   identify the review as a self-review; do not fabricate independent sign-off.
5. Resolve findings, rerun checks justified by the changes and record actual
   commands/results, remaining limitations and next actions in the task file.

Treat model timeouts, scientific candidate failures and incomplete data distinctly.
A passing check does not justify changing the experimental protocol or destroying
partial state. A task file is a specification and handoff, not automatic permission
to run experiments, mutate study data or call paid services.

Keep reporting proportional. Do not create extra scorecards, status databases or
report hierarchies; the task record holds the plan, decisions and handoff together.
