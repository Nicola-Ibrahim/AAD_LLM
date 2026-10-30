# Error handling and diagnostic logs

[Documentation map](../README.md)

Notebook setup creates a `WorkflowScope` that owns DI resources and diagnostic
logging. It prints the diagnostic file location. Service constructors do not
configure global logging handlers.

```python
outcome = benchmark_coordinator.run_benchmarks(...)  # Supply the usual explicit parameters.
if outcome.is_success:
    results = outcome.value
else:
    print(outcome.error.message)
```

Public workflow APIs return `Result[T]`: successful data in `value`, or a useful
`ApplicationError` in `error`. Errors contain an operation, code, sanitized
message and diagnostic-log location when a host configured one. The original
exception and its cause remain available internally as `outcome.exception`;
that field is excluded from Pydantic serialization and representation. Failed
results never manufacture empty successful datasets.

Application methods catch workflow failures after their operation boundary logs
once, then return a failed Result instead of raising to notebook users. Notebook
cells check `is_success` and clear failed calculated values before later exports.
They do not manage per-cell operation contexts. Internal domain services,
repositories, analysis loaders, trial runners and the registered synthesis worker
still raise errors so orchestration, partial-result aggregation and existing
recovery work correctly. Genuine scientific optimizer failures remain recorded
outcomes, not failed application Results.

The existing strict `validate_call` decorators still reject invalid method call
shapes/types before the method runs. Validation performed inside the workflow
returns a failed Result. This distinction is intentional: a future HTTP host
validates its request body and maps the workflow Result to its response.
KeyboardInterrupt/SystemExit are not converted to failed Results. DI setup and
required resource teardown can still raise because no application response exists
at those host lifecycle boundaries.

Notebook figure and numerical-result exporters own their host-level reporting.
Numerical storage adapters translate failures without logging them. Export/host
failures outside the application API propagate after reporting, with calculations
preserved for retry. Full diagnostic chains are available in the log file.

## Files and console

Diagnostic files are written to:

```text
logs/<provider-context>/<UTC-timestamp-and-id>/diagnostics.log
```

New invocation folders use readable, sortable names such as
`2026-10-27_18-53-56_UTC-8a643c85`. Existing logs are left untouched.
From a separate terminal, including while a notebook is busy, read the most
recently updated synthesis log with:

```bash
python scripts/show_logs.py --lines 60
```

Use `--workflow benchmark` for benchmark/analysis logs. This command only reads
logs; it does not start or retry work.

Gateway and LLM client adapters do not configure or emit logs. They retain bounded
transport retries and shared pacing, then translate terminal provider failures
into `ProviderError`, preserving the SDK exception as the cause. Application
operation boundaries report the propagated failure once, with workflow context.
Transient retries are intentionally silent; these adapters do not report progress
or duplicate the application's error report. Generation uses a 600-second HTTP read timeout and up to three retries (four
attempts per query). Shared pacing waits are additional. The explicit startup
ping makes one attempt using the configured client timeout. Provider defaults
control output length; no additional token cap or finish-reason rejection is
applied. Normal candidate parsing and execution validation remain in place.

The provider context is normally `evolution` or `benchmark`; benchmark also hosts
audit and analysis. Each file rotates at 5 MB, keeping three backups. Rotation is
per invocation; whole invocation directories are not automatically deleted.
These files are operational logs, not scientific result snapshots or archives.

The console retains scientific progress rows, colors and numeric formatting.
Routine debug messages stay in files. Repeated warnings with the same source and
message template are coalesced for the console for 60 seconds; diagnostic files
retain all attempts. Error messages link to the diagnostic file.

Files contain UTC timestamps, severity, module, process and scoped workflow/task/
condition identity, with exception chains. SDK/HTTP exception messages and response
bodies are omitted from diagnostic rendering; the original cause remains attached
within its process. Worker provider errors transport safe cause text and exception
type rather than live SDK requests or private response text. LLaMEA's duplicate
rendered exception events are suppressed; dependency guards still surface terminal
errors. ANSI codes and common bearer/API-key patterns are redacted. Do not intentionally log credentials, request headers,
environment values or full prompt histories.

Each process-pool worker sends records through a queue; the parent alone writes
files and formats notebook output. Library stdout/stderr is captured only in
these dedicated workers. The notebook parent's global streams are not redirected,
including around benchmark candidate threads. Third-party output in that process
can therefore still appear if the library offers no safe verbosity hook.

Run `services.close()` to release resources early; repeated setup closes the old
scope. Ordinary kernel shutdown also invokes cleanup. Restart the kernel after
updating code; already-running workers do not reload changes.

