# System architecture

[Documentation map](../README.md) · [Project README](../../README.md)

A modular monolith with two workflow contexts: **evolution** and **benchmark**.
Audit is a capability within those contexts; notebooks own presentation.

## Workflow overview

[Workflow overview](../../README.md#level-0--workflow-overview) ·
[Detailed system diagram](../../README.md#level-1--detailed-system-view) ·
[Level 0 Mermaid source](system_overview.mmd) ·
[Level 1 Mermaid source](system_diagram.mmd)

## Synthesis collaboration

```mermaid
%%{init: {"theme":"base","themeVariables":{"background":"#f2e6ff","lineColor":"#333333","fontFamily":"Arial, Helvetica, sans-serif","clusterBkg":"#f7f7f7","clusterBorder":"#dedede"},"flowchart":{"curve":"stepAfter","nodeSpacing":32,"rankSpacing":48}}}%%
flowchart TD
    accTitle: Synthesis collaboration
    accDescr: Campaign composition dispatches worker-local synthesis sessions; LLaMEA delegates candidate evaluation to shared execution and evolution scoring.
    subgraph Campaign["Campaign composition and dispatch"]
        direction LR
        Bootstrap["EvolutionModule<br/>MODULE ENTRY POINT<br/>Own operation scope<br/>with Dishka providers"]
        Coordinator["SynthesisCampaignCoordinator<br/>EVOLUTION APPLICATION<br/>CampaignAuditor + CampaignPlanner<br/>Reconcile state; build CampaignTask payloads"]
        Dispatcher["ProcessPoolRunner<br/>EVOLUTION INFRASTRUCTURE<br/>Dispatch worker processes<br/>run_synthesis_worker"]
        Bootstrap --> Coordinator --> Dispatcher
    end
    subgraph Session["Worker-local synthesis session"]
        direction LR
        UseCase["SingleSynthesisUseCase<br/>EVOLUTION APPLICATION<br/>Worker-local repository and database<br/>Execute one synthesis session"]
        Engine["LLaMEAEngine / LLaMEASession<br/>EVOLUTION INFRASTRUCTURE<br/>Build prompts; restore trusted checkpoints<br/>Run LLaMEA with Evaluator callback"]
        Evaluator["Evaluator<br/>EVOLUTION INFRASTRUCTURE<br/>Translate Solution into code evaluation<br/>Persist iterations; attach fitness / feedback"]
        UseCase --> Engine --> Evaluator
    end
    subgraph Candidate["Candidate evaluation"]
        direction TB
        Evaluation["CandidateEvaluationService<br/>EVOLUTION APPLICATION<br/>Execute through CandidateExecutor interface<br/>Validate, clean-score and assemble diagnostics"]
        Executor["AlgorithmExecutorAdapter<br/>SHARED INFRASTRUCTURE<br/>Compile, run and capture warnings<br/>func_timeout; require (best_x, best_y)"]
        Scoring["AlgorithmScoringService<br/>EVOLUTION DOMAIN<br/>Shared objective_gap(clean_y, f_opt)<br/>Evolution fitness and failure penalties"]
        Evaluation --> Executor
        Evaluation --> Scoring
    end
    Dispatcher --> UseCase
    Evaluator --> Evaluation
    classDef application fill:#dbeafe,stroke:#2563eb,color:#172554;
    classDef infrastructure fill:#fef3c7,stroke:#d97706,color:#78350f;
    classDef composition fill:#e0e7ff,stroke:#4f46e5,color:#312e81;
    class Bootstrap composition;
    class Coordinator,UseCase,Evaluation,Scoring application;
    class Dispatcher,Engine,Evaluator,Executor infrastructure;
```

Arrows show runtime calls/delegation, not permission for core modules to import adapters.
Fitness and feedback return through the Evaluator callback.
Configuration, repositories, problem factory and LLM client are injected collaborators;
they remain visible in the detailed system diagram rather than repeated as separate
nodes in this focused view.

## Dependency direction

```mermaid
flowchart LR
    Entry[Notebook / CLI / future HTTP] --> Bootstrap[Module façades and composition]
    Bootstrap --> App[Application workflows]
    App --> Ports[Application ports]
    App --> Domain[Domain rules and entities]
    Infra[Infrastructure adapters] -. implements .-> Ports
    Infra --> Domain
    Infra --> External[(SQLite, files, IOH, LLaMEA, solvers, processes)]
```

Solid arrows describe dependencies/composition; the dashed edge means an adapter
implements an interface. Application code does not import its concrete adapter.

| Owner | Responsibilities |
| --- | --- |
| Evolution | Prompts, campaigns, iterations, feedback, fitness penalties and synthesis recovery. |
| Benchmark | Champion selection, trial validity/resumption, audit, reliability, ECDF and transfer. |
| Shared foundation | BBOB/noise definitions, objective gap, problem capabilities, execution and database adapters. |
| Notebooks / infrastructure DI | Composition, labels, Plotly figures and explicit exports. |

Neither context's application/domain imports the other context. Shared code imports
neither context. Benchmark infrastructure may read synthesis records through
read-only adapters; evolution owns synthesis writes. Database sessions are short-lived,
with worker-local engines and the existing SQLite WAL configuration.

[Execution and recovery](execution_flow.md) ·
[Benchmark protocol](../benchmark_protocol.md) ·
[Analysis workflows](../../notebooks/analysis/README.md)

<details>
<summary>Module ownership, persistence and implementation notes</summary>

## Context map and ownership

This is a modular monolith with two workflow contexts, not independent services.

```text
Notebook dashboards / figures / exports
                  ↓ composition in infrastructure DI
        Evolution                 Benchmark
    synthesis + campaign       selection + evaluation + analysis
                  ↓                    ↓
       Shared scientific rules and runtime infrastructure
```

Evolution owns prompts, generation modes, experiment/iteration semantics, fitness
penalties, and campaign coverage. Benchmark owns champion ranking, trial
protocols, condition validity, benchmark coverage, reliability, and transfer studies.
Audit and analysis are workflows, not a third bounded context. Persistence and
candidate runtime are supporting infrastructure, not business contexts.

Shared code must not depend on either context. Neither context's domain or
application imports the other context. Bootstrap may compose both. Benchmark's
read-only SQLite adapters deliberately consume synthesis-owned table projections;
they must not write synthesis state or invoke synthesis workflows. The ORM schema
stays in shared infrastructure for this single-database application; evolution owns
its synthesis-table meaning and writes. Benchmark traces/provenance belong to
benchmark. No database/schema migration is required.

## Dependency direction

The dependency rule for core code is inward: domain code owns scientific rules
and may use numerical/data-model libraries, but does not depend on infrastructure
or application workflows; application code depends on domain and application
ports; infrastructure depends inward on those contracts and outward on external
libraries. Infrastructure Dishka providers construct concrete adapters; notebooks resolve workflows. The dotted adapter
relationship is runtime wiring, not an import from a port to its implementation.
Shared BBOB metadata, objective-problem capabilities, noise mathematics, and the
objective-gap function live in `shared/domain/`. IOH problem construction,
calibration/lifecycle, SQLite, and guarded candidate execution live in
`shared/infra/`. Synthesis mode and `ProblemProfile` are not problem-adapter
capabilities: evolution constructs the profile and passes the session mode.

## Dependency injection and resource scopes

Dishka bindings live only in infrastructure:

| Provider | Ownership |
| --- | --- |
| [SharedProvider](../../src/shared/infra/di.py) | Process-local SQLAlchemy engine/session factory and shared problem factory |
| [EvolutionProvider](../../src/evolution/infra/di.py) | Synthesis repositories, logging, engine, dispatcher and use cases |
| [BenchmarkProvider](../../src/benchmark/infra/di.py) | Champion reads/selection, benchmark execution, audit and analytical collaborators |

Providers use `provide(Service)` for ordinary constructor injection. `AnyOf`
binds a concrete adapter and its existing interface to the same scoped instance.
Factories remain only where construction needs settings, callable adapters,
library defaults or resource finalization. The shared session-factory registration
comes from the owned database engine; repositories do not construct their own engines.

This follows the same division of responsibility as .NET's Generic Host without
imitating its builder syntax: the host owns lifetime, providers register bindings,
and the container constructs services using typed constructor parameters. An API
server is not required. Console/job code can compose these same providers directly;
module façades own operation scopes; callers own module startup and shutdown.

Existing abstract classes are bound only for external or replaceable boundaries
(repositories, code/trace storage, problem creation, logging and task dispatch).
Pure analytical engines and application use cases stay concrete. Provider factories
request these existing interfaces, so replacing an external adapter does not require
rewriting workflow construction. No interface is generated for every class, and
no project-wide scanning or custom `AddScoped` wrapper is used. Register a normal
service with `provide(Service)`; keep experimental inputs as method arguments.

### Interface ownership

An interface belongs to the layer whose concepts it describes, not automatically
to the application layer because Dishka injects it. Returning a domain object
alone is not sufficient: a trace-loading workflow may also return domain data.

| Owner | Contracts | Reason |
| --- | --- | --- |
| Evolution domain | `domain/interfaces/synthesis_repository.py` | Persists and restores experiment domain objects and iteration state |
| Shared scientific domain | `domain/problem.py`, `domain/interfaces/problem_factory.py` | Defines objective-problem capabilities and creation of scientific problem objects |
| Benchmark application | `ChampionRepository`, `SynthesisReadRepository` | Query projections/DataFrames and workflow exports; not repositories for benchmark domain aggregates |
| Benchmark application | `BenchmarkTraceReader`, `BenchmarkStateStore`, `CandidateCodeReader` | Workflow IO, provenance, trace lifecycle and code access |
| Evolution application | `SynthesisEngine`, `SynthesisCodeStore`, `TaskDispatcher`, `DuplicateStorage` | Synthesis execution, source artifacts, dispatch and maintenance workflows |
| Shared application | `CandidateExecutor` | External generated-code execution, warnings and timeout boundary |
| Context application packages | `BaseLogger`, `BenchmarkLoggerInterface` | Workflow telemetry rather than scientific rules |

Concrete adapters remain in infrastructure and implement these contracts. The
domain repository does not expose SQLite WAL checkpointing; that method remains
an internal capability of `SQLiteSynthesisRepository`, with its existing calls
and database behavior unchanged. Domain modules may not import application,
infrastructure or Dishka. No replacement interface was introduced for WAL work.

### Module entry points and lifetimes

[EvolutionModule](../../src/evolution/infra/module.py) and
[BenchmarkModule](../../src/benchmark/infra/module.py) are the public runtime
entry points for notebooks, console programs and a future HTTP host. Each instance
builds one process-local Dishka root from its context provider and SharedProvider.
Construction validates the graph but does not launch a campaign or eagerly open a
database.

Each public operation opens a fresh REQUEST/job scope, resolves the existing use
case, invokes it directly, and closes the scope on return or exception. There is
no mediator, command bus, global container or service locator in application/domain
code. Façades contain only typed argument forwarding, validated analysis-settings
construction, and lifecycle handling. Analytical calculations stay in domain
engines; application use cases still own loading and orchestration.

The database engine/session factory and caller-owned LLM client have APP/process
scope. Repositories, mutable loggers, workload coordinators and analysis use cases
have operation scope. Repositories continue opening short-lived database sessions
per operation. The root retains its engine until module shutdown; WAL, foreign
keys, busy timeout and synchronous settings remain the database adapter's job.

```python
from evolution.infra.module import EvolutionModule
from benchmark.infra.module import BenchmarkModule

evolution = EvolutionModule(llm)
benchmark_module = BenchmarkModule()
try:
    results = evolution.run_campaign(**synthesis_parameters)
    outcomes = benchmark_module.run_benchmarks(
        solver_type="champions", **benchmark_parameters
    )
    coverage = benchmark_module.audit_coverage(**benchmark_parameters)
finally:
    evolution.close()
    benchmark_module.close()
```

In notebooks, setup initializes a module once and registers one normal-process
shutdown callback. Rerunning setup closes and unregisters the previous module
before replacing it. No notebook ExitStack, per-operation scope management, or
live repository/use-case bundle is exposed. Calculations and numerical persistence
are separate module calls; figures and CSV presentation remain notebook-owned.

Only detached data is returned: DataFrames, calculated result classes, champion
catalogs, paths and immutable model-registry entries. Operation scopes never
escape through module APIs. A failed operation closes its scope but leaves the
module root available for a new operation. Analysis settings are passed per call,
not retained as mutable module configuration. Module close is idempotent; calls
after close fail explicitly. Modules reject serialization and cross-process
operation calls. Caller-owned LLM clients are not closed.

The host must call close during graceful shutdown, after draining active jobs.
Notebook atexit is only a fallback for normal interpreter exit; force-killing a
process cannot guarantee finalization. Recreate the module when switching an
imported database or infrastructure configuration. Scientific settings remain
explicit method arguments, with existing Pydantic validation in use cases and
analysis configuration models.

Synthesis workers open their own container inside the worker process, then resolve
`SingleSynthesisUseCase` with the engine already in the unchanged task payload.
No container, database engine or session is serialized into a task. The module-level
worker stays picklable. Detached numerical results remain usable after scope exit.

The scope and generator-finalization mechanisms follow the
[Dishka container documentation](https://dishka.readthedocs.io/en/stable/container/index.html).
Service registration and constructor injection follow the
[Dishka quickstart](https://dishka.readthedocs.io/en/stable/quickstart.html).

### Future FastAPI entry point

FastAPI is not implemented by this change. A future server will assemble the same
`SharedProvider`, `EvolutionProvider` and `BenchmarkProvider` in its composition
The API lifespan initializes the two module instances once and closes them on
shutdown. Routes call their public methods; module-internal containers are not
registered in an API-global service locator. An API container may inject the
module objects into handlers, but each module still owns its internal operation
scope. No notebook setup is imported. Service constructors and scientific methods
do not change.

The module methods and current adapters are synchronous. Keep blocking calls in
synchronous handlers or dedicated jobs, and use async containers only if future
adapters actually need them. Do not run
blocking synthesis/benchmark campaigns directly in an async event loop. Long jobs
need worker/job lifetimes separate from HTTP request lifetimes; never pass request
repositories, sessions or containers into the existing process-pool payload.
Analysis method arguments become a fresh validated `BenchmarkConfig` inside each
module operation; the worker engine context remains process-local.
See [Dishka's FastAPI integration](https://dishka.readthedocs.io/en/stable/integrations/fastapi.html).

## Evolution context (`src/evolution/`)

- `application/campaign/` separates audit, task planning, and campaign dispatch.
  `application/synthesis/` groups the single-session and candidate-evaluation use cases.
- `domain/interfaces/` owns the synthesis experiment repository contract.
  `application/interfaces/` owns engine, logging, code-store, dispatch and maintenance
  contracts. The problem-factory contract belongs to the shared scientific domain;
  isolated execution belongs to shared application.
  Worker functions remain module-level for process pickling.
- `domain/` owns experiment entities, synthesis enums, and `AlgorithmScoringService`
  (fitness and failure classification using the shared objective gap).
- `infra/` adapts SQLite/files, LLaMEA, logging, synthesis telemetry, and multiprocessing.

Notebook 02 calls `EvolutionModule` methods; its operation scope prepares the
coordinator, repositories, problem factory, engine and automatically sized dispatcher. Setup does
not read study configuration files. The notebook supplies flat validated method arguments;
the coordinator builds a fresh planner and configuration for each invocation.
Benchmark composition injects concrete workload and trial-runner objects. Each
invocation passes its validated settings to their methods, without factories or
mutable service configuration. No previous call's settings are retained. See the
[parameter inventory](../configuration/model_configuration.md#explicit-study-parameters).
The module-level worker calls `SingleSynthesisUseCase`; `LLaMEAEngine` implements
the synthesis engine interface and delegates a session to `LLaMEASession`.
Its infrastructure `Evaluator` translates LLaMEA solutions into calls to
`CandidateEvaluationService` and persists iteration telemetry. The shared
`AlgorithmExecutorAdapter` implements the candidate executor interface;
`BBOBProblemFactory` implements the problem factory interface. These are runtime
collaborations, not imports from application code into infrastructure.

For dispatch and checkpoint steps, see [execution and recovery](execution_flow.md).
For scoring and execution limitations, see [evaluation protocol](../benchmark_protocol.md).

Candidate execution is coordinated by the application: shared infrastructure runs
generated Python and captures warnings, while the application measures runtime
and assembles exception diagnostics. Scoring is a
domain policy specific to synthesis; both workflows use the shared objective-gap
calculation without sharing fitness penalties. Use the application
candidate-evaluation service and executor port directly; the domain contains no
generated-code execution.

## Benchmark context (`src/benchmark/`)

- `application/trials/` separates workload discovery, per-condition trials,
  batch execution, and coverage auditing. `select_champions.py` owns ranking.
- `application/analysis/` contains injected analysis use cases. A shared loader
  reads validated snapshots; profile, reliability, noise-robustness and performance
  use cases call domain engines and return calculated arrays/tables.
  Numerical snapshots and CSV statistics remain separate from figure export.
- `domain/` owns benchmark-independent reliability, ECDF, performance, and statistical
  calculations.
- `infra/` owns SQLite candidate queries and benchmark state, champion JSON and trace
  IO, numerical snapshot storage, code loading, and CMA-ES/DE/PSO adapters. IOH problem
  lifecycle/noise calibration and candidate execution are shared infrastructure.

The notebook composition functions wire concrete problem, execution, solver, and
code-reading adapters. Model-registry TOML loading is infrastructure work; the
domain's `ModelNames` formats names from supplied registry records. Both workflows
use the same shared BBOB function definition. Champion selection policy is
application-owned; repositories return candidate records and persist exports.

## Audit and analysis boundaries

The independent workflow is named `benchmark`: notebook `03_benchmark.ipynb`
calls `BenchmarkModule`; live workload and repository objects stay inside each operation.
The provider composes `BenchmarkCoordinator` and its adapters; method parameters
create the validated `BenchmarkConfig`. Configuration
uses `trials_per_condition`, `trial_timeout_seconds` and
`noise_robustness_enabled`; old workflow imports are not forwarding aliases.
Synthesis candidate evaluation and objective-evaluation counts retain their
scientific names. Recorded provenance keys such as `evaluation_schema_version`,
`evaluation_kind` and `evaluations_used` retain their existing serialized format.

Inside `application/trials/`, `coordinator.py` coordinates injected workload and trial
collaborators; the infrastructure provider owns their construction. `workload.py` discovers typed
tasks carrying exact selected champions, then projects them into audit tables.
`runner.py` resumes and executes those conditions using one record per terminal
trial rather than parallel mutable columns. `models.py` contains these application
records and callable dependency types. `summary.py` produces read-only outcome
summaries; `audit.py` reports coverage. Scientific validity, trial identities and
outcome calculations remain domain policies; the storage adapter owns native and
transfer directory layouts. Partial histories with incompatible execution versions
are reported consistently by readiness and refused by resumption without deletion;
complete compatible-schema historical results remain reusable.

Notebook 04 passes expected synthesis coverage as plain condition specifications
to `BenchmarkModule(planned_conditions=...)`, then calls `audit_coverage()`. The benchmark audit reports missing champions
separately from executable condition completion and reuses the pure status policy
used by workload discovery and trial resumption. Stale schema/hash results expose
recorded counts but contribute zero reusable trials. Native, noise robustness,
implicit/explicit origins, and cross-function conditions never substitute for one
another. Baselines do not require a synthesis champion.

Audit returns numeric IDs, counts, reasons, and statuses. Notebook 04 owns icons,
labels, heatmaps, CSV exports, and the Markdown dashboard. Analysis use cases receive
required loaders and engines through constructor injection.
Analysis notebooks pass explicit scientific settings to the module's four
`analyze_*` methods; the module opens and closes each operation scope. Application use cases load an
internal snapshot and calculate results without writes. Notebooks receive detached
scientific results and resolved metadata, not live repositories or engine services.
Plotly builders consume those results; `AnalysisFigureExporter` orchestrates PNG
export under `notebooks/analysis/plotting/`, without figure caching.
`infra/storage/analysis_results_store.py` owns numeric persistence, separately composed
by the same provider: compressed arrays, CSV statistics and provenance manifests under
`results/analysis/`, plus established report CSVs. Reloading restores detached
results without database access or calculation. Calculation does not depend on export
requests. Only intermediate numerical results are persisted for reuse, not
Plotly objects or image-export state. Every export call rebuilds and writes PNGs.
Terminal trial completion and available
convergence traces remain distinct: missing traces are not fabricated.

Architecture tests enforce layer direction, context independence, shared-foundation
independence, the absence of backend presentation dependencies, and the absence
of scientific calculation/data-loading calls in figure builders.

## Data and imports

Imports are explicit from the owning layer; compatibility shims are not maintained.
Configuration keys, notebook entry points,
champion JSON shape, traces, and existing experiment data are preserved; this refactor
does not regenerate benchmark results.

Historical synthesis pickle checkpoints use an infrastructure reader that translates
the six relocated scientific/runtime type module names during deserialization.
It preserves pickle state and normal rehydration hooks without restoring obsolete
Python modules or rewriting archives. As before, only trusted local pickle archives
may be loaded; this is not a security sandbox for checkpoint files.

</details>
