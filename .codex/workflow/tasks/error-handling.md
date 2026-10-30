# Error handling and application-owned reporting

Status: planned — investigation complete; implementation not authorized
Updated: 2026-10-30
Initial investigation baseline: `main`, HEAD `6d1bac4`, including the then-staged
and unstaged changes. Layer-boundary revision: `main`, HEAD `118c7db`; the working
tree was clean before this documentation-only revision. Original test evidence
below belongs to the initial investigation, not a rerun on this revision.
Preserve any subsequent unrelated staged/unstaged changes. Findings describe
inspected working files; recheck named symbols before implementation.

## Problem and evidence

The requested outcome is clear reporting at application/host boundaries,
explicit exception causes, and no swallowed required failures or duplicated
low-level reporting. This task is planning-only. No production reproduction,
experiment run, study-database access, checkpoint load, API call or figure export
was needed for this investigation.

### Execution paths and existing protections

- Synthesis: notebook -> `SynthesisCampaign.run` -> `ProcessWorkerPool.execute`
  -> module-level worker -> `Synthesis.execute` -> `LLaMEAEngine/LLaMEASession`
  -> provider or candidate evaluator -> storage. The campaign reports the
  aggregate failure; the worker pool preserves successful results and task errors.
- Candidate evaluation: generated-code execution/return validation feeds domain
  scoring. Invalid generated programs and candidate timeouts are scientific
  outcomes, not reasons to stop all experiments. Provider/storage/backend faults
  must remain distinguishable from those outcomes.
- Benchmarking: notebook -> `BenchmarkCoordinator` operation -> workload/trial
  runner -> solver/executor, problem adapter, IOH logger and provenance storage.
  Known execution failures remain terminal trial observations with infinite gaps.
- Analysis: `Analyze*` application methods load and calculate inside logger
  operations. Notebooks separately invoke calculated-result storage and figure
  exporters; some of those currently own reporting despite being infrastructure.
- Setup/shutdown: `WorkflowScope` and Dishka composition own resource lifetimes.
  Domain services do not configure operational logging.

Existing protections to retain:

| Protection | Evidence |
| --- | --- |
| Outermost operation reports once, then rethrows unchanged; interruption is separate | `src/shared/application/diagnostics.py:26`, `report_operation` |
| Provider errors preserve SDK causes; transport retries remain bounded and unlogged | `src/evolution/infra/llm/gateway.py:24`, `provider_error`; `GatewayLLM.query` |
| Provider failures bypass malformed-output retries and are retained through third-party catches | `src/evolution/infra/llm/client.py:280`, `sample_solution` / `raise_if_failed`; `src/evolution/infra/engines/llamea/runtime.py:10` |
| Persistence/callback failures escape LLaMEA via the evaluator guard | `src/evolution/infra/engines/llamea/evaluator.py:149` |
| Database and atomic-write translations preserve original causes | `src/shared/infra/database/session.py:10`; `src/shared/infra/artifacts.py:23` |
| Corrupt provenance is an audit status; execution/analysis must not invent successful empty data | `src/benchmark/application/trials/workload.py:63`; `tests/test_error_reporting.py:100` |
| Missing or invalid positive-iteration checkpoints refuse unsafe resume without deletion | `src/evolution/infra/engines/llamea/runner.py:219`, `run` / `_create_synthesis_engine` |

Line numbers are investigation anchors; use the named symbols if files move.

### Domain-driven and hexagonal responsibility review

The requirement is propagation to an informative application/host boundary, not
an absolute ban on catching exceptions below that boundary. DDD does not require
one exception hierarchy per layer, nor a catch-and-wrap in every method. Catch
only to perform a concrete responsibility: translate an external failure, apply
an already-defined scientific outcome rule, perform bounded recovery, preserve
cleanup, or report at the selected terminal boundary. Otherwise let it propagate.

