# Investigate and plan

For substantial work, keep the reusable planning procedure in `research-change`.
Add `architecture-review` when the task involves design or boundaries. Give the
agent the outcome, task-specific constraints and decisions to investigate:

```text
Use $research-change to plan <desired outcome>.
Follow AGENTS.md and write the plan to
.codex/workflow/tasks/<task-name>.md.

Required behavior: <observable requirements>.
Preserve: <task-specific behavior or compatibility constraints>.
Investigate: <design choices, uncertainties or tradeoffs that matter>.

Investigate and plan only. Do not implement, launch experiments, call live
providers, migrate databases or change research data.
```

For an architecture task, start with `Use $research-change and
$architecture-review to plan ...`. Repository safeguards already live in AGENTS;
include additional constraints that shape this particular task. Small questions
can be asked directly without a task record.
