# System Architecture Design

This document details the component-level architecture of the `AAD_LLM` system, using the C4 Model (Level 2: Container/Component Diagram) represented via Mermaid. It details the boundaries, component responsibilities, and how execution, evaluation, database persistence, and crash recovery interact.

---

## 🗺️ C4 Component Diagram (Level 2)

```mermaid
graph LR
    %% Styling Definitions
    classDef person fill:#08427b,stroke:#052e56,color:#fff,stroke-width:2px,rx:10px,ry:10px;
    classDef internal fill:#0f766e,stroke:#115e59,color:#fff,stroke-width:2px,rx:6px,ry:6px;
    classDef external fill:#7c3aed,stroke:#6d28d9,color:#fff,stroke-width:2px,rx:6px,ry:6px;
    classDef db fill:#374151,stroke:#1f2937,color:#fff,stroke-width:2px,shape:cylinder;

    User(["🧑‍💻 Researcher"]):::person
    Notebook["📓 Notebooks / Scripts"]:::internal

    %% --------------------------------------------------------
    %% BOUNDED CONTEXTS
    %% --------------------------------------------------------

    subgraph CoreContext ["🧱 Core Domain Layer (src/core/)"]
        direction TB
        Dispatcher["⚡ Dispatcher"]:::internal
        
        subgraph CoreLLaMEA ["LLaMEA (src/core/llamea/)"]
            direction TB
            Session["🔄 Session"]:::internal
            Evaluator["🎯 Evaluator"]:::internal
            AlgExecutor["🖥️ Alg Executor"]:::internal
        end

        subgraph CoreCheckpoint ["Checkpointing (src/core/checkpoint/)"]
            direction TB
            CkptManager["💼 Checkpoint Manager"]:::internal
            CkptLogger["📝 Checkpoint Logger"]:::internal
        end
        
        subgraph DomainModels ["Domain Models"]
            Problems["📈 Problem Wrapper"]:::internal
            Schemas["🗂️ Domain Schemas"]:::internal
        end
    end

    subgraph InfraContext ["🌐 Infrastructure Layer (src/infra/)"]
        direction TB
        subgraph InfraStorage ["Storage (src/infra/storage/)"]
            StorageMgr["📂 Storage Manager"]:::internal
            CkptRepo["💾 Checkpoint Repo"]:::internal
        end
        
        subgraph InfraLLM ["LLM (src/infra/llm/)"]
            LLMClient["💬 LLM Client"]:::internal
        end
        SQLite["🛢️ SQLite DB"]:::db
    end

    subgraph ExternalLibraries ["External Packages"]
        direction TB
        LLaMEALib["🧠 LLaMEA Optimizer"]:::external
        BBOBProb["📈 IOH Solver"]:::external
    end

    %% --------------------------------------------------------
    %% STRUCTURAL DEPENDENCIES
    %% --------------------------------------------------------

    User --> Notebook
    Notebook -->|Submits jobs to| Dispatcher
    
    %% Dispatcher
    Dispatcher -->|Instantiates| Session
    Dispatcher -->|Cleans up via| CkptManager
    
    %% Session
    Session -->|Reads/Resumes from| CkptRepo
    Session -->|Runs| LLaMEALib
    Session -->|Creates| Evaluator
    Session -->|Hooks| CkptLogger
    
    %% LLaMEA Execution
    LLaMEALib -->|Queries| LLMClient
    LLaMEALib -->|Evaluates via| Evaluator
    LLaMEALib -->|Logs to| CkptLogger
    
    %% Evaluation
    Evaluator -->|Executes in| AlgExecutor
    AlgExecutor -->|Queries| Problems
    AlgExecutor -->|Calculates fitness on| BBOBProb
    
    %% Storage & Persistence
    CkptLogger -.->|Flushes to| StorageMgr
    CkptManager -->|Persists to| StorageMgr
    CkptManager -->|Deletes| CkptRepo
    StorageMgr -->|Writes to| SQLite

    %% Visual distinction for cross-context lines
    linkStyle default stroke-width:2px,fill:none;
```

---

## 🧩 Component Breakdown