| Owner | Responsibility | Avoid |
| --- | --- | --- |
| Domain | Enforce scientific/state invariants; return legitimate scientific outcomes or raise a meaningful validation/invariant error | Operational logging, vendor/HTTP errors, retries, DI or persistence handling |
| Application | Coordinate collaborators; distinguish scientific outcomes from workflow failures; attach task/condition context and report a terminal workflow failure once | Catch-all fallback success, fabricated empty data, reclassifying backend defects as bad optimizers, HTTP mapping |
| Infrastructure | Implement external access and execution; narrowly translate vendor/IO failures to errors defined by the consuming contract, preserving causes | Terminal workflow logs, swallowing required writes, wrapping errors repeatedly without new semantics |
| Host (notebook, CLI, future HTTP API) | Configure output/lifetimes; display useful messages; map propagated errors to transport-specific responses or exit codes | Duplicating the application terminal log, leaking raw private provider details, choosing scientific penalties |

There is one selected terminal reporting owner for each operation. Application
workflows normally own it; host-only setup/export/teardown can own their own
boundary. Notebook traceback display alongside one diagnostic log is expected.
A future HTTP handler may map an already-reported application error to a response
without logging the same stack again. No HTTP server or error mapping is added here.

Confirmed ownership evidence from the revision:

- `evolution/domain/entities/experiment.py`: `record_iteration`, `complete` and
  `fail` enforce lifecycle rules with `ValueError`; they do not log or catch IO.
  Keep those invariants and their behavior. A generic `DomainError` rename alone
  would add no correction and is not required by this plan.
- `shared/domain/solution.py` and `shared/domain/scoring.py`: returned-point and
  finite-objective checks are pure validation/scientific rules. Both currently
  use `ValueError`, although an invalid generated point and a trusted scoring
  defect must not be handled identically merely because the exception type matches.
- `benchmark/domain/services/ecdf.py` and `reliability.py`: invalid analytical
  inputs raise `ValueError`. `hypothesis.py` deliberately catches known undefined
  calculations and returns unavailable results. Retain that explicit scientific
  convention; do not replace it with blanket propagation or zero results.
- `shared/application/errors.py` defines vendor-independent storage/artifact
  failures; `evolution/application/exceptions.py` defines provider, orchestration
  and unsafe-resume failures. Their infrastructure producers depend on those
  contracts, rather than forcing the core to import SDK exception classes.
- `shared/infra/database/session.py` translates `SQLAlchemyError` with an explicit
  cause. `evolution/infra/llm/gateway.py` translates exhausted SDK errors similarly.
  This is appropriate boundary handling, not solving or hiding the underlying fault.
- `shared/application/diagnostics.py` reports and rethrows without changing the
  exception. The broad catches identified in F6 and low-level logging in F1/F3/F5
  are the confirmed deviations from the intended division of responsibilities.

This is a focused exception-boundary review, not certification that the complete
codebase follows every DDD pattern. The architecture checks remain necessary.
The current error-handling guide describes unexpected backend faults as propagating,
but F6 shows catch scopes can still turn them into scientific failures. Update the
guide to match verified implementation; do not assume the documented policy is
already enforced everywhere.

#### Required propagation paths

```text
External IO/provider fault
  -> infrastructure translation (raise ContractError(...) from original)
  -> intermediate workflows propagate; cleanup preserves the primary failure
  -> outer application boundary reports once and rethrows
  -> host displays/maps a sanitized user-facing error

Domain invariant or unexpected backend fault
  -> originating rule/service raises
  -> intermediate layers propagate unchanged unless translation adds real meaning
  -> application/host boundary reports with operation and condition context

Genuine generated optimizer failure or timeout
  -> isolated execution boundary captures execution diagnostics
  -> application applies the existing domain scoring/outcome rules
  -> recorded failure remains a scientific observation; workflow can continue
```

The third path is intentional: propagating every invalid optimizer as a fatal
campaign error would change the experiment. Conversely, a storage or provider
failure must not acquire fitness, a terminal optimizer failure, or a success result.
`raise` preserves an unchanged exception; `raise NewError(...) from error`
preserves translation causality. Avoid `from None` for terminal workflow faults.
Do not add catch/rethrow-only blocks or a universal `ServiceError` wrapper.

