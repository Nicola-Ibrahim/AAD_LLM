from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from core.config import DATA_DIR
from domain.interfaces import BaseProblem
from infra.llm.client import LLMClient
from infra.storage.code.repository import CodeRepository
from infra.storage.sqlite.factory import initialize_sqlite_storage, setup_storage_environment
from synthesis.prompts import PromptStrategy
from synthesis.session import LLaMEASession, SessionResult


@dataclass
class EvolutionTask:
    """A single unit of evolution work to be executed in the process pool.

    Stores all parameters required to construct and run a LLaMEASession inside a worker process,
    or a custom picklable fn callable for custom tasks.
    """

    key: str
    problem: BaseProblem | None = None
    llm_client: LLMClient | None = None
    budget: int = 1000
    iterations: int | None = None
    resume_experiment_id: int | None = None
    prompt_strategy: PromptStrategy | str = PromptStrategy.BASELINE
    db_path: Path = field(default_factory=lambda: DATA_DIR / "db.sqlite3")
    fn: Callable[[], SessionResult] | None = None

    def __call__(self) -> SessionResult:
        """Executes the evolution task inside the worker process."""
        if self.fn is not None:
            return self.fn()

        db_repo = initialize_sqlite_storage(self.db_path)
        code_repo = CodeRepository()

        if self.resume_experiment_id is not None:
            session = LLaMEASession.resume(
                experiment_id=self.resume_experiment_id,
                llm_client=self.llm_client,
                db_repo=db_repo,
                code_repo=code_repo,
                iterations=self.iterations,
            )
        else:
            session = LLaMEASession.create(
                problem=self.problem,
                llm_client=self.llm_client,
                db_repo=db_repo,
                code_repo=code_repo,
                budget=self.budget,
                iterations=self.iterations or 10,
                prompt_strategy=self.prompt_strategy,
            )
        return session.run()


class OrchestrationError(RuntimeError):
    """Exception raised when one or more evolution tasks fail."""

    def __init__(self, errors: dict[str, Exception]):
        formatted_details = "\n".join(
            f"  - Task '{key}': {type(err).__name__}: {err}" for key, err in errors.items()
        )
        super().__init__(f"Evolution tasks failed:\n{formatted_details}")
        self.errors = errors


def _execute_task(task: EvolutionTask) -> SessionResult:
    """Worker function that runs the task directly."""
    return task()


class TaskOrchestrator:
    """Manages multi-core parallel execution and lifecycle of evolution tasks."""

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
