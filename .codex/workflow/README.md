# Codex workflow for AAD_LLM

[Project guidance](../../AGENTS.md) · [Application documentation](../../docs/README.md)

This folder is for the person directing Codex and the agents working on the code.
It is not application configuration and does not change LLaMEA or benchmarking.
Start with [the prompt library](prompts/README.md). Copy the relevant prompt,
replace its placeholders and send it in Codex.

## Where things belong

| Location | Responsibility |
| --- | --- |
| [Root AGENTS.md](../../AGENTS.md) | Stable project rules, discovered by Codex |
| [Agent roles](../agents/) | Project-scoped investigator, coder and reviewer definitions |
| [Research-change skill](../../.agents/skills/research-change/SKILL.md) | Reusable procedure for substantial research-code changes |
| [Prompts](prompts/README.md) | Copy-and-paste entry points for you |
| [Task template](templates/task.md) | Starting structure for one substantial task |
| [Task records](tasks/README.md) | Requirements, progress, evidence and handoffs |

Agent files and skills use Codex's recognized locations. This workflow folder
has no automatic execution behavior: name the task file in the prompt. Skills
are reusable procedures; agents are separate actors; task records are durable
context. Defining roles does not start them or increase synthesis concurrency.
When these role files are applied, the investigator and coder use `gpt-6-luna`;
the reviewer uses `gpt-6.1-terra`. All use medium reasoning and low verbosity.
The main agent uses the session model and handles complex planning and integration. Their
instructions request concise evidence rather than repeated narration. Model
availability depends on the account/runtime; report an unavailable configuration
instead of silently substituting a different model.

Permissions, provider and tools still inherit from the parent session. Read-only
instructions are behavioral constraints, not separate sandbox permissions. These
files configure future agent creation; they do not prove which settings an
existing thread used. Record effective settings when runtime evidence is available.

## Working sequence

1. **Main agent defines scope:** inspect the working tree, identify safeguards and
   assign a bounded investigation. Retain ownership of the task record.
2. **Investigator gathers evidence:** trace relevant paths read-only; return facts,
   file/symbol references and open questions. Main agent agrees the plan and criteria.
3. **Coder implements a bounded part:** after implementation is authorized, assign
   explicit files, behavior and isolated checks. The coder preserves others’ changes,
   reports blockers and returns changed files plus actual verification. Complex or
   scientifically ambiguous changes remain with the main agent.
4. **Reviewer checks the diff:** independently review the completed relevant changes
   against acceptance criteria and baseline. Report actionable findings read-only.
5. **Main agent integrates and verifies:** inspect delegated edits, resolve findings,
   rerun affected checks and update the task with actual evidence and limitations.

Use these role files: [investigator](../agents/investigator.toml),
[coder](../agents/coder.toml) and [reviewer](../agents/reviewer.toml).
Send a compact handoff: objective, owned files, baseline, necessary findings,
acceptance criteria, safeguards and expected output. Avoid copying the entire chat.
Do not repeat a finished investigation without new evidence. Run dependent stages
in order; parallelize only independent work with disjoint edit ownership. No agent
stages or commits unless separately authorized. Browser debugging is optional future
work, not a required stage or configured role in this workflow.

Keep small fixes lightweight. Read-only investigation and planning prompts do
not authorize implementation. A resumed agent reads the task and current working
tree; it must not assume previous agents' memories. Do not use arbitrary numeric
quality scores as evidence that a change is correct.

## Current state and agent evidence

Start each task with a short current-state summary: authorized phase and scope,
next step, unresolved decisions, baseline and latest verification limits. Keep the
detailed investigation and older evidence below it. A new session reads the summary
first, then verifies it against the working tree.

For delegated work, confirm actual spawn/completion in available Codex agent
activity/threads or tool responses. Record the runtime name/ID, assigned scope,
reviewed HEAD plus relevant staged/unstaged diff, findings and actual checks.
A diff fingerprint helps identify an uncommitted reviewed snapshot; it does not
prove execution. Keep secrets and raw transcript dumps out of the task record.

Configured roles and executed agents are different facts. If the coordinator asks
a subagent to read a role file, record that as explicitly supplied instructions.
Only claim automatic custom-role loading when the runtime confirms it; otherwise
mark it unverified. If no agent ran, record self-review. Documentation preserves
the evidence summary; execution is confirmed by the Codex activity itself.

## Verification commands

The existing tasks in `pyproject.toml` include `uv run poe lint`,
`uv run poe format-check` and `uv run poe test`. Local read-only equivalents are:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format . --check
```

Some tests resolve shared database/storage configuration, and session cleanup
can inspect `data/`. Use isolated storage for pytest rather than pointing it at
an active study. From the repository root, this harness uses a temporary test
DB, data directory and results directory; schema creation is only for that test DB:

```bash
aad_test_root="$(mktemp -d)"
DATABASE_URL="sqlite:///$aad_test_root/tests.sqlite3" AAD_TEST_ROOT="$aad_test_root" PYTHONPATH=src \
.venv/bin/python -c '
import os
from pathlib import Path
import shared.config as config
root = Path(os.environ["AAD_TEST_ROOT"])
config.DATA_DIR = root / "data"
config.RESULTS_DIR = root / "results"
config.DATA_DIR.mkdir()
config.RESULTS_DIR.mkdir()
from shared.infra.database import Database
from shared.infra.database.tables import Base
database = Database()
Base.metadata.create_all(database.engine)
database.dispose()
import pytest
raise SystemExit(pytest.main(["-q", "--tb=short"]))
'
```

For focused verification, append test paths or selectors to the `pytest.main`
argument list. `PYTHONPATH=src` also reaches spawned workers. Existing test
fixtures mock the model provider; tests must not make live gateway requests.
Do not claim this setup ran the full suite merely because the command is documented.

## Sources and maintenance

- [Custom project instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Custom agents and inherited permissions](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Repository skills](https://learn.chatgpt.com/docs/build-skills)
- [Workflow conventions](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex)
- [Research-workflow inspiration](https://github.com/zhao-dongchen/codex-research-workflow/blob/main/AGENTS.md)

This setup adapts those ideas to the existing repository; it does not install the
external scaffold. Add rules or roles when repeated work justifies them. Keep
scientific defaults and implementation details in their existing sources of truth.
