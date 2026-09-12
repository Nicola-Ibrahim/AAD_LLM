# Execution Sequence & Concurrency Lifecycle

This document illustrates the execution lifecycle, process concurrency, and warm-start resumption mechanisms in the `AAD_LLM` system.

---

## 1. Multi-Process Synthesis Execution Flow

The following sequence diagram captures the end-to-end flow from experiment campaign invocation down to isolated worker execution and result aggregation:

```mermaid
sequenceDiagram
    autonumber
    actor User as Notebook / CLI Runner
    participant Service as SynthesisService
    participant Orch as TaskOrchestrator
    participant Worker as Worker Process (ProcessPool)
    participant Task as EvolutionTask
    participant Engine as LLaMEAEngine
    participant Session as LLaMEASession
    participant LLaMEA as LLaMEA Optimizer
    participant Eval as Evaluator
    participant DB as SQLite DB (WAL)

    User->>Service: run_campaign() (or run_task())
    Service->>Service: audit_matrix() (DB reconciliation)
    Service->>Service: build_tasks() (fresh, resume, targeted)
    Service->>Orch: run(tasks)
    Orch->>DB: setup_storage_environment() (WAL pragma)

    par Parallel Work Units Across Workers
        Orch->>Worker: _execute_task(task)
        Worker->>Task: task.__call__()
        Task->>DB: initialize_sqlite_storage()
        Task->>Engine: new LLaMEAEngine() & engine.run(...)
        Engine->>Session: LLaMEASession(...) & session.run()

        alt Warm-Start Checkpoint Exists (Resumption)
            Session->>Session: LLaMEA.warm_start(archive_dir)
            Note over Session: Resumes generation count and history
        else Fresh Experiment
            Session->>Session: Instantiate LLaMEA(...)
        end

        Session->>Eval: setup_evaluator()
        Session->>LLaMEA: run()

        loop Generations (Budget Iterations)
            LLaMEA->>Eval: __call__(solution)
            Eval->>Eval: AlgorithmExecutor.execute()
            Eval->>DB: append_iteration_log()
            Eval-->>LLaMEA: solution with fitness/feedback
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
    Service-->>User: Campaign Results Summary
```

---

## 2. Crash Recovery & Resumption Lifecycle

1. **State Persistence**:
   During active evolution runs, checkpoints (`llamea_config.pkl`) are maintained in `data/evolution_state/{dim}D/std_{noise}/f{problem_id}/experiment_{id}/`.
2. **Crash Interruption Detection**:
   When `SynthesisService.audit_matrix()` inspects the database, any experiment whose status remains `running` is earmarked for resumption.
3. **Resumption Dispatch**:
   `SynthesisService._build_resume_task()` creates an `EvolutionTask` with `initial_iteration` set to the number of existing iterations already recorded in the database.
4. **Warm Start**:
   `LLaMEASession._create_synthesis_engine()` invokes `LLaMEA.warm_start()`, restores the existing population and generation count, attaches fresh `Evaluator` and `LLMClient` instances, and proceeds to complete the remaining iterations.
5. **Post-Run Cleanup**:
   Upon successful experiment completion (`experiment.complete()`), `_cleanup_archive_dir()` silently purges the checkpoint state files to prevent disk bloating.
