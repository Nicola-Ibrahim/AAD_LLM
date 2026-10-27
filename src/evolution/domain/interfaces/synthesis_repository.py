"""Domain repository contract for synthesis experiments and their iteration state."""

from abc import ABC, abstractmethod

from evolution.domain.entities import Experiment
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.vos import IterationMetadata, ProblemProfile


class SynthesisRepository(ABC):
    """Load and persist experiment domain objects without exposing storage technology."""

    @abstractmethod
    def load(
        self,
        *,
        experiment_id: int | None = None,
        problem_id: int | None = None,
        instance_id: int | None = None,
        llm_name: str | None = None,
        mode: SynthesisMode | None = None,
        prompt_strategy: PromptStrategy | None = None,
        noise_std: float | None = None,
        dim: int | None = None,
        status: str | None = None,
    ) -> list[Experiment]: ...

    @abstractmethod
    def load_by_ids(self, experiment_ids: list[int]) -> list[Experiment]: ...

    @abstractmethod
    def get_experiment_status(self, experiment_id: int) -> tuple[str | None, int]: ...

    @abstractmethod
    def create_experiment(
        self,
        problem: ProblemProfile,
        mode: SynthesisMode,
        llm_name: str,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        *,
        budget: int,
        max_iterations: int,
        synthesis_seed: int | None = None,
    ) -> int: ...

    @abstractmethod
    def append_iteration(self, experiment_id: int, metadata: IterationMetadata) -> None: ...

    @abstractmethod
    def save_experiment(self, exp: Experiment) -> None: ...

    @abstractmethod
    def mark_failed(self, experiment_id: int, reason: str = "") -> None: ...

    @abstractmethod
    def reset_experiment(self, experiment_id: int) -> None:
        """Discard iterations and champion state, retaining the experiment's ID and condition."""