### 1. Core Domain Layer (`src/core/`)
- **Dispatcher (`dispatcher.py`)**: Entry-point module running batch configurations of multiple evolution jobs concurrently under a `ThreadPoolExecutor`. Binds resources and runs database persistence and checkpoint cleanups.
- **LLaMEASession (`llamea/session.py`)**: Consolidated execution orchestrator. Instantiates or warm-starts the LLaMEA algorithm optimizer, runs the core generation iterations, logs outputs, and compiles final metrics.
- **Evaluator (`llamea/evaluator.py`)**: A LLaMEA-compliant evaluator. It executes generated algorithms, measures execution metrics (runtime, CPU cycles, error bounds), penalizes timeouts/crashes, and assigns fitness.
- **Algorithm Executor (`llamea/executor.py`)**: Uses isolated python environment execution tools to securely execute generated source code under strict `timeout` constraints.

#### Domain Models & Solvers
- **BBOB Runtime Wrapper (`problems/bbob.py`)**: Active wrapper loading underlying IOH benchmark problems. Handles bounds querying and validation, resets, and noise injection vectors during runtime evaluations.
- **Domain Schemas (`schema/`)**: Pydantic entities decoupled into granular domain concepts:
  - `problem.py`: Holds `ProblemProfile`.
  - `metrics.py`: Defines intermediate telemetry profiles (`ExecutionProfile`, `FitnessMetrics`, `CodeMetrics`, `ErrorProfile`, `ConvergenceProfile`).
  - `iteration.py`: Structures `IterationMetadata` describing individual candidate execution iterations.
  - `experiment.py`: Defines the aggregated summary entity `ExperimentSummary`.

### 2. Checkpoints & Recovery (`src/core/checkpoint/`)
- **Checkpoint Logger (`logger.py`)**: A custom logger intercepting LLaMEA execution. It writes pickle archives (`llamea_config.pkl`) to disk and flushes data to the repository every $N$ generations to avoid memory congestion.
- **Checkpoint Manager (`manager.py`)**: Coordinates loading, recovery, database persistence, and cleanup of checkpoints created during experiment executions.

### 3. Infrastructure Layer (`src/infra/`)
- **Storage Manager (`storage/manager.py`)**: A database repository facade exposing SQLite writes and managing filesystem blob savings via `CodeBlobSaver`.
- **Checkpoint Repository (`storage/checkpoint/repository.py`)**: Lower-level technical persistence engine managing filesystem checkpoint folder resolution, pickle saves, and serialization.
- **LLM Client (`llm/client.py`)**: Adapts client queries, timeouts, and providers to talk with local or external inference servers.

---

## 🔄 Execution Sequence & Resumption

```mermaid
sequenceDiagram
    autonumber
    actor User as Jupyter Notebook / Dispatcher
    participant Session as LLaMEASession
    participant Logger as Checkpoint Logger
    participant LLaMEA as LLaMEA Optimizer
    participant Manager as Checkpoint Manager
    participant CkptRepo as Checkpoint Repository

    User->>Session: LLaMEASession(problem, checkpoint_repo, ...).run(budget=10)
    Session->>CkptRepo: resolve(problem_id, dim, mode, run_id)
    
    alt Checkpoint File Exists (Resumption)
        CkptRepo-->>Session: Return CheckpointState (pickle_exists=True)
        Session->>Session: LLaMEA.warm_start()
        Note over Session: Resumes state, logs, and population
    else No Checkpoint (Fresh Start)
        CkptRepo-->>Session: Return CheckpointState (pickle_exists=False)
        Session->>Session: Instantiate LLaMEA()
    end

    Session->>Logger: Instantiate CheckpointLogger(archive_dir)
    Session->>LLaMEA: Set optimizer.logger = CheckpointLogger
    Session->>LLaMEA: optimizer.run()

    loop Generations
        LLaMEA->>Logger: log_population(population)
        opt Every N Generations
            Logger->>Logger: Save pickle state (llamea_config.pkl)
            Logger->>Logger: Flush intermediate runs to SQLite DB
        end
    end

    LLaMEA-->>Session: Evolution complete
    Session->>Logger: flush_remaining()
    Session-->>User: Return SessionResult

    Note over User, Manager: Done inside Dispatcher loop:
    User->>Manager: persist_and_cleanup(result)
    Manager->>Manager: Save final history to SQLite DB
    Manager->>CkptRepo: delete(checkpoint_state)
```
