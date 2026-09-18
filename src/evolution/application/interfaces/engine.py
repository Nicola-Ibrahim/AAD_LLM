"""Synthesis Engine Port Interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.interfaces import BaseProblem


class SessionConfig(BaseModel):
    """Runtime configuration for an evolutionary synthesis session.

    Serves as the strongly-typed parameter object for runtime budgets, timeouts,
    iterations, stagnation thresholds, and convergence criteria.
    """

    budget: int = Field(
        default=1_000_000,
        ge=1,
        description="Maximum objective function evaluations allowed per algorithm candidate run.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Maximum wall-clock execution time allowed per candidate algorithm in seconds.",
    )
    iterations: int = Field(
        default=10,
        ge=1,
        description="Total number of evolutionary iterations / generations to execute.",
    )
    stagnation_threshold: int = Field(
        default=3,
        ge=1,
        description="Consecutive unimproved iterations before triggering mutation escalation or reset.",
    )
    convergence_threshold: float = Field(
        default=1e-6,
        ge=0.0,
        description="Final error threshold below which optimization is considered successfully converged.",
    )

    model_config = ConfigDict(frozen=True)


@dataclass(slots=True)
class SessionResult:
    """Contract returned per-problem run by an evolutionary synthesis engine."""

    problem_id: int
    dim: int
    mode: SynthesisMode
    noise_std: float
    experiment_id: int
    best_error: float | None = None
    run_history: list[Any] = field(default_factory=list)
    experiment_name: str = ""
    llm_name: str = ""
    error_msg: str = ""
    best_solution: Any = None
    problem_profile: Any = None


class SynthesisEngine(ABC):
    """Port interface for algorithm synthesis engines (LLaMEA, EoH, Reflection, etc.).

    Following the Strategy Pattern, each engine encapsulates algorithmic synthesis logic.
    Common execution collaborators (config, repository, prompting strategies) can be
    configured as engine defaults in `__init__`, allowing `run()` to focus on run-specific
    targets (`problem`, `experiment_id`) while still permitting parameter overrides.
    """

    def __init__(
        self,
        config: SessionConfig | None = None,
        db_repo: Any | None = None,
        prompt_strategy: PromptStrategy = PromptStrategy.BASELINE,
        synthesis_mode: SynthesisMode = SynthesisMode.EXPLICIT,
    ) -> None:
        self.config = config
        self.db_repo = db_repo
        self.prompt_strategy = prompt_strategy
        self.synthesis_mode = synthesis_mode

    @abstractmethod
    def run(
        self,
        problem: BaseProblem,
        experiment_id: int,
        config: SessionConfig | None = None,
        db_repo: Any | None = None,
        prompt_strategy: PromptStrategy | None = None,
        synthesis_mode: SynthesisMode | None = None,
        initial_iteration: int = 0,
    ) -> SessionResult:
        """Executes a single algorithm synthesis run."""
        ...
