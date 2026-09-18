# System Architecture Design

This document details the component-level architecture of the `AAD_LLM` system, using the C4 Model (Level 2: Container/Component Diagram) represented via Mermaid. It details the bounded contexts, component responsibilities, and how evolutionary synthesis, benchmark evaluation, database persistence, and LLM inference interact.

---

## 1. 🗺️ C4 Component Diagram (Level 2)

```mermaid
graph TB
    %% Styling Definitions
    classDef person fill:#08427b,stroke:#052e56,color:#fff,stroke-width:2px,rx:10px,ry:10px;
    classDef app fill:#0f766e,stroke:#115e59,color:#fff,stroke-width:2px,rx:6px,ry:6px;
    classDef domain fill:#0369a1,stroke:#075985,color:#fff,stroke-width:2px,rx:6px,ry:6px;
    classDef infra fill:#4338ca,stroke:#3730a3,color:#fff,stroke-width:2px,rx:6px,ry:6px;
    classDef external fill:#7c3aed,stroke:#6d28d9,color:#fff,stroke-width:2px,rx:6px,ry:6px;
    classDef db fill:#374151,stroke:#1f2937,color:#fff,stroke-width:2px,shape:cylinder;

    User(["🧑‍💻 Researcher / Experimenter"]):::person
    Client["📓 Jupyter Notebooks / CLI Tasks"]:::app

    %% --------------------------------------------------------
    %% BOUNDED CONTEXT: EVOLUTION
    %% --------------------------------------------------------
    subgraph EvolutionContext ["🧬 Evolution Bounded Context (src/evolution/)"]
        direction TB
        
        subgraph EvoApp ["Application Layer"]
            SynthesisCampaignUseCase["⚡ SynthesisCampaignUseCase<br/>(Campaign Multiprocessing Use Case)"]:::app
            SingleSynthesisUseCase["🎯 SingleSynthesisUseCase<br/>(Single-Run Use Case)"]:::app
        end

        subgraph EvoDomain ["Domain Layer"]
            ExpSummary["📋 ExperimentSummary (Aggregate)"]:::domain
            NoiseStrategies["🎲 NoiseStrategy (Domain Service)"]:::domain
            BaseProblem["📐 BaseProblem (Port)"]:::domain
        end

        subgraph EvoInfra ["Infrastructure Layer"]
            LLaMEAEngine["🚀 LLaMEAEngine (Engine)"]:::infra
            LLaMEASession["⏱️ LLaMEASession"]:::infra
            Evaluator["🎯 Evaluator (Sandboxed Harness)"]:::infra
            BBOBProblem["📈 BBOBProblem (IOH Adapter)"]:::infra
        end
    end

    %% --------------------------------------------------------
    %% BOUNDED CONTEXT: BENCHMARKING
    %% --------------------------------------------------------
    subgraph BenchmarkingContext ["📊 Benchmarking Bounded Context (src/benchmarking/)"]
        direction TB
        EvalService["⚙️ EvaluationService"]:::app
        Baselines["📉 Baseline Algorithms<br/>(CMA-ES, DE, PSO, etc.)"]:::domain
        BenchStorage["💾 Benchmark Storage Repo"]:::infra
    end

    %% --------------------------------------------------------
    %% SHARED FOUNDATION & EXTERNAL
    %% --------------------------------------------------------
    subgraph SharedComponents ["🧱 Shared Foundation (src/shared/)"]
        direction TB
        SQLiteRepo["🗄️ SQLiteSynthesisRepository"]:::infra
        CodeRepo["📁 CodeRepository (Filesystem)"]:::infra
        Executor["🛡️ AlgorithmExecutor (Sandboxed)"]:::infra
        DBStorage[("💽 db.sqlite3 (WAL Mode)")]:::storage
        LLMProvider["🤖 LLM Providers (OpenAI, Anthropic, Ollama)"]:::infra
    end

    %% --------------------------------------------------------
    %% STRUCTURAL DEPENDENCIES
    %% --------------------------------------------------------
    User --> Client
    Client -->|Invokes| SynthesisCampaignUseCase
    Client -->|Invokes| EvalService

    %% Evolution Flow
    SynthesisCampaignUseCase -->|Multiprocessing (ProcessPoolRunner)| SingleSynthesisUseCase
    SingleSynthesisUseCase -->|Executes strategy| LLaMEAEngine

    LLaMEAEngine -->|Coordinates| LLaMEASession
    LLaMEASession -->|Instantiates| Evaluator
    LLaMEASession -->|Drives| LLaMEALib
    LLaMEASession -->|Persists summary| SQLiteRepo

    LLaMEALib -->|Queries code mutations| LLMProvider
    LLaMEALib -->|Evaluates candidate| Evaluator
    Evaluator -->|Executes code safely| Executor
    Evaluator -->|Scores objective| BBOBProblem
    Evaluator -->|Logs iteration| SQLiteRepo
    Evaluator -->|Saves python source| CodeRepo
    BBOBProblem -->|Wraps benchmark| IOHExperimenter
    BBOBProblem -->|Applies noise| NoiseStrategies

    %% Benchmarking Flow
    EvalService -->|Evaluates synthesized algorithms| Baselines
    EvalService -->|Persists benchmark metrics| BenchStorage
    BenchStorage --> SQLiteRepo

    %% Storage Backing
    SQLiteRepo --> DBStorage
```

---

## 2. 🧩 Bounded Contexts & Layer Breakdown

### A. Evolution Bounded Context (`src/evolution/`)
- **Application Layer (`src/evolution/application/`)**:
  - `SingleSynthesisUseCase`: Isolated application use case for executing a single evolutionary algorithm synthesis run in-process without multiprocessing.
  - `SynthesisCampaignUseCase`: Application use case managing matrix auditing, database status reconciliation, task planning, and parallel multi-process dispatching via `ProcessPoolRunner`.
  - `BaseLogger`: Abstract Base Class (ABC) in `interfaces/logger.py` defining logger port interface with default domain telemetry routing.
  - `SynthesisEngine`: Strategy port interface in `interfaces/engine.py` implemented by engines like `LLaMEAEngine`.
  - `SessionConfig` & `SessionResult`: Strongly-typed configuration and execution outcome contracts in `interfaces/engine.py`.
- **Domain Layer (`src/evolution/domain/`)**:
  - `BaseProblem`: Abstract problem contract.
  - `ExperimentSummary`: Aggregate root capturing the lifecycle, metadata, and status of an evolutionary experiment.
  - `NoiseStrategy`: Domain service calculating deterministic, homoscedastic, and heteroscedastic noise perturbations.
- **Infrastructure Layer (`src/evolution/infra/`)**:
  - `engines/llamea/`: Evolutionary synthesis engine and session management (`LLaMEAEngine`, `LLaMEASession`, `Evaluator`).
  - `problems/bbob.py`: Concrete IOHexperimenter problem adapter implementing `BaseProblem`.
  - `storage/`: SQLite database storage (`SQLiteSynthesisRepository`) and filesystem Python source archive (`CodeRepository`).

### B. Benchmarking Bounded Context (`src/benchmarking/`)
- `EvaluationService`: Evaluates champion synthesized algorithms against classical baseline algorithms (e.g. CMA-ES, Differential Evolution, Particle Swarm Optimization).
- `BenchmarkRunRepository`: Manages evaluation runs, convergence data, and comparison metrics.

### C. Shared Kernel (`src/shared/`)
- `AlgorithmExecutor`: Sandboxed runtime execution harness with timeout enforcement (`SIGALRM` / `multiprocessing`) and exception capture.
- `database`: SQLite connection factory with WAL mode, busy timeout, and schema initialization.
