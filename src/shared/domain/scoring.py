"""Common minimization mathematics, independent of workflow scoring policy."""


def objective_gap(clean_objective: float, true_optimum: float) -> float:
    """Nonnegative minimization gap with the established roundoff clamp."""
    return max(0.0, float(clean_objective) - float(true_optimum))
