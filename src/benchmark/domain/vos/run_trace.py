"""Validated search history from one optimizer execution."""

from typing import Self

import numpy as np
from pydantic import Field, field_validator, model_validator

from benchmark.domain.base import ValueObject


class RunTrace(ValueObject):
    """Strongly-typed Value Object representing a single experimental execution run on a BBOB problem."""

    evaluations: np.ndarray = Field(description="Array of cumulative function evaluations.")
    raw_objectives: np.ndarray = Field(
        description="Array of objective error values at each evaluation checkpoint."
    )

    @field_validator("evaluations", "raw_objectives")
    @classmethod
    def protect_array(cls, value: np.ndarray) -> np.ndarray:
        if value.ndim != 1:
            raise ValueError("Trace arrays must be one-dimensional")
        values = np.array(value, copy=True)
        values.setflags(write=False)
        return values

    @model_validator(mode="after")
    def validate_trace(self) -> Self:
        if len(self.evaluations) != len(self.raw_objectives):
            raise ValueError("Trace evaluations and objective gaps must have identical lengths")
        if not np.isfinite(self.evaluations).all() or np.any(self.evaluations < 0):
            raise ValueError("Evaluation counts must be finite and nonnegative")
        if np.any(np.diff(self.evaluations) < 0):
            raise ValueError("Evaluation counts must be nondecreasing")
        return self

    @property
    def final_value(self) -> float:
        """Terminal objective error achieved at the end of the run."""
        if len(self.raw_objectives) == 0:
            return float("nan")
        return float(self.raw_objectives[-1])

    @property
    def best_value(self) -> float:
        """Best (minimum) objective error achieved during the run."""
        if len(self.raw_objectives) == 0:
            return float("nan")
        return float(np.min(self.raw_objectives))

    @property
    def eval_count(self) -> int:
        """Total number of function evaluation checkpoints logged."""
        return len(self.evaluations)

    def is_success(self, threshold: float = 1e-8) -> bool:
        """Determine if this run successfully hit target precision delta_y <= threshold."""
        return self.best_value <= threshold

    def __repr__(self) -> str:
        return f"RunTrace(n_evals={self.eval_count}, final={self.final_value:.2e})"