Where `ValueError` spans several origins, prefer separating execution/validation
from trusted backend work by call scope. Introduce a narrowly named domain or
contract error only if callers genuinely need that semantic distinction. Its
owner must be the layer defining the rule/contract, with tests preserving existing
scientific category strings and recorded diagnostics. No class-per-repository
hierarchy, exception-name classification, HTTP dependency or generic error framework.

### Confirmed code-path findings

These are supported by source inspection; double-failure and malformed-artifact
scenarios below were not reproduced against a live study.

**F1 — Duplicate low-level failure reporting.**
`src/evolution/infra/concurrency/process_worker_pool.py:75–91` warns for failed
futures and then raises `OrchestrationError`; the campaign reports that failure
again. Preserve aggregation, successful results, pickling, admission stop for
systemic failures and completion of already-active workers when removing this
warning. This finding is about duplicate reports, not lost task results.

**F2 — A cleanup failure can become the primary raised exception.**
`src/evolution/infra/di.py:43–51` closes the client in a bare `finally` around
startup probing/yield. If probing and close both fail, close becomes primary.
`src/benchmark/infra/io/trace_repository.py:377–410` closes IOH loggers and merges
incremental traces in `finally`, with the same masking risk. The `with request`
exit inside `src/shared/infra/di.py:40–48` can fail before its outer handler sees
the original body exception; the existing root-close guard does not establish
protection for every nested teardown. Notebook `finally: scope.close()` patterns
also need dual-failure coverage. Do not change normal flush/merge order casually.

**F3 — Secondary failures have inconsistent visibility and ownership.**
`runner.py:203–210` logs failure-status write errors while preserving the primary
error. `src/shared/infra/artifacts.py:35–41`,
`src/evolution/infra/problems/analyzer.py:84–91,118–123` and
`src/shared/infra/lifecycle.py:63–70` similarly warn during cleanup.
`runner.py:269–270` instead uses `shutil.rmtree(..., ignore_errors=True)` and can
hide checkpoint-cleanup failures entirely. Required writes must propagate;
secondary cleanup must not replace the original failure. When cleanup is the
only failure, its required/optional nature must be explicit.

The passive WAL checkpoint in
`src/evolution/infra/storage/synthesis/repository.py:205–219` is deliberately
best-effort after committed data is stored. Its failure must not be promoted to
failed synthesis or imply committed data was lost. Removing its warning without
another nonfatal reporting path would reduce observability.

**F4 — Required IO translation is incomplete.**
`src/evolution/infra/storage/code/repository.py:26–29` creates directories outside
`atomic_write`'s translation; permission failures can escape as raw `OSError`.
Similar directory/read/merge operations occur in
`src/benchmark/infra/io/trace_repository.py:419–461` and
`src/benchmark/infra/storage/analysis_results_store.py:178–197,209–227`.
This matters in the worker pool, whose systemic-failure decision recognizes
`StorageError`, `ArtifactError` and `ProviderError`, not every raw IO exception.
Translate narrowly at actual IO boundaries, with operation/path context and
`raise ... from error`; do not catch every `ValueError` as a storage failure.

**F5 — Result storage reports from infrastructure.**
`src/benchmark/infra/storage/analysis_results_store.py:41–44,200–204` wraps save
and load in `report_operation`. Analysis notebooks resolve/call this adapter
directly. Simply deleting those wrappers would remove its current failure
reporting. Move ownership to an application/host entry point and migrate callers
together. Keep checksum validation, safe loading, atomic-manifest ordering,
namespace/signature behavior and existing serialized formats.
The notebook-owned `AnalysisFigureExporter` is a legitimate presentation/export
boundary; its operation reporting is not inherently a low-level logging defect.

