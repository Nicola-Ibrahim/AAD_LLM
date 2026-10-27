"""Validated settings for generating one optimizer."""

from pydantic import BaseModel, ConfigDict, Field


class SynthesisSettings(BaseModel):
    """Runtime budgets and stopping criteria for one synthesis experiment."""

    budget: int = Field(ge=1)
    timeout_seconds: float = Field(default=30.0, gt=0.0)
    iterations: int = Field(default=10, ge=1)
    stagnation_threshold: int = Field(default=3, ge=1)
    convergence_threshold: float = Field(default=1e-6, ge=0.0)

    model_config = ConfigDict(frozen=True)
