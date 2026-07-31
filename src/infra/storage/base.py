from abc import ABC, abstractmethod

from core.schema.experiment import ExperimentSummary
from core.schema.iteration import IterationMetadata


class ExperimentRepository(ABC):
    """Abstract base class representing a repository interface for experiment results metadata and session state lifecycle."""

    @abstractmethod
    def load(
        self,
        problem_id: int | None = None,
        instance_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters stored ExperimentSummary objects."""
        pass

    @abstractmethod
    def get_incomplete_experiments(
        self,
        problem_id: int,
        dim: int,
        mode: str,
        llm_name: str,
        noise_std: float,
        instance_id: int = 1,
    ) -> list[int]:
        """Returns a list of experiment IDs with status 'running' that match the given parameters."""
        pass

    @abstractmethod
    def get_experiment_status(self, experiment_id: int) -> tuple[str | None, int]:
        """Returns a tuple of (status_string, max_iteration_number) for an experiment, or (None, 0) if not found."""
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
        instance_id: int = 1,
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

    @abstractmethod
    def get_best_raw_fitness(self, experiment_id: int) -> float | None:
        """Returns the raw algorithm-returned objective value from the best (lowest-error) iteration of an experiment."""
        pass
