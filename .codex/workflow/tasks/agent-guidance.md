# Project guidance and focused skills

## Current state

Updated: 2026-11-03

- **Phase and authorized scope:** complete; agent guidance and skills only.
- **Next concrete step:** none within this task; use the updated prompts/skill map for new work.
- **Unresolved decisions:** none. Future API/frontend/monitoring/deployment skills are deferred.
- **Baseline:** main, `0cd887e691d68a1bf0ffaf5385fae900c7a82ab5`. Existing unstaged changes in
  docs, three analysis notebooks and two tests, plus deleted result_exports.py, belong
  to the earlier exporter cleanup and must be preserved.
- **Latest verification and limits:** all five skills passed validation; 28 relative
  links, command/configuration checks, Python 3.11 harness syntax and diff whitespace
  checks passed. Independent review completed and corrections re-reviewed. No backend
  tests or live skill-discovery check; no experiments or data mutations.

## Problem and evidence

AGENTS.md mixed durable architecture/data rules with detailed task coordination.
The broad research-change skill, workflow guide and prompts repeated the same
agent choreography and evidence requirements. Setup/run commands were missing
from AGENTS. The current stack uses Ruff formatting; Black, FastAPI, frontend,
Datadog and production deployment are not configured application capabilities.

Official guidance distinguishes always-applied repository instructions from
selectively loaded procedures. OpenAI's SDK maintenance example uses AGENTS for
project policy and skill triggers, with repo skills under .agents/skills.

## Scope and preserved behavior

Only AGENTS, repository skills, human workflow navigation/prompts and this task
record change. Agent role definitions and existing task records remain in place.
No backend, dependencies, scientific settings, research data or notebook edits
are part of this task. Keep scientific/data safeguards visible in AGENTS.

## Acceptance criteria

- [x] AGENTS states purpose, actual stack, DDD boundaries, commands, constraints and skill triggers.
- [x] Focused discoverable skills have accurate frontmatter and distinct responsibilities.
- [x] Multi-agent procedure and isolated pytest harness each have one maintained home.
- [x] General plan/implement/resume prompts route into skills without repeating procedures.
- [x] Relative links and commands match actual files/configuration.
- [x] Independent review addresses confirmed defects; unrelated dirty changes are preserved.

## Plan and dependencies

1. Inspect local guidance and actual project tools; consult official sources.
2. Separate durable guidance from research coordination, architecture, analysis,
   storage and verification procedures. Update human navigation and prompts.
3. Validate skills, links and command accuracy without running research workflows.
4. Review the actual diff independently, address findings and record results.

## Progress and decisions

- Kept research-change as the substantial-task coordination procedure; split domain
  procedures into architecture-review, analysis-change, research-storage and research-verification.
- Kept three generic human prompts. Small fixes need no task record or all-agent workflow.
- Documented Ruff as the formatter and notebook workflow as the run entry point.
  Added no placeholder deployment/API skills or new dependencies.
- No runtime role auto-loading is inferred from files. Configured models remain unchanged.

## Verification and review

| Actual check | Result and limits |
| --- | --- |
| `python3 .../skill-creator/scripts/quick_validate.py <skill>` | Initial system interpreter lacked PyYAML; no dependencies installed |
| `for skill in .agents/skills/*; do .venv/bin/python /Users/nicolaibrahim/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill" || exit; done` | All five skills valid; repeated after reviewer corrections |
| `python3` read-only heredoc inspecting Markdown links, `pyproject.toml` and harness AST | 28 relative links valid across 11 guidance files; documented Ruff settings/Poe tasks/notebook extra match config; harness parses for Python 3.11, not executed |
| `git diff --check` | Passed |
| Independent review and correction review | Two confirmed findings resolved; no residual defect reported |

Reviewed guidance fingerprint (all 11 guidance files, excluding this task record):
`ec6d9e061d25c9879451e5e08deff2c85ac876f5b445867d9ffcc4c845328aca`.
No backend suite was run for instruction-only changes. Files are discoverable in
repository skill locations; live discovery/activation in a fresh session was not tested.

The reviewer found that the inherited pytest harness did not establish offline
execution in child processes: notebook setup tests can ping a local model despite
SKIP_LLM_VALIDATION, and Python path overrides do not reach fresh interpreters.
The verification skill now states those limits, restricts selectors to inspected
offline tests, names the known unsafe notebook subprocess test, and redirects the
parent PROJECT_ROOT for logging. The backend/test gap is documented, not repaired
outside this task. Full-suite child-process isolation remains separate future work.

### Agent activity evidence

| Runtime identity | Role supplied | Scope/baseline | Actual outcome and limits |
| --- | --- | --- | --- |
| /root/guidance_investigation | investigator role via spawn tool; no claim of custom-file auto-loading | HEAD above; existing guidance and repo stack | Read-only evidence about stack, commands, boundaries and duplication; no tests/studies |
| /root/guidance_docs | coder role via spawn tool, explicit temporary-file ownership | Workflow guide/prompts at baseline above | Drafted five navigation/prompt files in /private/tmp; no repo or research edits |
| /root/guidance_review | reviewer role via spawn tool, .codex/agents/reviewer.toml explicitly supplied | Actual tracked diff plus four new skills/task at HEAD above; correction reviewed afterward | Identified live-ping and subprocess-path isolation defects in verification instructions; re-review confirmed both resolved. Read-only source review; no tests/live calls |

## Sources

- [Official AGENTS guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Official skill guidance](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI SDK maintenance example](https://developers.openai.com/blog/skills-agents-sdk)
- [Concise instructions and progressive disclosure](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)

## Handoff

Completed: project blueprint, five focused skills, shorter generic prompts,
workflow navigation, static validation and independent review. Existing unrelated
exporter edits and study artifacts were left untouched. No application code or
scientific configuration changed in this task.

Remaining limitation: full-suite subprocess isolation needs separate work before
claiming all tests are offline; new skill runtime discovery was not exercised.
No further action is required for this documentation task.
