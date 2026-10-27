"""External optimizer-generation engine used by both synthesis workflows."""

from abc import ABC, abstractmethod

from evolution.application.synthesis.result import SynthesisResult
from evolution.application.synthesis.settings import SynthesisSettings
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from shared.domain.problem import BaseProblem


class SynthesisEngine(ABC):
    """Generate and improve candidates for one problem condition."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identity of the model actually connected to this engine."""

    @abstractmethod
    def run(
        self,
        problem: BaseProblem,
        experiment_id: int,
        config: SynthesisSettings,
        db_repo: SynthesisRepository,
        prompt_strategy: PromptStrategy,
        synthesis_mode: SynthesisMode,
        initial_iteration: int = 0,
        restart: bool = False,
    ) -> SynthesisResult:
        """Perform synthesis and return its result."""
