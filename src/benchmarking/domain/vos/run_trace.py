"""RunTrace and SolverRunCollection Value Objects representing empirical optimization convergence traces."""

from typing import Self
import numpy as np
from pydantic import Field, model_validator

from benchmarking.domain.base import ValueObject


class RunTrace(ValueObject):
    """Strongly-typed Value Object representing a single experimental execution run on a BBOB problem."""

    evaluations: np.ndarray = Field(description="Array of cumulative function evaluations.")
    raw_objectives: np.ndarray = Field(description="Array of objective error values at each evaluation checkpoint.")

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        """Guarantee evaluations and raw_objectives have identical length."""
        len_evals = len(self.evaluations)
        len_raw = len(self.raw_objectives)
        if len_evals != len_raw:
            min_len = min(len_evals, len_raw)
            self.evaluations = self.evaluations[:min_len]
            self.raw_objectives = self.raw_objectives[:min_len]
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


class SolverRunCollection(ValueObject):
    """Value Object representing the collection of experimental runs for a specific solver under a single condition."""

    solver_name: str = Field(description="Canonical display name of the solver or LLaMEA configuration.")
    runs: list[RunTrace] = Field(default_factory=list, description="List of individual RunTrace value objects.")

    @property
    def terminal_values(self) -> list[float]:
        """List of final terminal error values across all runs."""
        return [r.final_value for r in self.runs if not np.isnan(r.final_value)]

    @property
    def best_values(self) -> list[float]:
        """List of best objective values across all runs."""
        return [r.best_value for r in self.runs if not np.isnan(r.best_value)]

    def success_rate(self, threshold: float = 1e-8) -> float:
        """Fraction of runs that reached delta_y <= threshold."""
        if not self.runs:
            return 0.0
        successes = sum(1 for r in self.runs if r.is_success(threshold))
        return successes / len(self.runs)

    def __len__(self) -> int:
        return len(self.runs)

    def __iter__(self):
        return iter(self.runs)

    def __getitem__(self, idx: int) -> RunTrace:
        return self.runs[idx]

    def __repr__(self) -> str:
        return f"SolverRunCollection(solver='{self.solver_name}', n_runs={len(self.runs)})"
