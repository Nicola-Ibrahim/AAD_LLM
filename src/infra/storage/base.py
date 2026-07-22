from abc import ABC, abstractmethod
from pathlib import Path

from core.schema.experiment import ExperimentSummary
from core.schema.iteration import IterationMetadata
from infra.storage.run_context import RunContext


class ExperimentRepository(ABC):
    """Abstract base class representing a repository interface for experiment results metadata and checkpoint lifecycle."""

    @abstractmethod
    def save(self, summary: ExperimentSummary) -> None:
        """Persists a pre-built ExperimentSummary."""
        pass

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
    ) -> RunContext:
        """Creates the experiment DB row and all pre-execution directories.

        Returns a RunContext with run_id and guaranteed-to-exist directory paths.
        This is the only setup call needed before firing a session.
        """
        pass

    @abstractmethod
    def append_iteration(
        self,
        problem_id: int,
        dim: int,
        mode: str,
        run_id: int,
        metadata: IterationMetadata,
        experiment_meta: dict,
    ) -> None:
        """Appends an iteration record to the checkpoint cache file."""
        pass

    @abstractmethod
    def commit_and_cleanup(self, problem_id: int, dim: int, mode: str, run_id: int) -> None:
        """Parses local checkpoint cache, commits to DB, and deletes temporary files."""
        pass

    @abstractmethod
    def commit_without_cleanup(self, problem_id: int, dim: int, mode: str, run_id: int) -> None:
        """Parses local checkpoint cache, commits to DB, but preserves temporary files."""
        pass

    @abstractmethod
    def recover_orphaned(self) -> int:
        """Scans for orphaned checkpoints and commits them."""
        pass
