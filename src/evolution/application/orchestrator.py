"""Task orchestrator for parallel evolutionary synthesis campaigns.

Coordinates parallel execution of EvolutionTask units using ProcessPoolRunner.
"""

from evolution.application.synthesis_service import EvolutionTask, SessionResult
from evolution.application.worker import run_evolution_worker
from evolution.infra.concurrency.runner import ProcessPoolRunner

class TaskOrchestrator:
    """Manages multi-core parallel execution of evolution tasks."""

    def __init__(self, max_workers: int | None = None) -> None:
        """Initializes the task orchestrator with worker configuration.

        Args:
            max_workers: Maximum process pool worker processes. Defaults to number of tasks.
        """
        self.max_workers = max_workers
        self.runner = ProcessPoolRunner(max_workers=max_workers)

    def run(self, tasks: list[EvolutionTask]) -> dict[str, SessionResult]:
        """Executes a list of evolution tasks concurrently in a multi-core process pool.

        Args:
            tasks: List of EvolutionTask units to execute.

        Returns:
            TaskResults: Dictionary mapping task keys to their SessionResult objects.

        Raises:
            OrchestrationError: If one or more tasks fail during execution.
        """
        return self.runner.run(
            fn=run_evolution_worker,
            items=tasks,
            key_fn=lambda task: task.key,
        )
