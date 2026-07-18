"""
BBOB problem wrapper with validation and noise injection.
"""

import numpy as np
from ioh import get_problem, ProblemClass


class BBOBProblem:
    """
    Stateless BBOB problem descriptor.

    Loads the clean IOH problem instance once, stores the global optimum
    and problem parameters, and provides clean and noisy evaluation methods.

    Parameters
    ----------
    problem_id : int
        The BBOB function ID. Must be an integer in [1, 24].
    dim : int
        The search space dimensionality.
    instance_id : int, optional
        The BBOB instance ID, by default 1.

    Raises
    ------
    ValueError
        If ``problem_id`` is not in the range [1, 24].

    Examples
    --------
    >>> problem = BBOBProblem(problem_id=1, dim=3)
    >>> import numpy as np
    >>> y_clean = problem(np.zeros(3))                       # clean float
    >>> y_dict = problem(np.zeros(3), noise_level=0.05)      # dict: {0.0: clean, 0.05: noisy}
    >>> problem.true_optimum                                 # float: global minimum
    """

    VALID_IDS: range = range(1, 25)  # Valid BBOB problem IDs: 1 to 24 inclusive

    def __init__(
        self,
        problem_id: int,
        dim: int,
        instance_id: int = 1,
    ):
        if problem_id not in self.VALID_IDS:
            raise ValueError(
                f"Invalid BBOB problem_id={problem_id!r}. Must be an integer in [1, 24]."
            )
        self.problem_id = problem_id
        self.dim = dim
        self.instance_id = instance_id

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

    def add_noise(self, true_value: float, noise_level: float) -> float:
        """
        Inject constant additive Gaussian noise, scaled to the problem's overall landscape.
        
        Parameters
        ----------
        true_value : float
            The clean objective value.
        noise_level : float
            The percentage of noise to apply (e.g., 0.05 for 5%).
            
        Returns
        -------
        float
            The noisy objective value.
        """
        if noise_level <= 0.0:
            return true_value

        # The standard deviation is now fixed for the whole problem, 
        # but relative to the specific problem's massive (or tiny) scale.
        dynamic_std = noise_level * self._landscape_scale

        return true_value + np.random.normal(0.0, dynamic_std)

    def __call__(
        self,
        x: np.ndarray,
        noise_level: float | list[float] | None = None,
    ) -> float | dict[float, float]:
        """
        Evaluate the objective function at point ``x``.

        Parameters
        ----------
        x : np.ndarray
            The candidate search point vector.
        noise_level : float | list[float] | None, optional
            If None, returns the clean objective value as a float.
            If a float or list of floats is passed, returns a dictionary mapping
            noise levels (percentages, including 0.0 for clean) to their evaluated fitness.
            
        Returns
        -------
        float | dict[float, float]
            Evaluated fitness float or dictionary of noise_level -> fitness value.
        """
        f_clean = self._clean_problem(x.tolist())
        if noise_level is None:
            return f_clean

        if isinstance(noise_level, (int, float)):
            levels = [float(noise_level)]
        else:
            levels = [float(lvl) for lvl in noise_level]

        results: dict[float, float] = {0.0: f_clean}
        for lvl in levels:
            results[lvl] = self.add_noise(f_clean, lvl)
        return results

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
    def lower_bound(self) -> float | np.ndarray:
        """Return lower bound (scalar float if uniform across dimensions, otherwise array)."""
        lb_vec = self.lb
        return float(lb_vec[0]) if np.all(lb_vec == lb_vec[0]) else lb_vec

    @property
    def upper_bound(self) -> float | np.ndarray:
        """Return upper bound (scalar float if uniform across dimensions, otherwise array)."""
        ub_vec = self.ub
        return float(ub_vec[0]) if np.all(ub_vec == ub_vec[0]) else ub_vec

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
        from ioh import get_problem, ProblemClass
        self._clean_problem = get_problem(self.problem_id, self.instance_id, self.dim, ProblemClass.BBOB)