**F6 — Broad execution catches include trusted backend work.**
`src/evolution/application/synthesis/candidate_evaluation.py:104–150` encloses
executor invocation, warning/metadata access and `_resolve_clean_objective` in
one broad catch. `src/benchmark/application/trials/runner.py:172–197` catches
all non-storage/artifact exceptions from a runner whose champion closure also
validates the returned point and calls `prob.eval_clean`.
A backend/problem-adapter exception there can be recorded as a candidate/trial
failure. Existing scoring calls outside these catches already propagate
correctly. Narrow failure domains only after characterizing genuine generated
code, invalid-return and timeout behavior; do not globally remove broad catches
around arbitrary generated code or reclassify solver exceptions by name alone.

**F7 — Tolerated trace/statistical cases need explicit treatment.**
`src/benchmark/infra/io/trace_repository.py:62–105` skips malformed numeric rows
with an infrastructure warning and retains existing null/NaN carry-forward
behavior. Some short/unrecognized rows are ignored without that warning.
`src/benchmark/domain/services/hypothesis.py:71,131` deliberately represents
undefined statistical results as unavailable. These are not all swallowed
workflow failures. Preserve parsing eligibility and numerical outputs in this
refactor; report tolerated exclusions through the analysis boundary without
silently switching to strict parsing or changing denominators.

### Recovery behavior requiring a separate decision

**F8 — Provider interruption affects destructive retry policy today.**
`LLaMEASession._execute_loop` (`runner.py:187–215`) marks any ordinary exception,
other than `SynthesisResumeError`, as failed. Automatic failed-experiment retry
in `src/evolution/application/campaign/planner.py:78–93` selects replacement;
`runner.py:257–264` deletes that experiment's old code/checkpoint/iterations.
This includes provider timeouts, not only unsuccessful optimizer discovery.
Likewise, failed zero-iteration warm-start loading currently warns and starts
fresh, whereas positive-iteration resume fails safely (`runner.py:277–307`).

The requested preservation of recovery behavior means this task must not change
those status transitions, retry eligibility, replacement decisions or warm-start
fallbacks without separate explicit agreement. Capture current behavior in tests
and document the consequences accurately. Do not silently treat an interruption
as resumable, declare an incomplete experiment complete, or mutate historical rows.

### Risks and hypotheses not established as production defects

- `FailureAwareLLaMEA.logevent` forwards library event strings, which can contain
  rendered tracebacks. Inspect sanitization and duplication with synthetic secret
  values; no actual credential leak was established.
- A process boundary retains rendered remote traceback but does not guarantee a
  traversable original SDK exception/request object. Preserve safe type, message,
  task identity and remote traceback; never serialize credentials or SDK clients
  merely to recreate an identical `__cause__` tree in the parent.
- Changes to trace staging after merge errors could alter recovery/idempotence.
  Characterize partial append/merge failure before proposing changes; transactional
  trace-storage redesign is not an incidental logging fix.

## Scope and preserved behavior

In scope: exception translation, failure-report ownership, primary/secondary
error preservation, error context, meaningful failure-boundary tests, and related
application/host/notebook wiring and documentation.

Out of scope: scientific-method changes, new lifecycle statuses, automatic
checkpoint replacement/resumption policies, migrations, retry/timeout/rate-limit
changes, streaming, paid/live API calls, campaign execution, study-data cleanup,
figure regeneration, logging heartbeat threads, and a new generic exception or
repository framework. Reuse existing useful error types; no class per repository.

Preserve exactly: objective gaps and penalties; invalid-code/return/timeout
categories and diagnostics used for scientific outcomes; budgets and RNG/instance
policy; termination/stagnation decisions; trace interpolation, eligibility and
missing-data rules; statistical unavailable-result conventions; champion choice;
trial denominators; result paths, JSON/CSV/checkpoint formats; committed data,
code, partial traces, checkpoints, archived results and saved notebook outputs.

## Acceptance criteria

- [ ] Domain rules remain independent of logging, external exception classes and
  transport concerns; state/scientific invariant violations remain observable.
