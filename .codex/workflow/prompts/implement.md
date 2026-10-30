# Implement an agreed task

Replace `<task-name>` with the existing task record's name. Keep task-specific
requirements and safeguards in that record.

```text
Use $research-change to implement the agreed plan in
.codex/workflow/tasks/<task-name>.md.

Follow AGENTS.md. Read the task and inspect staged and unstaged changes first.
Preserve the task's scientific behavior, experiment data, checkpoints and recovery
rules, as well as unrelated changes. Complete only the authorized scope.

Run appropriate isolated verification against the acceptance criteria. Delegate
bounded testing to a separate agent when useful; give it explicit scope and
safeguards, and avoid overlapping file edits. Do not require a tester role file
or claim that one exists. Report actual commands, results and verification gaps.

Use the reviewer role defined in .codex/agents/reviewer.toml for an independent
read-only review of the actual changes against the task. Request actionable
findings with severity, file/symbol, trigger, impact and suggested correction;
distinguish confirmed defects from hypotheses. Address findings and re-verify
affected behavior.
If independent review is unavailable, state that limitation and label self-review.

Update the task with actual results,
material decisions and remaining limitations.
Do not launch experiments, call live APIs, run migrations, regenerate results,
stage or commit changes unless separately authorized.
```
