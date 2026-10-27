"""Validation of a generated optimizer's reported solution."""

import numpy as np

from shared.domain.problem import BaseProblem


def validate_returned_point(problem: BaseProblem, point: np.ndarray) -> None:
    """Require a finite, correctly dimensioned point inside the search domain."""
    if point.ndim != 1 or point.shape[0] != problem.dim:
        raise ValueError(
            f"Returned best_x must have shape ({problem.dim},); expected problem dimension {problem.dim}"
        )
    if not np.isfinite(point).all():
        raise ValueError("[INVALID RETURN] Returned best_x contains non-finite coordinates")
    if not problem.is_in_bounds(point):
        raise ValueError("Returned best_x is outside search space bounds")
