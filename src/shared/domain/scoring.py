"""Common minimization mathematics, independent of workflow scoring policy."""

import math


def objective_gap(clean_objective: float, true_optimum: float) -> float:
    """Nonnegative minimization gap with the established roundoff clamp."""
    if not math.isfinite(clean_objective) or not math.isfinite(true_optimum):
        raise ValueError("Clean objective and true optimum must be finite")
    return max(0.0, float(clean_objective) - float(true_optimum))
