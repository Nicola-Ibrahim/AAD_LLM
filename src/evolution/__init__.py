"""Evolutionary Algorithm Synthesis Bounded Context.

Provides LLM-driven evolutionary optimization, code synthesis,
candidate evaluation, and experiment tracking for continuous optimization problems.
"""

from evolution.application import (
    EvolutionExperimentService,
    EvolutionTask,
    SessionResult,
    TaskOrchestrator,
)
from evolution.application.synthesis import LLaMEASession
from evolution.domain import (
    AWGNStrategy,
    AlgorithmTimeoutException,
    BaseDomainException,
    BaseNoiseStrategy,
    BaseProblem,
    Code,
    CodeValidationException,
    Convergence,
    DomainEntity,
    EntityID,
    Error,
    Execution,
    ExperimentSummary,
    Fitness,
    HeteroscedasticNoiseStrategy,
    HomoscedasticAdditiveNoiseStrategy,
    IterationMetadata,
    NoNoiseStrategy,
    NoiseModelEnum,
    NoiseStrategyFactory,
    OrchestrationError,
    ProblemMode,
    ProblemProfile,
    PromptStrategy,
    ValueObject,
)

__all__ = [
    # Domain
    "DomainEntity",
    "ValueObject",
    "EntityID",
    "BaseDomainException",
    "CodeValidationException",
    "AlgorithmTimeoutException",
    "OrchestrationError",
    "ExperimentSummary",
    "IterationMetadata",
    "ProblemProfile",
    "ProblemMode",
    "PromptStrategy",
    "BaseProblem",
    "NoiseModelEnum",
    "BaseNoiseStrategy",
    "NoNoiseStrategy",
    "HeteroscedasticNoiseStrategy",
    "HomoscedasticAdditiveNoiseStrategy",
    "AWGNStrategy",
    "NoiseStrategyFactory",
    "Execution",
    "Fitness",
    "Code",
    "Error",
    "Convergence",
    # Application & Task Execution
    "EvolutionExperimentService",
    "TaskOrchestrator",
    "EvolutionTask",
    "LLaMEASession",
    "SessionResult",
]
