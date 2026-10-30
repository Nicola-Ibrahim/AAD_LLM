# <Descriptive task title>

## Current state

Updated: YYYY-MM-DD

- **Phase and authorized scope:** proposed / planning / implementation / verification /
  complete / blocked; state exactly what is authorized now.
- **Next concrete step:** one action, or no remaining work within this task.
- **Unresolved decisions:** list blocking decisions separately from deferred work;
  write none if no decision is needed.
- **Baseline:** branch, full HEAD commit, and relevant staged/unstaged changes.
  For a substantial review identify the compared commit/diff scope or fingerprint.
- **Latest verification and limits:** actual latest results, reviewed snapshot,
  runtime/environment and any checks not performed. Keep older evidence below.

Keep this summary concise and refresh it after a material change or handoff.

## Problem and evidence

Describe the observed behavior, expected behavior and reproducible trigger.
Separate confirmed facts, hypotheses and unresolved questions. Cite relevant
files/symbols and sanitized evidence; do not paste credentials or huge logs.

## Scope and preserved behavior

- In scope:
- Out of scope:
- Scientific/protocol invariants:
- Data, artifacts and notebook outputs to preserve:

## Acceptance criteria

- [ ] Observable condition demonstrating the intended behavior.
- [ ] Relevant existing behavior still works.

## Plan and dependencies

- [ ] Investigate the owning code paths and capture necessary baseline behavior.
- [ ] Implement the scoped change.
- [ ] Verify the affected behavior in isolated storage.
- [ ] Review, address findings and re-verify as warranted.

Adjust the steps for this task. Identify independent investigations and any
assigned file ownership; do not imply all tasks require subagents.

## Progress and decisions

Record material changes, rationale, evidence and deviations from the plan.
Keep old conclusions only when they explain a current decision.

## Verification and review

| Check or command | Actual result | Scope/limitations |
| --- | --- | --- |
| Not run yet | Pending | Do not infer a pass |

Review: not performed | self-review | independent review by named agent
Findings resolved / deferred, with reasons:

### Agent activity evidence

| Runtime agent/thread | Assigned role and how supplied | Scope/baseline reviewed | Actual findings/checks and limits |
| --- | --- | --- | --- |
| Not used yet | Not applicable | Not reviewed | No delegation or independent review claimed |

Confirm actual delegation/completion from available Codex agent activity/threads
or tool responses. Record the runtime identity and review baseline when available.
Role configuration alone is not execution evidence. Distinguish explicit role
instructions from verified automatic custom-role loading; write not verified
when the runtime does not expose that information. A task record summarizes this
evidence; it cannot itself prove external agent execution.

## Handoff

Completed work:
Remaining work and risks:
Next concrete action:
Conditions requiring user input or an external-state change:
