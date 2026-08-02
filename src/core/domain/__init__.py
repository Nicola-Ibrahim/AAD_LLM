"""Domain model package containing entities, value objects, and domain abstractions."""

from core.domain.base import DomainEntity, EntityID, ValueObject
from core.domain.experiment import ExperimentSummary
from core.domain.iteration import IterationMetadata
from core.domain.metrics import (
    CodeMetrics,
    ConvergenceProfile,
    ErrorProfile,
    ExecutionProfile,
    FitnessMetrics,
)
from core.domain.problem import ProblemProfile

__all__ = [
    "DomainEntity",
    "ValueObject",
    "EntityID",
    "ExperimentSummary",
    "IterationMetadata",
    "ProblemProfile",
    "ExecutionProfile",
    "FitnessMetrics",
    "CodeMetrics",
    "ErrorProfile",
    "ConvergenceProfile",
]
