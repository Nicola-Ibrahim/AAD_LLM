"""
BBOB problem wrapper with validation and noise injection.
"""

from enum import StrEnum

import numpy as np
from ioh import ProblemClass, get_problem


class ProblemMode(StrEnum):
    CLEAN = "clean"
    NOISY = "noisy"


class BBOBProblem:
    """BBOB problem wrapper with a configurable noise level.

    Loads the clean IOH problem instance once, stores the global optimum
    and problem parameters, and provides clean and noisy evaluation methods.

    Args:
        problem_id: The BBOB function ID. Must be an integer in [1, 24].
        dim: The search space dimensionality.
        instance_id: The BBOB instance ID, by default 1.
        noise_std: Standard deviation factor for additive Gaussian noise
            scaled to the problem landscape. 0.0 means clean (no noise), by default 0.0.

    Raises:
        ValueError: If `problem_id` is not in the range [1, 24].

    Examples:
        >>> clean_problem = BBOBProblem(problem_id=1, dim=3, noise_std=0.0)
        >>> noisy_problem = BBOBProblem(problem_id=1, dim=3, noise_std=0.05)
        >>> import numpy as np
        >>> y_clean = clean_problem(np.zeros(3))   # clean float
        >>> y_noisy = noisy_problem(np.zeros(3))   # noisy float
        >>> clean_problem.true_optimum              # float: global minimum
    """

    VALID_IDS: range = range(1, 25)  # Valid BBOB problem IDs: 1 to 24 inclusive

    def __init__(
        self,
        problem_id: int,
        dim: int,
        instance_id: int = 1,
        noise_std: float = 0.0,
    ):
        if problem_id not in self.VALID_IDS:
            raise ValueError(
                f"Invalid BBOB problem_id={problem_id!r}. Must be an integer in [1, 24]."
            )
        self.problem_id = problem_id
        self.dim = dim
        self.instance_id = instance_id
        self.noise_std = float(noise_std)

        # Load the underlying clean IOH problem once
        self._clean_problem = get_problem(problem_id, instance_id, dim, ProblemClass.BBOB)
        self.true_optimum: float = float(self._clean_problem.optimum.y)
        # Eagerly cache bounds to avoid deadlocks from dynamic imports in concurrent thread pools
        self._lb = np.array(self._clean_problem.bounds.lb, dtype=float)
        self._ub = np.array(self._clean_problem.bounds.ub, dtype=float)

        # Estimate the "Landscape Scale" by sampling random points
        # This gives us a problem-specific magnitude to base our noise on.
        np.random.seed(42)  # Fixed seed so the scale is consistent every run
        sample_points = np.random.uniform(self._lb, self._ub, (20, self.dim))
        sample_y = [self._clean_problem(x.tolist()) for x in sample_points]

        # The scale is the average distance from the optimum across the whole space
        self._landscape_scale = float(np.mean([abs(y - self.true_optimum) for y in sample_y]))

        # Reset internal evaluation counter after initialization samples
        self._clean_problem.reset()

    def _add_noise(self, true_value: float, noise_std: float) -> float:
        """Inject constant additive Gaussian noise, scaled to the problem's overall landscape.

        Args:
            true_value: The clean objective value.
            noise_std: The standard deviation factor to apply (e.g., 0.05).

        Returns:
            float: The noisy objective value.
        """
        if noise_std <= 0.0:
            return true_value

        # The standard deviation is now fixed for the whole problem,
        # but relative to the specific problem's massive (or tiny) scale.
        dynamic_std = noise_std * self._landscape_scale

        return true_value + np.random.normal(0.0, dynamic_std)

    def __call__(self, x: np.ndarray) -> float:
        """Evaluate the objective function at point `x`.

        Args:
            x: The candidate search point vector.

        Returns:
            float: Evaluated objective value (noisy if self.noise_std > 0 else clean).
        """
        f_clean = self._clean_problem(x.tolist())
        if self.noise_std <= 0.0:
            return f_clean

        return self._add_noise(f_clean, self.noise_std)

    @property
    def mode(self) -> ProblemMode:
        """Return ProblemMode.NOISY if noise_std > 0 else ProblemMode.CLEAN."""
        return ProblemMode.NOISY if self.noise_std > 0.0 else ProblemMode.CLEAN

    def eval_scalar(self, x: np.ndarray) -> float:
        """Evaluate the objective function at point `x` and return a single scalar float."""
        return self(x)

    def get_objective_fn(self) -> "BBOBProblem":
        """Return self as the single-scalar objective callable for optimization algorithms."""
        return self

    def __repr__(self) -> str:
        return (
            f"BBOBProblem(problem_id={self.problem_id}, dim={self.dim}, "
            f"instance_id={self.instance_id})"
        )

    def reset(self):
        """Reset the IOH problem state (call counter) for reuse across runs."""
        self._clean_problem.reset()

    @property
    def bounds(self):
        """Return the problem bounds object from IOH."""
        return self._clean_problem.bounds

    @property
    def lb(self) -> np.ndarray:
        """Return the lower bounds vector for the search space."""
        return self._lb

    @property
    def ub(self) -> np.ndarray:
        """Return the upper bounds vector for the search space."""
        return self._ub

    @property
    def optimum_x(self) -> np.ndarray:
        """Return the coordinates of the global optimum in the search space."""
        return np.array(self._clean_problem.optimum.x, dtype=float)

    @property
    def lower_bound(self) -> np.ndarray:
        """Return lower bounds vector for the search space."""
        return self._lb

    @property
    def upper_bound(self) -> np.ndarray:
        """Return upper bounds vector for the search space."""
        return self._ub

    @property
    def name(self) -> str:
        """Return the BBOB function name (e.g. 'BentCigar', 'Sphere')."""
        return self._clean_problem.meta_data.name

    @property
    def meta_str(self) -> str:
        """Return formatted metadata string e.g. 'bbob f₁₂, 2-D, inst. 4'."""
        subscripts = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        f_sub = str(self.problem_id).translate(subscripts)
        return f"bbob f{f_sub}, {self.dim}-D, inst. {self.instance_id}"

    @property
    def full_meta_str(self) -> str:
        """Return full formatted metadata string with function name e.g. 'BentCigar (bbob f₁₂, 2-D, inst. 4)'."""
        subscripts = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        f_sub = str(self.problem_id).translate(subscripts)
        return f"{self.name} (bbob f{f_sub}, {self.dim}-D, inst. {self.instance_id})"

    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude C++ unpicklable wrapper
        state["_clean_problem"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Re-initialize clean IOH problem instance on unpickling
        self._clean_problem = get_problem(
            self.problem_id, self.instance_id, self.dim, ProblemClass.BBOB
        )
