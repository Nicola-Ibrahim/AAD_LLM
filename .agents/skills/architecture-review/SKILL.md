---
name: architecture-review
description: Trace AAD_LLM architecture and evaluate design choices for boundary reviews or structural plans. Supports chat-only reviews and named task plans; excludes ordinary local fixes.
---

# Review architecture boundaries

## 1. Trace the current design

Inputs: the requested architecture question or proposed change, relevant code and
[system architecture](../../../docs/architecture/system_architecture.md). Follow
`AGENTS.md`; use [research-change](../research-change/SKILL.md) for substantial-task
phases, record creation, delegation and handoff. This skill owns architecture
tracing and design evaluation, not orchestration.

Trace a representative notebook/service entry through application, domain and
infrastructure before proposing new abstractions. Inspect imports and Dishka wiring;
folder names alone do not establish ownership.

Map current responsibilities to evolution, benchmark and shared. Check cross-context
core imports, shared dependencies, IO in domain logic, scientific calculations in
plotting, repeated validation, forwarding wrappers and unnecessary interfaces.
Respect the documented benchmark infrastructure reader of synthesis-owned records.

## 2. Evaluate the design

Report findings as evidence: file/symbol, concrete trigger or dependency, impact,
and smallest correction. Separate defects from preferences. Keep useful modularity;
do not prescribe an interface, service or folder for every class.

For a proposed move, list callers, notebook imports, DI registrations, serialization,
worker pickling and recovery behavior that could change. Specify characterization
checks for affected scientific behavior; execution/isolation belongs to
[research-verification](../research-verification/SKILL.md) when authorized. Distinguish current
architecture from deferred proposals and preserve numerical operations and ordering.

## 3. Produce the requested output

**Review or chat-only question:** return evidence-backed findings and recommendations
in chat, including unresolved assumptions. Stop after answering the question; do
not turn a review into a refactor or create a task file solely because this skill ran.

**Architecture plan:** put the following in the named/permitted task record, or
in chat when requested. Research-change owns record creation and phase handling.
Scale detail to the decision; do not create separate documents for each item.

- Current architecture and relevant execution path, supported by source references.
- Viable alternatives, including reuse of existing capabilities or a smaller change;
  tradeoffs, constraints and a recommended design with reasons. If only one option
  is viable, explain why. Identify assumptions and decisions still needing input.
- Proposed components, ownership and dependency direction. Add a sequence or
  component diagram when it clarifies the decision; label proposed behavior.
- Affected files, public callers and compatibility/data impacts.
- Acceptance criteria, ordered migration steps and dependencies, recovery/rollback
  where relevant, and isolated verification tied to the criteria.

When the design involves background work or external systems, examine execution
ownership, concurrency, dependency/session lifetimes, failure propagation and
restart recovery as applicable. Derive specific requirements from the task brief;
do not assume a queue, API framework, delivery guarantee or deployment platform.

For review/planning, inspect code read-only and write only the permitted planning
output. Run only explicitly requested safe read-only checks within the planning
scope; stop before implementation or other proposed check execution. If a structural
implementation is separately authorized, hand the recommendation to research-change
and the relevant specialist skills. Update current architecture documentation only
within that implementation's scope; keep proposals clearly identified.
