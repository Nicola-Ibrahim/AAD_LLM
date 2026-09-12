# LLaMEA Evolutionary Synthesis Architecture (Ports & Adapters)

This document details the decoupled Clean Architecture (Hexagonal / Ports & Adapters) design for the evolutionary algorithm synthesis bounded context in `AAD_LLM`.

---

## 1. Architectural Overview: Ports & Adapters (Hexagonal)

The application layer defines the use cases, task orchestrations, and abstract port interfaces. It has **zero dependencies** on third-party optimization libraries (`llamea`). Concrete adapters, engine harnesses, and evaluators live strictly in the infrastructure layer.

```mermaid
graph TD
    subgraph AppLayer ["Application Layer (evolution.application)"]
        SS["SynthesisService<br/>(Campaign & Execution Facade)"]
        ET["EvolutionTask<br/>(Picklable Worker Unit)"]
        TO["TaskOrchestrator<br/>(ProcessPoolExecutor)"]
        BL["&laquo;ABC Interface&raquo;<br/>BaseLogger<br/>(Port in interfaces/logger.py)"]
        SR["SessionResult<br/>(Data Transfer Object)"]
    end

    subgraph DomainLayer ["Domain Layer (evolution.domain)"]
        BP["&laquo;Interface&raquo;<br/>BaseProblem"]
        ES["ExperimentSummary<br/>(Aggregate Root)"]
        PP["ProblemProfile<br/>(Value Object)"]
        NS["NoiseStrategy<br/>(Domain Service)"]
    end

    subgraph InfraEngines ["Infrastructure Engines (evolution.infra.engines.llamea)"]
        LE["LLaMEAEngine<br/>(Engine Adapter)"]
        LS["LLaMEASession<br/>(Lifecycle & Warm-Start Manager)"]
        EV["Evaluator<br/>(Sandboxed Benchmark Harness)"]
    end

    subgraph InfraExternal ["External & Storage (evolution.infra)"]
        EXT_LLAMEA["External llamea Library<br/>(LLaMEA, Solution)"]
        LLM["LLMClient<br/>(Gemini, Local, etc.)"]
        DB["SQLiteSynthesisRepository"]
        CR["CodeRepository"]
        LOG["SynthesisLogger<br/>(Logging Adapter)"]
    end

    %% Dependencies and Relationships
    SS -->|builds| ET
    SS -->|dispatches via| TO
    TO -->|executes across processes| ET
    ET -->|invokes port| SE
    SE -.->|implements| LE
    LE -->|manages| LS
    LS -->|instantiates| EV
    LS -->|initializes & executes| EXT_LLAMEA
    LS -->|returns| SR
    EV -->|evaluates candidate| BP
    EV -->|persists telemetry| DB
    EV -->|saves source code| CR
    EXT_LLAMEA -->|fitness callback| EV
    EXT_LLAMEA -->|mutation queries| LLM
```

---

## 2. Core Component Responsibilities

| Layer | Component | Architectural Role | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Application** | `SynthesisService` | Application Service | Audits experiment matrix against SQLite DB, reconciles completed vs failed/interrupted runs, constructs `EvolutionTask` units, and provides `run_task` (single-run) and `run_campaign` (multi-process). |
| **Application** | `EvolutionTask` | Work Unit DTO | Self-contained picklable work unit executed inside worker processes. Initializes process-isolated DB connections and executes `LLaMEAEngine`. |
| **Application** | `TaskOrchestrator` | Concurrency Manager | Manages a `ProcessPoolExecutor`, sets up SQLite WAL journal mode, monitors task completion, and aggregates `SessionResult` DTOs. |
| **Application** | `BaseLogger` | Abstract Port (ABC) | Defines base class contract for synthesis telemetry, progress reporting, and metric summaries. Located in `evolution.application.interfaces`. |
| **Application** | `SessionResult` | Response DTO | Immutable contract encapsulating the outcome of an evolutionary synthesis run (best error, run history, champion solution, problem profile). |
| **Infrastructure** | `LLaMEAEngine` | Concrete Synthesis Engine | Instantiates and coordinates `LLaMEASession` for a single run. |
| **Infrastructure** | `LLaMEASession` | Lifecycle Manager | Manages prompt injection, warm-start checkpointing (`llamea_config.pkl`), evaluator instantiation, LLaMEA loop execution, and status transitions. |
| **Infrastructure** | `Evaluator` | Evaluation Adapter | Wraps candidate Python code in `AlgorithmExecutor`, enforces timeouts and domain bounds, penalizes crashes/infeasibilities, captures runtime feedback, and persists telemetry to SQLite. |
| **Infrastructure** | `SynthesisLogger` | Logging Adapter | Implements `BaseLogger` using Python's standard `logging.Logger` with ANSI colors and formatted banners. |

---

## 3. Class & Interface Diagram

