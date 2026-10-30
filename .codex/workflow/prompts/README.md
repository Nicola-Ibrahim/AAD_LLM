# Prompts to use with Codex

[Workflow guide](../README.md) · [Task template](../templates/task.md)

Copy a prompt, replace `<task-name>` and its other placeholders, and send it in
Codex. These files are a human prompt library; they do not run automatically.

| What you want now | Prompt |
| --- | --- |
| Investigate a requirement or issue and agree a plan | [Plan](plan.md) |
| Implement the approved plan, test and obtain independent review | [Implement](implement.md) |
| Continue an existing task within its authorized phase | [Resume](resume.md) |

## Reuse for any requirement

Use a short descriptive task name and keep the same task path throughout.
Task-specific requirements, findings, decisions and verification belong in
`.codex/workflow/tasks/`. Small fixes can use a direct prompt without a task record.

Plan includes investigation and permits edits only to the task record. It does
not authorize implementation. Implement includes verification and independent
review. Resume preserves the existing authorization and cannot turn an unapproved
plan into permission to code. Standalone investigation or review can still be
requested directly in chat without a separate template.

## Agents and safeguards

Templates and agent roles are independent. Merging prompts does not remove
investigator or reviewer definitions in `.codex/agents/`, or the ability to
delegate bounded testing. A separate tester role file is not required.
The coordinator assigns scope, safeguards and evidence expectations and integrates
findings. Investigators and reviewers remain read-only; the coordinator updates
the task record. State limitations when independent work is unavailable.

All templates invoke `$research-change`, read project guidance and the working
tree, preserve study data and unrelated changes, and require actual verification
evidence. Agent roles here assist development; they are separate from experimental
LLMs and synthesis workers.

When copying these templates to another project, adapt its skill names, role paths
and safeguards as well as `AGENTS.md`.
