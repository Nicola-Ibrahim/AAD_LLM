from abc import ABC, abstractmethod
from schema import ExperimentSummary


class ExperimentStore(ABC):
    """Abstract base class representing a storage backend for experiment results metadata."""

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


