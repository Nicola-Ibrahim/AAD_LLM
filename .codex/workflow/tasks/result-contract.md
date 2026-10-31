# Explicit Result outcomes and callback dispatch

## Current state

Updated: 2026-10-31

- **Phase and authorized scope:** complete; user superseded the variant design with one generic Result holding value and error, retaining on().
- **Next concrete step:** none in this correction.
- **Unresolved decisions:** none; inactive payload is None, empty/mixed results rejected.
- **Baseline:** d6fcc46882849db18c9a52a5f7557c0b82d0fa42; prior prompt edits and other task work preserved.
- **Latest verification and limits:** simplified implementation: 95 focused isolated tests passed, 1 warning, 5.44s; Ruff lint/format and diff checks pass. Independent read-only correction review found no confirmed defects. Earlier full-suite 702 pass applies to the superseded variant design; full suite not repeated for this correction. No live APIs or studies.

## User-requested simplification (supersedes variant design below)

Removed Success/Failure, custom schema hooks, Pydantic generic metadata handling
and base construction override. Result is a normal generic Pydantic model with
value and error, one exclusive-payload validator, existing factories and on().
Error rename, private original exception, sanitization and callback propagation
remain. Falsey values (0, False, empty collections/text) are successful values;
None is the inactive payload, so success(None) and an entirely empty Result are
rejected. Notebook callers are unchanged from the preceding migration.

Actual verification command: temporary isolated harness described below, with
`tests/test_result.py tests/test_failure_boundaries.py tests/test_error_reporting.py tests/test_analysis_use_cases.py`:
**95 passed, 1 warning in 5.44s**. `.venv/bin/ruff check .`,
`.venv/bin/ruff format . --check` (251 files) and `git diff --check` passed.
The warning concerns optional CMA matplotlib availability.

Agent evidence: /root/result_review independently inspected the correction in
result.py/test_result.py read-only using explicitly supplied reviewer instructions;
no confirmed defects, no pytest or study operations. Prior variant review is
historical. Main implemented this bounded simplification directly.

## Historical implementation record (variant design superseded)

## Problem and evidence

Main inspected Result and callers before user approved the contract plan. Result
stored nullable value, error and exception together. Workflows use success/failure
factories; notebooks branch on is_success. Tests inspect original exception identity
and causes. Logging uses error sanitization.

## Scope and preserved behavior

Rename ApplicationError to Error; provide Success(value) and Failure(error), retain
Result factories and is_success, add on(on_success, on_failure). Keep application
catch/report-once boundaries, exception causes, privacy and scientific failures.
No protocol, numerical, recovery, database or storage changes. Preserve notebook
outputs, metadata and execution counts. No experiments, APIs, migrations, result
regeneration, staging or commits.

## Acceptance criteria

- Exactly one payload per variant; no nullable inactive fields or public exception.
- on calls only the matching callback, returns its value and propagates callback errors.
- Original exception and cause retained privately without serialized vendor details.
- Existing workflow callers and tests work; numerical behavior unchanged.
- Notebook source compiles and saved outputs/metadata are preserved.

## Plan and dependencies

1. Reuse main-agent investigation completed before approval.
2. Delegate Result and focused tests to coder; main migrates callers/docs.
3. Run isolated tests and lint; inspect notebook preservation.
4. Independent review, address findings and reverify.

## Progress and decisions

Keep Result[T] public return annotations and factories with concrete variants.
Notebook None variables represent unavailable calculated data, not Result placeholders.
No new DI layer, wrapper or decorator. Complex notebook branches retain is_success;
simple host calls demonstrate on() callback dispatch.

## Verification and review

Final commands and actual results:

- Isolated full suite: `aad_test_root=$(mktemp -d /private/tmp/aad-result-final.XXXXXX)`
  then `DATABASE_URL="sqlite:///$aad_test_root/tests.sqlite3" AAD_TEST_ROOT="$aad_test_root" PYTHONPATH=src:. .venv/bin/python /private/tmp/aad-run-tests.py`:
  **702 passed, 20 warnings, 50.08s**. Harness redirects DATA_DIR/RESULTS_DIR,
  creates tables only in the temporary SQLite DB, and invokes pytest under a main guard.
- Focused final generic/error checks with the same isolated harness and
  `tests/test_result.py tests/test_failure_boundaries.py tests/test_error_reporting.py`:
  **52 passed, 1 warning, 4.77s**.
- `.venv/bin/ruff check .`: passed; `.venv/bin/ruff format . --check`: 251 files formatted.
- `git diff --check`: passed.
- Parsed JSON comparison of all six modified notebooks against HEAD: every non-source
  field preserved; all their code cells compile. Core Result/tests parse as Python
  3.11 syntax; actual execution used Python 3.13.
- Existing warnings: NumPy infinite interpolation, optional CMA matplotlib,
  synthetic budget overrun and joblib SequentialBackend timeout. Not suppressed.

Earlier integration run: 191 passed, one obsolete assertion expected failure.value
None; migrated it to assert the field is absent. Intermediate full suite passed
699 tests before the generic correction; this is superseded by the final run.

Independent reviewer identified P2: typed factories lost their generic type and
Pydantic Result[int] fields rejected variants. Corrected with a compact typed-union
schema hook and generic-aware factories; added typed embedding/serialization tests.
Main rejected an intermediate dynamic class factory and retained normal Pydantic
generics. Base Result construction raises TypeError; callers use success/failure
factories. Independent re-review found no remaining confirmed issue.

Review baseline: HEAD d6fcc46882849db18c9a52a5f7557c0b82d0fa42; assigned diff
covers Result, logging consumers, docs, tests and notebooks, excluding prior prompt
edits. Tracked scope diff plus new test_result.py SHA256 recorded after re-review:
`84cce0982776d3a8b051ef16f7ba1567a5eaeb55c58b62faae1e28ed10764d3c`.
This records the final snapshot, not retroactive evidence of earlier exact bytes.

### Agent activity evidence

- /root/result_coder: worker with explicit .codex/agents/coder.toml instructions;
  Luna medium requested, owns result.py and test_result.py only. Reports 7 tests,
  focused Ruff and direct checks passed. Its bare pytest invocation was not the
  authorized isolated harness; main will verify in isolated storage independently.
- Prior investigation: main code inspection, not an independent investigator.
- /root/result_review: actual read-only reviewer thread, role instructions explicitly
  supplied and read from reviewer.toml. Confirmed the P2 generic issue, then independently
  rechecked the correction through pure in-memory validation/embedding/serialization,
  nested Result and arbitrary-payload probes. Independently compared notebook JSON.
  No pytest or live study operations by reviewer. No remaining confirmed defects.
  Runtime activity/tool responses confirm delegation; automatic role loading is not claimed.

## Handoff

Completed implementation, caller migration, independent review and isolated verification.
No experiments, migrations, live API calls, result regeneration, staging or commits.
Existing notebook outputs and unrelated prompt edits preserved. Remaining limitation:
no runtime Python 3.11 or live Jupyter/provider verification.
