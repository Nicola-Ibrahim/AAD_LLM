"""Application Task Concurrency & Process Pool Orchestration.

Defines self-contained picklable work units (EvolutionTask) and the multi-core
process pool orchestrator (TaskOrchestrator) for parallel evolutionary campaigns.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from shared.config import DATA_DIR
from shared.database import initialize_sqlite_storage, setup_storage_environment
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.exceptions import OrchestrationError
from evolution.domain.interfaces import BaseProblem
from evolution.application.synthesis.config import SessionConfig
from evolution.infra.llm.client import LLMClient
from evolution.infra.storage.code.repository import CodeRepository
from evolution.application.synthesis.session import LLaMEASession, SessionResult


@dataclass
class EvolutionTask:
    """A single picklable unit of evolution work executed inside a worker process.

    Workflow:
                 Task Specification (Problem, LLM, Config, DB Path)
                                │
                                ▼
                 Worker Process Execution: task()
                 ├── Initialize process-isolated SQLite connection (WAL mode)
                 ├── Instantiate local CodeRepository
                 ├── Construct LLaMEASession
                 └── Execute session.run() -> Return SessionResult
    """

    key: str
    problem: BaseProblem
    llm_client: LLMClient
    experiment_id: int
    config: SessionConfig
    initial_iteration: int = 0
    prompt_strategy: PromptStrategy = PromptStrategy.BASELINE
    synthesis_mode: SynthesisMode = SynthesisMode.CLEAN
    db_path: Path = field(default_factory=lambda: DATA_DIR / "db.sqlite3")

    def __call__(self) -> SessionResult:
        """Executes the evolution task inside the worker process."""
        db_repo = initialize_sqlite_storage(self.db_path)
        code_repo = CodeRepository()

        session = LLaMEASession(
            problem=self.problem,
            experiment_id=self.experiment_id,
            initial_iteration=self.initial_iteration,
            prompt_strategy=self.prompt_strategy,
            llm_client=self.llm_client,
            db_repo=db_repo,
            code_repo=code_repo,
            config=self.config,
            synthesis_mode=self.synthesis_mode,
        )
        return session.run()


def _execute_task(task: EvolutionTask) -> SessionResult:
    """Worker function that runs the task directly inside the worker process."""
    return task()


class TaskOrchestrator:
    """Manages multi-core parallel execution and lifecycle of evolution tasks.

    Workflow:
                 List of EvolutionTask Work Units
                                │
                                ▼
                 Pre-Flight Environment Setup
                 • Apply SQLite PRAGMA journal_mode=WAL across database files
                                │
                                ▼
                 ProcessPoolExecutor(max_workers)
                 • Dispatch _execute_task() across worker pool processes
                                │
           ┌────────────────────┴────────────────────┐
        Worker Process 1                          Worker Process N
    • Local SQLite storage                    • Local SQLite storage
    • LLaMEASession execution                 • LLaMEASession execution
    • Return SessionResult                    • Return SessionResult
           │                                         │
           └────────────────────┬────────────────────┘
                                ▼
                 Asynchronous Future Reconciliation
                 • Collect results as workers complete (as_completed)
                 • If any worker raises: Aggregate into OrchestrationError
                 • If all succeed: Return dict[str, SessionResult]
    """

    def __init__(self, max_workers: int | None = None):
        """Initializes the task orchestrator with worker configuration.

        Args:
            max_workers: Maximum process pool worker processes. Defaults to number of tasks.
        """
        self.max_workers = max_workers

    def run(self, tasks: list[EvolutionTask]) -> dict[str, SessionResult]:
        """Executes a list of evolution tasks concurrently in a multi-core process pool.

        Args:
            tasks: List of EvolutionTask units to execute.

        Returns:
            dict[str, SessionResult]: Dictionary mapping task keys to their SessionResult objects.

        Raises:
            OrchestrationError: If one or more tasks fail during execution.
        """
        results: dict[str, SessionResult] = {}
        errors: dict[str, Exception] = {}
        workers = self.max_workers if self.max_workers is not None else len(tasks)

        # Pre-flight: Ensure WAL mode is active once in the parent process before worker processes start
        db_paths = [task.db_path for task in tasks if task.db_path]
        setup_storage_environment(db_paths)

        with ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_key = {executor.submit(_execute_task, task): task.key for task in tasks}

            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    errors[key] = e

        if errors:
            raise OrchestrationError(errors)

        return results
