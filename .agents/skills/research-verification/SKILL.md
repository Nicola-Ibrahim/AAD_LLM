---
name: research-verification
description: Verify AAD_LLM code, notebook code, tests and tooling changes with focused checks and isolated research storage. Use after executable changes; documentation needs only relevant static checks.
---

# Verify without touching studies

## 1. Select permitted checks

Inputs: the requested verification scope, changed behavior/diff and acceptance
criteria, with specialist criteria from the relevant skill. This skill owns check
selection, isolation and execution; [research-change](../research-change/SKILL.md)
owns task records, delegation and final handoff.

Select checks from the changed behavior and acceptance criteria. Inspect existing
fixtures and imports before running pytest; tests can resolve shared database paths
and session cleanup can inspect `data/`. Use disposable storage, mocked providers
and precomputed fixtures. Never invoke an experiment, live provider or migration
against a study database as a test. Read `AGENTS.md` for scientific safeguards.

**If planning only:** propose checks and isolation requirements, then stop without
running them unless read-only checks were requested. **If verification is restricted
to read-only:** inspect sources and run permitted static checks only; do not run
pytest or the harness below, which creates temporary files and a database.

## 2. Run the applicable authorized checks

### Code and notebook checks

Lint/format checks from the repository root, with cache writes disabled for
strictly read-only verification:

```bash
.venv/bin/ruff check --no-cache .
.venv/bin/ruff format --no-cache . --check
```

Narrow paths for focused edits; broaden for changes affecting shared behavior.
Ruff excludes notebooks: parse their JSON and compile ordinary Python code cells
without executing them; handle IPython syntax separately when present. Verify
imports only when their initialization cannot call providers or touch study storage.
For documentation/skills check links, frontmatter and command accuracy; no backend
suite is needed solely for prose edits.

### Pytest, only when execution and disposable writes are permitted

The existing fixtures provide partial isolation. This harness sets database, data,
results and logging roots in the current Python interpreter and confines schema
creation to a throwaway database. Replace selectors only with inspected offline
tests. Do not infer that the entire suite is isolated by this command.

Python path overrides do not propagate into spawned interpreters; only environment
variables such as DATABASE_URL are inherited. Inspect each subprocess/worker's
storage, logging and transport setup before adding its tests. Full-suite execution
needs separately verified isolation, including offline providers in every child.

Known gap: `tests/test_synthesis_notebook_setup.py` executes notebook setup in a
subprocess, enabling `EvolutionProvider(test_generation_on_startup=True)` and
`LLMClient.ping()`. SKIP_LLM_VALIDATION does not disable ping; that test can call
a local model and use repository data/results/log paths. Keep it outside this
harness until its child transport and paths are explicitly isolated/mocked.
A disposable project copy alone does not prevent network requests.

```bash
aad_test_root="$(mktemp -d)"
DATABASE_URL="sqlite:///$aad_test_root/tests.sqlite3" AAD_TEST_ROOT="$aad_test_root" PYTHONPATH=src \
.venv/bin/python -c '
import os
from pathlib import Path
import shared.config as config
root = Path(os.environ["AAD_TEST_ROOT"])
config.PROJECT_ROOT = root
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
raise SystemExit(pytest.main(["-q", "--tb=short", "tests/test_failure_boundaries.py"]))
'
```

Choose behavioral tests: scoring, selection, numerical equivalence, serialization,
resumption or failed-write handling as affected. Avoid assertions that merely copy
implementation details. Do not alter valid scientific rules to satisfy a brittle test.

## 3. Return verification evidence

Return actual commands, scope, results/pass-fail counts, environment and limitations
to the caller. Research-change owns recording/handoff when a task exists; for
standalone verification return the summary in chat. Distinguish pre-existing
failures from regressions using evidence. Repeat checks only for changes, failures
or unresolved concerns; do not fix application code under a verification-only brief.
Stop when the permitted checks are complete, or report why a required check could
not safely run. Mark unexecuted checks as such. A configured reviewer or a written
command is not proof of execution or independent review.
