"""
BBOB problem wrapper with validation, noise injection, and history tracking.
"""

from typing import List
import numpy as np
from ioh import get_problem, ProblemClass


class BBOBProblem:
    """
    Self-contained BBOB problem: validates the problem ID, loads the IOH problem,
    injects additive Gaussian noise on every call, and tracks the clean convergence
    history.

    Parameters
    ----------
    problem_id : int
        The BBOB function ID. Must be an integer in [1, 24].
    dim : int
        The search space dimensionality.
    instance_id : int, optional
        The BBOB instance ID, by default 1.
    noise_std : float, optional
        Standard deviation of additive Gaussian noise, by default 0.05.

    Raises
    ------
    ValueError
        If ``problem_id`` is not in the range [1, 24].

    Examples
    --------
    >>> problem = BBOBProblem(problem_id=1, dim=3)
    >>> import numpy as np
    >>> y = problem(np.zeros(3))   # noisy objective call
    >>> problem.true_optimum       # float: global minimum
    >>> problem.best_clean_values  # list: convergence trajectory
    >>> problem.reset()            # clear history for a fresh run
    """

    VALID_IDS: range = range(1, 25)  # Valid BBOB problem IDs: 1 to 24 inclusive

    def __init__(
        self,
        problem_id: int,
        dim: int,
        instance_id: int = 1,
        noise_std: float = 0.05,
    ):
        if problem_id not in self.VALID_IDS:
            raise ValueError(
                f"Invalid BBOB problem_id={problem_id!r}. "
                f"Must be an integer in [1, 24]."
            )
        self.problem_id = problem_id
        self.dim = dim
        self.instance_id = instance_id
        self.noise_std = noise_std

        # Load the underlying clean IOH problem once
        self._clean_problem = get_problem(problem_id, instance_id, dim, ProblemClass.BBOB)
        self.true_optimum: float = float(self._clean_problem.optimum.y)

        # Convergence history (reset between evaluations)
        self.clean_values: List[float] = []
        self.best_clean_values: List[float] = []
        self._current_best: float = float("inf")

    def __call__(self, x: np.ndarray) -> float:
        """Evaluate the noisy objective at point ``x``."""
        true_value = float(self._clean_problem(x))  # type: ignore

        # Inject additive Gaussian noise
        noise = np.random.normal(0.0, self.noise_std)
        noisy_value = true_value + noise

        # Track clean evaluation history
        self.clean_values.append(true_value)
        if true_value < self._current_best:
            self._current_best = true_value
        self.best_clean_values.append(self._current_best)

        return noisy_value

    def reset(self) -> None:
        """Clear convergence history for a fresh algorithm run."""
        self._clean_problem.reset()
        self.clean_values = []
        self.best_clean_values = []
        self._current_best = float("inf")

    def __repr__(self) -> str:
        return (
            f"BBOBProblem(problem_id={self.problem_id}, dim={self.dim}, "
            f"instance_id={self.instance_id}, noise_std={self.noise_std})"
        )
