# LLaMEA Component Architecture (Decoupled Persistence)

This document outlines the decoupled architecture and communication flow between the orchestration layer (`LLaMEASession`), the execution layer (`Evaluator`), the integration layer (`LLaMEAFrameworkLogger`), and the persistence layers (`ExperimentRepository` and `CodeRepository`).

## 1. Class & Component Diagram

The following Mermaid class diagram illustrates the structural relationships, dependencies, and interfaces between the core components:

```mermaid
classDiagram
    class LLaMEASession {
        -int _run_id
        -BBOBProblem _problem
        -LLMClient _llm_client
        -ExperimentRepository _db_repo
        -CodeRepository _code_repo
        +run() SessionResult
    }
    
    class Evaluator {
        -BBOBProblem _problem
        -ExperimentRepository _db_repo
        -AlgorithmExecutor _executor
        +__call__(solution) Solution
    }
    
    class LLaMEAFrameworkLogger {
        -CodeRepository _code_repo
        -ExperimentRepository _db_repo
        +log_population(population)
        +flush_remaining()
    }
    
    class ExperimentRepository {
        <<Interface>>
        +reserve_run_id() int
        +init_run_checkpoint()
        +append_iteration(metadata)
        +commit_and_cleanup()
    }
    
    class CodeRepository {
        <<Interface>>
        +save(history)
    }

    class LLaMEA {
        <<External Library>>
        +run()
    }

    LLaMEASession --> Evaluator : "creates"
    LLaMEASession --> LLaMEAFrameworkLogger : "creates"
    LLaMEASession --> ExperimentRepository : "uses"
    LLaMEASession --> CodeRepository : "uses"
    LLaMEASession --> LLaMEA : "initializes & orchestrates"
    
    LLaMEA o-- Evaluator : "delegates to (fitness fn)"
    LLaMEA o-- LLaMEAFrameworkLogger : "delegates to (logging hooks)"
    
    Evaluator --> ExperimentRepository : "appends JSONL checkpoints"
    LLaMEAFrameworkLogger --> CodeRepository : "saves python code files"
```

## 2. Detailed Communication Flow

The following sequence diagram illustrates the lifecycle of a single evolutionary run and how responsibilities are delegated among the classes over time:

```mermaid
sequenceDiagram
    autonumber
    participant Session as LLaMEASession
    participant DBRepo as ExperimentRepository (DB)
    participant LLaMEA as LLaMEA (Optimizer)
    participant Eval as Evaluator
    participant Logger as LLaMEAFrameworkLogger
    participant CodeRepo as CodeRepository (FS)

    %% 1. Initialization and Reservation
    Note over Session, DBRepo: 1. Setup & Orchestration
    Session->>DBRepo: reserve_run_id()
    DBRepo-->>Session: run_id

    %% 2. Run Execution Starts
    Session->>+Session: run()
    
    %% 3. Evaluator Setup
    Session->>DBRepo: init_run_checkpoint()
    Note right of DBRepo: Prepares JSONL cache
    Session->>Eval: __init__(problem, db_repo, run_id)
    
    %% 4. Optimizer & Logger Setup
    Session->>LLaMEA: __init__(f=Evaluator)
    Session->>Logger: __init__(code_repo, db_repo, run_id)
    Session->>LLaMEA: attach logger (optimizer.log = True)
    
    %% 5. Evolution Loop
    Note over Session, CodeRepo: 2. Evolution Loop (LLaMEA)
    Session->>+LLaMEA: run()
    loop Every Generation
        %% 5.a Evaluation
        LLaMEA->>+Eval: __call__(solution)
        Eval->>Eval: execute_algorithm(solution.code)
        Eval->>Eval: calculate_fitness()
        Eval->>DBRepo: append_iteration(metadata)
        Note right of DBRepo: Appends iteration to fast JSONL
        Eval-->>-LLaMEA: solution (with fitness/feedback)
        
        %% 5.b Logging (Framework Integration)
        LLaMEA->>Logger: log_population(population)
        opt if generation % flush_every == 0
            Logger->>CodeRepo: save(history)
            Note right of CodeRepo: Flushes code files to disk
        end
    end
    LLaMEA-->>-Session: Return optimizer state
    
    %% 6. Finalization & Cleanup
    Note over Session, DBRepo: 3. Finalization & Persistence
    Session->>Logger: flush_remaining()
    Logger->>CodeRepo: save(pending_history)
    Session->>CodeRepo: save(final_history)
    
    %% 7. Commit to DB
    Session->>DBRepo: commit_and_cleanup(run_id)
    Note right of DBRepo: bulk_sync_run(): Reads JSONL -> Bulk Inserts to SQLite
    
    Session-->>-Session: Return SessionResult
```
