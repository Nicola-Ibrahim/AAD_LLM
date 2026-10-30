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
| [Agent roles](../agents/) | Project-scoped investigator/reviewer definitions |
| [Research-change skill](../../.agents/skills/research-change/SKILL.md) | Reusable procedure for substantial research-code changes |
| [Prompts](prompts/README.md) | Copy-and-paste entry points for you |
| [Task template](templates/task.md) | Starting structure for one substantial task |
| [Task records](tasks/README.md) | Requirements, progress, evidence and handoffs |

Agent files and skills use Codex's recognized locations. This workflow folder
has no automatic execution behavior: name the task file in the prompt. Skills
are reusable procedures; agents are separate actors; task records are durable
context. Defining roles does not start them or increase synthesis concurrency.
Roles inherit the parent model/settings and permissions; no particular model,
provider, extra tools or concurrency setting is forced by this setup. Their
read-only instructions are behavioral constraints, not separate sandbox permissions.

## Working sequence

1. Investigate the observed problem; identify evidence and ownership.
2. Plan a substantial task and agree its behavior and acceptance criteria.
3. Implement the authorized scope; record decisions and changed files.
4. Run focused verification in isolated storage.
5. Obtain an independent review when appropriate and available; fix findings.
6. Re-verify affected behavior and leave a concise handoff in the task file.

Keep small fixes lightweight. Read-only investigation and planning prompts do
not authorize implementation. A resumed agent reads the task and current working
tree; it must not assume previous agents' memories. Do not use arbitrary numeric
quality scores as evidence that a change is correct.

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
