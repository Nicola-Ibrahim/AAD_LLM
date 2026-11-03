# Implement a change

For a small, contained change:

```text
Update <component> to <desired behavior>.
Follow AGENTS.md. Inspect the working tree, implementation and callers first.
Preserve <required behavior> and unrelated changes. Use relevant skills only.
Update affected callers and verify the behavior with focused isolated checks.
Report actual results and limitations. Do not launch experiments, call live APIs,
modify study data, migrate, regenerate results, stage or commit.
```

For an agreed substantial task:

```text
Use $research-change to implement the agreed plan in
.codex/workflow/tasks/<task-name>.md.

Follow AGENTS.md and the task's acceptance criteria. Inspect the current working
tree and reuse verified evidence. Preserve unrelated edits and the task's
scientific, data and recovery constraints. Complete the authorized scope, review
and verify the actual changes, and update the task with results and limitations.
Do not launch experiments, call live APIs, modify study data, migrate, regenerate
results, stage or commit unless separately authorized.
```
