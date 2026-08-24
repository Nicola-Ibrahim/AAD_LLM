"""Evolutionary Algorithm Synthesis Bounded Context.

Provides LLM-driven evolutionary optimization, code synthesis,
candidate evaluation, and experiment tracking for continuous optimization problems.
"""

from evolution.domain import (
    AWGNStrategy,
    BaseDomainException,
    BaseNoiseStrategy,
    BaseProblem,
    Code,
    Convergence,
    DomainEntity,
    EntityID,
    Error,
    Execution,
    ExperimentSummary,
    Fitness,
    HomoscedasticAdditiveNoiseStrategy,
    IterationMetadata,
    MultiplicativeNoiseStrategy,
    NoNoiseStrategy,
    NoiseModelEnum,
    NoiseStrategyFactory,
    ProblemMode,
    ProblemProfile,
    ValueObject,
)
from evolution.orchestration import (
    EvolutionTask,
    OrchestrationError,
    TaskOrchestrator,
)
from evolution.synthesis.prompts import PromptStrategy
from evolution.synthesis.session import LLaMEASession, SessionResult

__all__ = [
    # Domain
    "DomainEntity",
    "ValueObject",
    "EntityID",
    "BaseDomainException",
    "ExperimentSummary",
    "IterationMetadata",
    "ProblemProfile",
    "ProblemMode",
    "BaseProblem",
    "NoiseModelEnum",
    "BaseNoiseStrategy",
    "NoNoiseStrategy",
    "MultiplicativeNoiseStrategy",
    "HomoscedasticAdditiveNoiseStrategy",
    "AWGNStrategy",
    "NoiseStrategyFactory",
    "Execution",
    "Fitness",
    "Code",
    "Error",
    "Convergence",
    # Orchestration
    "TaskOrchestrator",
    "EvolutionTask",
    "OrchestrationError",
    # Synthesis
    "LLaMEASession",
    "SessionResult",
    "PromptStrategy",
]
