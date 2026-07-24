from abc import ABC, abstractmethod

from core.schema.experiment import ExperimentSummary
from core.schema.iteration import IterationMetadata


class ExperimentRepository(ABC):
    """Abstract base class representing a repository interface for experiment results metadata and session state lifecycle."""

    @abstractmethod
    def load(
        self,
        problem_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters stored ExperimentSummary objects."""
        pass

    @abstractmethod
    def create_experiment(
        self,
        problem_id: int,
        dim: int,
        mode: str,
        llm_name: str,
        noise_std: float,
        true_optimum: float,
    ) -> int:
        """Creates the experiment DB row and returns its id."""
        pass

    @abstractmethod
    def append_iteration(
        self,
        experiment_id: int,
        metadata: IterationMetadata,
        experiment_meta: dict,
    ) -> None:
        """Appends an iteration record to the repository."""
        pass

    @abstractmethod
    def mark_completed(self, experiment_id: int) -> None:
        """Marks experiment completed and computes best_* rollup fields from iterations."""
        pass

    @abstractmethod
    def mark_failed(self, experiment_id: int, reason: str = "") -> None:
        """Marks an experiment as failed so it is not left in 'running' state."""
        pass

    @abstractmethod
    def checkpoint_wal(self) -> None:
        """Forces a checkpoint to flush WAL logs to the main database file (if applicable)."""
        pass
