# Resume existing work

Replace `<task-name>` with the existing task record's name.

```text
Use $research-change to continue .codex/workflow/tasks/<task-name>.md.

Follow AGENTS.md. Read the task and inspect staged and unstaged changes first.
Reconcile recorded progress with the actual files and verification evidence.
Do not assume another agent's memory or repeat expensive checks without a reason.

Resume the next unfinished step only within the previously authorized phase and
scope. A planned task remains planning-only until implementation is authorized.
Preserve scientific behavior, study data, checkpoints, recovery rules, notebook
outputs and unrelated changes.

Follow the main agent → investigator → coder → reviewer → main agent workflow,
resuming only unfinished stages. Use the coder role for a bounded implementation
part only when implementation is authorized; assign explicit file ownership and
preserve others’ edits. Use read-only investigation/review where needed. The main
agent integrates and verifies. State if delegation is unavailable.
Delegate bounded isolated testing when useful within that scope. Preserve
read-only investigator/reviewer assignments and avoid overlapping edits.
Do not claim independent review unless another agent actually performed it.

Update the task with material decisions, actual verification, remaining limitations
and the next action. If complete, confirm the evidence instead of reopening work.
Keep the task's current-state summary at the top up to date: authorized phase,
next action, unresolved decisions, baseline and latest verification limits.
When agents are used, confirm their activity and record actual runtime identities,
role-instruction source, reviewed commit/diff scope and findings/checks. Do not
claim automatic role loading or independent review from configuration alone.
Do not launch experiments, call live APIs, run migrations, regenerate results,
stage or commit changes unless separately authorized.
```