- [ ] Every changed catch has an explicit responsibility (translation, scientific
  classification, existing retry, cleanup or terminal reporting). Other failures
  propagate without redundant catch-and-wrap layers.
- [ ] External failures, domain/input violations, scientific optimizer outcomes,
  unexpected backend faults and cancellation follow distinct documented paths;
  exception type alone does not determine scientific classification.
- [ ] User-facing reporting includes available operation/task/condition identity,
  a concise sanitized explanation and diagnostic location where configured;
  causes remain available in diagnostics, without exposing credentials or payloads.
- [ ] One application/host terminal report per failed workflow, including nested
  operations and worker aggregates; no repeated adapter warning for the same failure.
- [ ] Infrastructure performs IO/translation without owning routine workflow
  logging. Concrete logging adapters, host setup and required third-party output
  capture remain legitimate infrastructure capabilities.
- [ ] Translated required failures retain their cause and useful sanitized
  operation/path context; no failed required read/write returns fabricated success.
- [ ] Dual failures preserve the original primary exception; sanitized secondary
  diagnostics survive. A sole required teardown failure is not hidden.
- [ ] Optional WAL/cleanup maintenance remains nonfatal where currently intended,
  with an explicit nonfatal reporting path at the owning boundary.
- [ ] Genuine candidate/solver/invalid-return/timeout outcomes retain their
  recorded classification, penalties, infinite gaps, histories and trial counts.
- [ ] Demonstrated trusted-backend defects propagate instead of becoming optimizer
  outcomes. This correction is explicit, with synthetic before/after evidence.
- [ ] Corrupt artifacts remain distinct from absence; tolerated trace exclusions
  become visible without changing parsing, included traces or numerical outputs.
- [ ] Existing checkpoint refusal, status transitions, replacement rules and
  worker scheduling decisions remain unchanged in this task.
- [ ] Notebook calls stay service-oriented; no per-cell operation wrappers or
  direct SDK handling. Storage/export reporting ownership remains explicit.
- [ ] Python 3.11 compatibility, exception pickling, contextual identity,
  redaction, handler isolation and cleanup of failed setup are verified.
- [ ] Appropriate numerical, resumption, storage, architecture and notebook
  checks pass in isolated storage; no study artifacts are regenerated.

## Plan and dependencies

1. **Characterize before moving catches.** First map each affected call and catch
   to its owning domain, application, infrastructure or host responsibility, and
   record the expected propagation path above. Verify no core imports depend on
   vendor or presentation errors. Extend existing tests with fault
   injection for required IO, dual failures, clean-objective backend defects,
   genuine generated-code failures, optional WAL failure, corrupt/tolerated trace
   rows, worker transport and existing recovery decisions. Record expected
   classifications and current numerical/serialization behavior. No live model calls.
2. **Fix primary/secondary error handling.** Begin with startup-probe + close,
   IOH body + close/merge, failure-status writes and host teardown. Keep primary
   failures primary, use Python 3.11-compatible notes/explicit diagnostics for
   secondary failures, and surface sole required cleanup failures. Keep flush and
   checkpoint semantics unchanged. Depends on step 1.
3. **Complete focused IO translations.** Reuse `StorageError` for required writes
   and `ArtifactError` for invalid/unreadable recorded inputs, preserving causes.
   Keep input/programming validation separate. Cover directory creation, code,
   provenance/trace merge and calculated-result loading/writing. Depends on step 1;
   can be independently investigated, with non-overlapping edit ownership.
4. **Consolidate reporting ownership.** Remove duplicate pool/adapter terminal
   logs and preserve `OrchestrationError.errors/results` and admission policy.
   Move calculated-result persistence reporting to an existing suitable
   application/host workflow; if a new entry point is necessary, define its real
   orchestration responsibility before adding it, not a forwarding-only wrapper.
   Migrate all notebook/DI callers together. For optional successful-with-warning
   IO, select the smallest explicit diagnostic return path during characterization;
   do not silently discard warnings or add a generic event bus. Depends on 2–3.
