"""Application configuration objects.

Defines runtime configuration contracts for synthesis sessions and evaluators.
"""

from pydantic import BaseModel, ConfigDict, Field


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