## Failure policy

| Failure | Behavior |
| --- | --- |
| Generated optimizer runtime/return/timeout failure | Recorded under existing scientific failure rules |
| Terminal model-provider error | Raised as `ProviderError` with its SDK cause; never assigned candidate fitness |
| Required database/artifact write failure | Raised with operation/target context; not reported as completed |
| Missing optional data | Existing missing-data and eligibility rules remain in force |
| Corrupt or unreadable existing provenance | `INVALID_ARTIFACT` in workload/audit; execution stops before replacement |
| Corrupt artifacts in analysis | Loading raises `ArtifactError`; the reduced dataset is not silently presented as complete |
| Known undefined statistical calculation | Existing unavailable numerical result retained |
| Unexpected backend/calculation error | Propagates internally to a failed application Result; never becomes a candidate failure or fabricated statistic |
| User interruption | Propagates; unfinished work is not a successful scientific observation |

Bounded retry and pacing remain in the gateway adapter. Exhausted retries and
authentication/quota failures propagate to the application. The synthesis pool
admits at most its worker capacity at once and stops admitting further work after
a systemic provider/storage/artifact error. Already-running tasks are allowed to
finish; this is not a hard-kill cancellation mechanism. The raised orchestration
error retains successful task results and task failures.

The LLaMEA adapter checks terminal dependency failures around its initialization
and mutation hooks so the library cannot silently convert them into candidate
penalties. Trusted historical checkpoints are loaded through the same guard.
Optimizer mathematics, parent/offspring selection, budgets and timeout mechanisms
are unchanged.

Figure-export methods return `ExportSummary(written, skipped)`. Empty data is an
explicit skip; PNG write failures raise with target context. Calculated results
remain usable if export fails. Export is still PNG-only with the same output names.

CLI tools retain intentional interactive/machine-readable stdout and existing
exit behavior. Discovery warnings go to stderr; backup cleanup preserves the
primary failure, including cancellation. No logging/DI setup is required merely
to call shell maintenance commands.

## Layer responsibilities and secondary diagnostics

Domain code enforces scientific and lifecycle invariants without configuring or
emitting operational logs. Application code distinguishes scientific optimizer
outcomes from failures of the workflow. Infrastructure catches narrowly to
translate external failures and preserve causes; it does not log terminal errors
before raising them to the application. A future HTTP host can map Result errors
to responses without importing HTTP exceptions into the core or logging twice.

Returned-point rule violations retain their historical `ValueError` scientific
diagnostics and penalties. A raised clean-scoring or bounds-adapter defect is a
backend failure, not evidence that the optimizer failed. Such defects now
propagate to the application, which returns a failed Result rather than generating
fabricated terminal optimizer observations.
Genuine nonfinite returned objectives retain their existing scientific treatment.
Budgets, timing boundaries, scoring mathematics and retry settings are unchanged.

Cleanup preserves an active primary failure and attaches sanitized secondary
notes before the terminal report where the resource owner controls the boundary.
A sole required logger flush/merge or resource teardown failure propagates.
Optional passive WAL checkpoints, completed-checkpoint removal and temporary-file
cleanup stay nonfatal. They produce scoped diagnostics collected by the owning
application operation; standalone calls use the shared application warning logger.
No warnings-as-errors policy can turn these diagnostics into scientific failures.
Tolerated malformed trace rows are counted per file and reported through the same
boundary, preserving existing parsing, carry-forward and inclusion behavior.

`AnalysisResultsStore` performs versioned snapshot IO without reporting, database
queries or calculations. `notebooks/analysis/result_exports.py` owns snapshot/CSV
export and reload reporting for notebook users. Plotting helpers remain separate
and consume only calculated results. Corrupt snapshots raise `ArtifactError` with
the parser/IO cause; invalid caller paths remain input validation errors. Snapshot
schema, hashes, manifest-last writes and established downstream CSV names remain
unchanged.

This refactor does not change experiment statuses or automatic recovery policy.
An exhausted provider request can still mark its synthesis experiment failed;
existing retry settings can select replacement of failed experiments. A missing
positive-iteration checkpoint still refuses resume and never triggers silent
replacement. Interruption-aware recovery is a separately deferred design change.

## Other hosts

An independently composed CLI configures logging at startup and closes it after
workers finish. Application workflow loggers retain their host configuration, so
calling a service directly also establishes context for its worker pool.
Future FastAPI startup/request/shutdown code can establish the same boundaries
and map errors to HTTP responses. Application/domain code contains no HTTP error
mapping, Dishka lookups or logging-output configuration.

Cloud collectors, dashboards and automatic telemetry upload are not configured.
