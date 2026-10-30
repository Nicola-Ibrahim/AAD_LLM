# Investigate and plan before implementation

Replace the placeholders with the requirement, outcomes, safeguards and task name.

```text
Use $research-change to investigate and plan <describe the requirement>.
Record the plan in .codex/workflow/tasks/<task-name>.md.

Follow AGENTS.md. Inspect staged and unstaged changes first. Read the existing
task record, or create it from .codex/workflow/templates/task.md if absent.

We want <observable outcomes>.
Preserve <required behavior, scientific rules, data and recovery guarantees>.

Use the investigator role defined in .codex/agents/investigator.toml to trace
<relevant workflow or concern> in a bounded read-only investigation.
If unavailable, investigate directly and state that limitation.
Trace the execution path before proposing changes. Record the cause, affected
behavior and smallest justified correction. Distinguish confirmed facts from
hypotheses, and identify proposed behavior changes explicitly.

The coordinator writes findings, scope, acceptance criteria, dependencies and a
step-by-step plan in the task file. Preserve existing evidence and decisions;
mark superseded conclusions clearly. Identify decisions needing my input.
Do not implement yet or treat the plan as implementation authorization.
Do not launch experiments, call live APIs, run migrations, regenerate results,
stage or commit changes. Only the task record may be edited.
```