```mermaid
classDiagram
    class BaseLogger {
        <<ABC>>
        +bool verbose*
        +header(title, subtitle, width)*
        +task_start(...) *
        +generation(...) *
        +audit_summary(...) *
        +summary(...) *
        +info(msg: str)*
        +warning(msg: str)*
        +error(msg: str)*
    }

    class SynthesisLogger {
        -logging.Logger logger
        +info(msg: str)
        +warning(msg: str)
        +error(msg: str)
        +header(title, subtitle, width)
        +task_start(...)
        +generation(...)
        +summary(...)
    }

    class LLaMEAEngine {
        +run(problem, experiment_id, prompt_strategy, llm_client, db_repo, code_repo, config, ...) SessionResult
    }

    class LLaMEASession {
        -LLaMEA llamea
        -Evaluator evaluator
        +run() SessionResult
        -_resume_or_initialize()
        -_checkpoint()
    }

    class Evaluator {
        -AlgorithmExecutor executor
        +evaluate(code_str) dict
        +is_failure(score) bool
    }

    class SynthesisService {
        -SQLiteSynthesisRepository sqlite_repo
        -SynthesisConfigRepository config_repo
        -LLMClient llm_client
        -BaseLogger logger
        +audit_matrix() tuple
        +build_tasks() list~EvolutionTask~
        +run_task(task, verbose) SessionResult
        +run_campaign(verbose) dict~str, SessionResult~
    }

    class EvolutionTask {
        +str key
        +BaseProblem problem
        +LLMClient llm_client
        +int experiment_id
        +SessionConfig config
        +__call__() SessionResult
    }

    class SessionResult {
        +int problem_id
        +int dim
        +SynthesisMode mode
        +float noise_std
        +int experiment_id
        +float best_error
        +list run_history
        +str experiment_name
        +str llm_name
        +Any best_solution
        +ProblemProfile problem_profile
    }

    BaseLogger <|-- SynthesisLogger : inherits and implements
    LLaMEAEngine --> LLaMEASession : delegates to
    LLaMEASession --> Evaluator : instantiates
    SynthesisService --> EvolutionTask : builds
    EvolutionTask --> LLaMEAEngine : instantiates and runs
    SynthesisService --> BaseLogger : logs via
    LLaMEASession --> SessionResult : returns
```

---

## 4. Execution Flow & Concurrency Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Researcher / Notebook
    participant Service as SynthesisService (App)
    participant Orch as TaskOrchestrator (App)
    participant Worker as Worker Process (ProcessPool)
    participant Task as EvolutionTask (App)
    participant Engine as LLaMEAEngine (Infra)
    participant Session as LLaMEASession (Infra)
    participant LLaMEA as LLaMEA Optimizer (External)
    participant Eval as Evaluator (Infra)
    participant DB as SQLite DB (Infra)

    User->>Service: run_campaign() (or run_task())
    Service->>Service: build_tasks() (audit DB, partition matrix)
    Service->>Orch: run(tasks)
    Orch->>DB: setup_storage_environment() (WAL mode)
    
    par Across Worker Processes
        Orch->>Worker: _execute_task(task)
        Worker->>Task: task()
        Task->>DB: initialize_sqlite_storage()
        Task->>Engine: new LLaMEAEngine() & engine.run(...)
        Engine->>Session: new LLaMEASession(...) & session.run()
        
        Session->>DB: save_experiment_summary(RUNNING)
        Session->>Eval: new Evaluator(...)
        Session->>LLaMEA: instantiate / warm_start()
        Session->>LLaMEA: run()
        
        loop Every Generation (Evolution Loop)
            LLaMEA->>Eval: __call__(candidate_solution)
            Eval->>Eval: AlgorithmExecutor.execute()
            Eval->>DB: append_iteration_log()
            Eval-->>LLaMEA: solution (fitness, feedback)
        end
        
        LLaMEA-->>Session: Champion Solution
        Session->>DB: save_experiment_summary(COMPLETED)
        Session->>Session: cleanup_archive_dir()
        Session-->>Engine: SessionResult
        Engine-->>Task: SessionResult
        Task-->>Worker: SessionResult
        Worker-->>Orch: SessionResult
    end

    Orch-->>Service: dict[str, SessionResult]
    Service->>Service: log_summary()
    Service-->>User: dict[str, SessionResult]
```

---

## 5. Key Architectural Guarantees

1. **Clean Service & Task Separation**:
   `SynthesisService` acts as the single entry point for planning and execution (`audit_matrix`, `build_tasks`, `run_task`, `run_campaign`), while `EvolutionTask` encapsulates self-contained execution inside worker processes by directly instantiating `LLaMEAEngine`.
2. **Process Isolation & Thread-Safety**:
   Each `EvolutionTask` runs in a separate process with its own SQLite connection operating under `journal_mode=WAL` and `busy_timeout=60000`, preventing lock contention and database corruption.
3. **Robust Warm-Start & Checkpointing**:
   State is pickled to `evolution_state/` each generation. If interrupted, `LLaMEASession` warm-starts from `llamea_config.pkl` and seamlessly resumes generation counts without duplicated iterations.
4. **No Legacy Aliases / Clean Canonical Contracts**:
   Zero backwards-compatibility shims or class aliases are maintained. All callers interact directly with canonical services (`SynthesisService`, `BaseLogger`, `LLaMEAEngine`, `SynthesisLogger`).
