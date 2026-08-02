from pydantic import Field

from core.domain.base import ValueObject
from core.domain.metrics import (
    ExecutionProfile,
    FitnessMetrics,
    CodeMetrics,
    ErrorProfile,
    ConvergenceProfile,
)


class IterationMetadata(ValueObject):
    """Structured result of one algorithm evaluation by the Evaluator."""

    iteration: int | None = Field(
        default=None,
        description="The 1-based index representing the generation or iteration of the evolution loop.",
        examples=[1, 5, 10],
    )
    algorithm_name: str = Field(
        description="Name of the generated algorithm candidate.",
        examples=["NoisyHillClimber", "RandomSearchAlgorithm"],
    )

    execution: ExecutionProfile = Field(
        description="Timing and throughput metrics for the iteration's execution run."
    )
    fitness: FitnessMetrics = Field(
        description="Fitness metrics and errors achieved by the candidate algorithm."
    )
    code: CodeMetrics = Field(
        description="Attributes and metadata about the candidate algorithm code."
    )
    error: ErrorProfile = Field(
        description="Traceback and exception info if the candidate algorithm failed."
    )
    convergence: ConvergenceProfile = Field(
        description="Details about convergence of the execution run."
    )