5. **Separate scientific execution from backend faults.** Keep generated execution
   and explicit invalid-return handling in their scientific boundary; move trusted
   clean-scoring/metadata operations outside catches that convert everything to
   optimizer failures. Prove existing legitimate outcomes unchanged. Only confirmed
   backend-defect cases change from fabricated scientific failures to propagated
   workflow errors. Depends on 1–3; review each catch-scope change separately.
6. **Surface tolerated analysis exclusions.** Remove direct trace-reader warnings
   only after per-file exclusion information reaches application-owned diagnostics.
   Preserve current valid arrays, carry-forward and missing-data behavior. Keep
   legitimate undefined statistics unavailable, not fatal or zero-filled.
7. **Verify, review and document.** Run focused checks after each coherent step;
   then relevant full-suite, architecture/import/notebook, numerical parity and
   serialization checks in temporary storage. Obtain a reviewer-agent review of
   the actual implementation, fix findings and re-verify. Update current docs and
   this task's evidence; do not claim a separate implementation review before it occurs.

No implementation of F8 is included. A follow-up proposal can distinguish
provider-interrupted sessions from failed discovery, but must separately specify
status, checkpoint compatibility, resumption, replacement and historical-data policy.

## Progress and decisions

- [x] Read repository guidance, the research-change skill, task template and current
  error-handling guide; inspected the dirty working tree before investigation.
- [x] Delegated read-only evolution/provider/worker/recovery tracing to the
  investigator role; integrated its report without editing production files.
- [x] Coordinator inspected benchmark, analysis, shared IO, numerical and host
  boundaries; distinguished intentional fallback from lost failure information.
- [x] Ran a focused existing baseline suite in isolated test storage.
- [x] Defined findings, preserved behavior, acceptance criteria and implementation order.
- [x] Revisited domain invariants, scientific validation, application error
  contracts, gateway/database translation and terminal reporting on `118c7db`.
  Added explicit layer responsibilities, propagation paths and acceptance criteria;
  no new test run or independent review was performed for this revision.
- [ ] Implementation — not authorized by the current request.
- [ ] Independent review of an implementation — not performed.

Decisions: no broad renaming, new DomainError/RepositoryError hierarchy, automatic
experiment recovery, changes to statistical undefined cases, logging heartbeat
or copied logging configuration in every layer. A function may catch a known
external error to translate it; it must not both log a terminal failure and raise
it to another reporting boundary.

## Verification and review

Actual baseline command: repository `.codex/workflow/README.md` isolation harness,
using a fresh `/private/tmp/aad-error-plan.*` SQLite DB, data and results paths,
with `PYTHONPATH=src`, then:

```python
pytest.main([
    "-q", "--tb=short",
    "tests/test_error_reporting.py",
    "tests/test_gateway_client.py",
    "tests/test_condition_status.py",
    "tests/test_candidate_evaluation.py",
    "tests/test_architecture_boundaries.py",
])
```

Result: **72 passed in 6.77 seconds**. These are existing regression tests; they
establish current protections, not that every proposed correction already works.
No new tests or backend changes were made. The 72-test result predates the
`118c7db` revision and is not claimed as a fresh check of that commit. The full suite and live scenarios
were not run. No production checkpoint was unpickled or study artifact modified.

Investigation: independent read-only investigator plus coordinator inspection.
Review: coordinator self-review of this plan; no independent implementation
review or approval is claimed. All findings remain open for implementation.

## Handoff

Completed: investigation, existing baseline checks and this plan.
Next action: obtain agreement to implement the scoped plan, then start with step 1.

Before implementation, resolve the concrete nonfatal diagnostic path for optional
maintenance and the ownership/API of calculated-result persistence reporting.
These are design choices within the requested scope; prefer existing collaborators
and typed data over new general infrastructure. They must not alter commit,
scientific outcome or recovery semantics.

If the desired scope includes interruption-aware recovery or strict rejection of
historically tolerated trace rows, record that as a separate behavior decision
before changing code. Existing dirty working changes must remain intact.
