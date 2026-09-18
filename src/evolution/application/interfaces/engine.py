"""Synthesis Engine Port Interface."""

from abc import ABC, abstractmethod

from evolution.application.synthesis_service import SessionConfig, SessionResult
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.interfaces.problem import BaseProblem
from evolution.infra.llm.client import LLMClient
from evolution.infra.storage.base import SynthesisRepository
from evolution.infra.storage.code.repository import CodeRepository


class SynthesisEngine(ABC):
    """Port interface for algorithm synthesis engines (LLaMEA, EoH, Reflection, etc.).

    Any concrete synthesis engine adapter in infra must inherit from this base class.
    """

    @abstractmethod
    def run(
        self,
        problem: BaseProblem,
        experiment_id: int,
        prompt_strategy: PromptStrategy,
        llm_client: LLMClient,
        db_repo: SynthesisRepository,
        code_repo: CodeRepository,
        config: SessionConfig,
        initial_iteration: int = 0,
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
    ) -> SessionResult:
        """Executes a complete algorithm synthesis session on the given optimization problem."""
        ...
