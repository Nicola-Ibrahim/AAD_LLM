# Error handling and diagnostic logs

[Documentation map](../README.md)

Notebook setup creates a `WorkflowScope` that owns DI resources and diagnostic
logging. It prints the diagnostic file location. Service constructors do not
configure global logging handlers.

```python
results = benchmark_coordinator.run_benchmarks(...)
```

Public application methods own their logging boundaries. Notebook cells call
synthesis, benchmarking, audit and analysis services directly; they do not manage
operation contexts. Figure exporters and numerical storage methods also report
their own failures. The boundary records a terminal failure once and re-raises it. It does
not swallow exceptions or turn an unsuccessful operation into an empty result.
The notebook can still display its normal exception traceback; full diagnostics
are also available in the log file.

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
or duplicate the application's error report. The HTTP read timeout remains 600
seconds, with shared throttle waiting additional to that timeout.

The provider context is normally `evolution` or `benchmark`; benchmark also hosts
audit and analysis. Each file rotates at 5 MB, keeping three backups. Rotation is
per invocation; whole invocation directories are not automatically deleted.
These files are operational logs, not scientific result snapshots or archives.

The console retains scientific progress rows, colors and numeric formatting.
Routine debug messages stay in files. Repeated warnings with the same source and
message template are coalesced for the console for 60 seconds; diagnostic files
retain all attempts. Error messages link to the diagnostic file.

Files contain UTC timestamps, severity, module, process and scoped workflow/task/
condition identity, with exception chains. ANSI codes and common bearer/API-key
patterns are redacted. Do not intentionally log credentials, request headers,
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
| Unexpected backend/calculation error | Propagates rather than becoming a candidate failure or fabricated statistic |
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

## Other hosts

An independently composed CLI configures logging at startup and closes it after
workers finish. Application workflow loggers retain their host configuration, so
calling a service directly also establishes context for its worker pool.
Future FastAPI startup/request/shutdown code can establish the same boundaries
and map errors to HTTP responses. Application/domain code contains no HTTP error
mapping, Dishka lookups or logging-output configuration.

Cloud collectors, dashboards and automatic telemetry upload are not configured.
