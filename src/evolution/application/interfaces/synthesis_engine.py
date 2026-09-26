"""Abstract interface for executing a synthesis session."""

from abc import ABC, abstractmethod

from evolution.application.synthesis.models import SessionConfig, SessionResult
from evolution.application.interfaces.synthesis_repository import SynthesisRepository
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.problem import BaseProblem


class SynthesisEngine(ABC):
    """Run one candidate-generation session for a problem condition."""

    @abstractmethod
    def run(
        self,
        problem: BaseProblem,
        experiment_id: int,
        config: SessionConfig,
        db_repo: SynthesisRepository,
        prompt_strategy: PromptStrategy,
        synthesis_mode: SynthesisMode,
        initial_iteration: int = 0,
    ) -> SessionResult:
        """Execute one synthesis session and return its result."""
