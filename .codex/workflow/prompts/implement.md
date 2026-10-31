# Implement a change

## Small tweak: no task record needed

Use this for a focused change with limited impact. Replace the placeholders.
For example: `Update the Result class to <describe the change>`.

```text
Update <class, method or component> to <describe the change>.

Follow AGENTS.md. Inspect staged and unstaged changes, the implementation and
its callers first. Preserve <required behavior> and unrelated changes.
For Result changes, preserve exception causes, error reporting and scientific
failure classifications unless the requested change explicitly alters them.

Update affected callers and meaningful tests. Run focused isolated verification
and report actual results and limitations. Keep the change bounded; if inspection
reveals a cross-workflow contract change, explain the impact and propose a plan
before broadening implementation.
Do not launch experiments, call live APIs, run migrations, modify research data,
regenerate results, stage or commit changes.
```

## Approved substantial task

Replace `<task-name>` with the existing task record's name. Keep task-specific
requirements and safeguards in that record.

```text
Use $research-change to implement the agreed plan in
.codex/workflow/tasks/<task-name>.md.

Follow AGENTS.md. Read the task and inspect staged and unstaged changes first.
Preserve the task's scientific behavior, experiment data, checkpoints and recovery
rules, as well as unrelated changes. Complete only the authorized scope.

Use the main agent → investigator → coder → reviewer → main agent workflow.
Reuse the task’s existing evidence; request further bounded read-only investigation
only for unresolved questions. Assign a focused implementation part using
.codex/agents/coder.toml, with explicit file ownership, acceptance criteria and
safeguards. The coder is not alone in the workspace and must preserve others’ edits.
Keep complex scientific decisions and integration with the main agent. Review the
coder’s actual changes; do not accept its summary as verification.
If a role is unavailable, report it and perform that work directly.

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
Keep the task's current-state summary at the top up to date: authorized phase,
next action, unresolved decisions, baseline and latest verification limits.
When agents are used, confirm their activity and record actual runtime identities,
role-instruction source, reviewed commit/diff scope and findings/checks. Do not
claim automatic role loading or independent review from configuration alone.
Do not launch experiments, call live APIs, run migrations, regenerate results,
stage or commit changes unless separately authorized.
```
