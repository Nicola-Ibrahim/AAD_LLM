---
name: research-change
description: Manage task phases, records, delegation and handoff for substantial AAD_LLM changes, including plan-only and resume requests. Routine fixes need no task record.
---

# Research change workflow

## 1. Establish phase and output

Read `AGENTS.md`, applicable nested guidance and the user's brief. Identify the
outcome, task-specific constraints, decisions to investigate and authorized phase.
On resume, reconcile the existing task summary with current files and evidence;
continue only unfinished work in the authorized phase.

For substantial work, read the named task record, or create one under
`.codex/workflow/tasks/` using the
[task template](../../../.codex/workflow/templates/task.md). Preserve existing history.
Create or update that record only when its path is permitted by the user's edit
scope. Use chat when explicitly requested or when task-record writes are excluded;
a limit to the named task file still permits saving that plan. If the user both
requires a named record and prohibits writing it, flag the conflict and continue
only permitted read-only investigation until resolved.
The [workflow guide](../../../.codex/workflow/README.md) is the human navigation map.

## 2. Investigate and plan

Record verified behavior with file/symbol evidence, assumptions and unresolved
questions. Identify preserved scientific/state behavior, affected callers, risks,
observable acceptance criteria and ordered steps. For architecture tracing and
design choices, use [architecture-review](../architecture-review/SKILL.md); for
other changes inspect the relevant implementation and callers. Specialist skills
define their own subject-specific evidence and proposed checks.

Investigate and write the plan directly when one agent has enough context.
Delegate a bounded read-only investigation only when an evidence gap or independent
work justifies it. Request independent plan review when a concrete consequential
assumption needs challenge; give the reviewer that question and evidence. No fixed
agent sequence is required for every planning task.

**If planning only:** return the findings/plan in the permitted output location.
Keep useful proposed diagrams inside the task record or chat and label them as
proposals. Stop before code edits, experiments, data mutations or implementation
verification; explicitly requested safe read-only checks remain permitted. A written
plan does not authorize its execution.

## 3. Implement only when authorized

When implementation is authorized, reuse existing evidence. Delegate a bounded
coding part when it usefully separates the work, with file ownership, safeguards,
acceptance criteria and expected checks. Tell the coder it shares the workspace
and must preserve others' edits. The main agent owns scientific decisions,
integration and the task record. Keep dependent work sequential.

Use the relevant specialist skills from AGENTS.md only when their scope applies.
Use [research-verification](../research-verification/SKILL.md) for affected executable
behavior; specialists supply the checks to cover, verification owns safe execution.
For substantial implementation, request a separate read-only reviewer for the actual
diff, including the baseline and acceptance criteria.
Ask for severity, file/symbol, trigger, impact and correction; distinguish confirmed
bugs from hypotheses. Address findings and repeat affected checks when justified.
If delegation is unavailable, continue within scope and record self-review and the limit.
Role definitions are in `.codex/agents/`; configuration alone is not evidence they ran.

## 4. Report and stop

When a task record is permitted, refresh its top summary: phase/scope, next action,
unresolved decisions, HEAD and relevant dirty changes, latest checks and limits.
Below it, record material decisions, actual commands/results and agent identities
from tool/activity evidence. Otherwise return those relevant facts in chat.
State whether role instructions were explicitly supplied or automatically loaded
when verified. Do not invent agent activity or independent sign-off.

Keep at most one task record; do not add parallel scorecards or status hierarchies.
Report completed work, actual verification and remaining decisions. Stop at the
requested phase boundary; for implementation finish the authorized changes,
verification and review, or identify the blocking condition and preserved partial
state. Do not claim completion when required checks/review remain unresolved.
No experiment, provider call or study mutation is authorized merely by using this skill.
