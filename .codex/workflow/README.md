# Codex workflow for AAD_LLM

[Project guidance](../../AGENTS.md) · [Application documentation](../../docs/README.md) · [Prompts](prompts/README.md)

Use these files as a navigation aid for human-directed Codex work. They do not run automatically and do not change synthesis or benchmark behavior.

## Where guidance lives

| Location | Purpose |
| --- | --- |
| `AGENTS.md` | Project purpose, structure, durable constraints, commands and skill routing |
| `.agents/skills/` | Reusable, task-specific procedures; load only the skill matching the work |
| `.codex/agents/` | Investigator, coder and reviewer role instructions for delegated work |
| `.codex/workflow/prompts/` | General prompts to copy and adapt |
| `.codex/workflow/templates/task.md` | Record structure for substantial work |
| `.codex/workflow/tasks/` | Requirements, decisions, evidence and handoff for individual tasks |

## Choose the workflow

A small, localized change can be implemented directly with the implement prompt. For substantial work, start with the plan prompt, record the approved scope and acceptance criteria in a task file, and use the implement prompt only after implementation is authorized. Use resume to continue an existing task within its current authorization. A plan does not authorize implementation.

Use a skill only when its description matches the task: `research-change` for substantial cross-workflow implementation and coordination; `architecture-review` for architecture boundaries; `analysis-change` for analysis calculations and notebook presentation; `research-storage` for databases, checkpoints, archives and provenance; `research-verification` for isolated checks. Routine fixes do not need all skills or every agent role.

## Delegated roles

| Role | Purpose |
| --- | --- |
| [Investigator](../agents/investigator.toml) | Trace behavior and return evidence, read-only |
| [Coder](../agents/coder.toml) | Implement a bounded assignment with explicit file ownership |
| [Reviewer](../agents/reviewer.toml) | Review the actual diff for actionable defects, read-only |

These role files describe development subagents. Their model fields are requested configuration; the runtime may not honor custom models or load the role automatically. Verify agent activity and effective instructions in the actual Codex session before claiming delegation or independent review. The main agent remains responsible for scope, integration and final verification. Role instructions do not grant separate filesystem permissions.

For project commands use [AGENTS.md](../../AGENTS.md); for test isolation use
[research-verification](../../.agents/skills/research-verification/SKILL.md). Keep experiment data and live services out of routine verification.

## Sources

- [Codex instructions with `AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI SDK maintenance with skills and agents](https://developers.openai.com/blog/skills-agents-sdk)
- [Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
