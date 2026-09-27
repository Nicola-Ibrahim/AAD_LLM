"""Abstract persistence interface for synthesis experiment state."""

from abc import ABC, abstractmethod

from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.vos import IterationMetadata, ProblemProfile
from evolution.domain.vos.experiment_filter import ExperimentFilter


class SynthesisRepository(ABC):
    """Load and persist synthesis experiment metadata and iteration state."""

    @abstractmethod
    def load(
        self,
        criteria: ExperimentFilter | None = None,
        *,
        experiment_id: int | None = None,
        problem_id: int | None = None,
        instance_id: int | None = None,
        llm_name: str | None = None,
        mode: SynthesisMode | None = None,
        prompt_strategy: PromptStrategy | None = None,
        noise_std: float | None = None,
    ) -> list[ExperimentSummary]: ...

    @abstractmethod
    def load_by_ids(self, experiment_ids: list[int]) -> list[ExperimentSummary]: ...

    @abstractmethod
    def get_experiment_status(self, experiment_id: int) -> tuple[str | None, int]: ...

    @abstractmethod
    def create_experiment(
        self,
        problem: ProblemProfile,
        mode: SynthesisMode,
        llm_name: str,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        budget: int = 1_000_000,
        max_iterations: int = 10,
        synthesis_seed: int | None = None,
    ) -> int: ...

    @abstractmethod
    def append_iteration(self, experiment_id: int, metadata: IterationMetadata) -> None: ...

    @abstractmethod
    def save_experiment_summary(self, exp: ExperimentSummary) -> None: ...

    @abstractmethod
    def mark_failed(self, experiment_id: int, reason: str = "") -> None: ...

    @abstractmethod
    def reset_experiment(self, experiment_id: int) -> None:
        """Discard iterations and champion state, retaining the experiment's ID and condition."""

    @abstractmethod
    def checkpoint_wal(self) -> None: ...

    @abstractmethod
    def get_best_raw_fitness(self, experiment_id: int) -> float | None: ...
