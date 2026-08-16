import numpy as np
from ioh import ProblemClass, get_problem

from domain.enums import ProblemMode
from domain.interfaces import BaseProblem
from domain.services.noise_strategy import BaseNoiseStrategy


class BBOBProblem(BaseProblem):
    """BBOB problem wrapper with strategy pattern for noise injection.

    Loads the clean IOH problem instance once, stores the global optimum
    and problem parameters, and provides clean and noisy evaluation methods.

    Args:
        problem_id: The BBOB function ID (1 to 24).
        dim: The search space dimensionality.
        noise_strategy: Noise strategy instance (e.g. NoNoiseStrategy()).
        instance_id: The BBOB instance ID, by default 1.
        seed: Random seed for landscape scale estimation.
    """

    def __init__(
        self,
        problem_id: int,
        dim: int,
        noise_strategy: BaseNoiseStrategy,
        instance_id: int = 1,
        seed: int = 42,
    ):
        self.problem_id = problem_id
        self.dim = dim
        self.instance_id = instance_id

        # Load the underlying clean IOH problem once
        self._clean_problem = get_problem(problem_id, instance_id, dim, ProblemClass.BBOB)
        self.true_optimum: float = self._clean_problem.optimum.y
        # Eagerly cache bounds to avoid deadlocks from dynamic imports in concurrent thread pools
        self._lb = np.array(self._clean_problem.bounds.lb, dtype=float)
        self._ub = np.array(self._clean_problem.bounds.ub, dtype=float)

        # Explicit Noise Strategy injection
        self.noise_strategy: BaseNoiseStrategy = noise_strategy
        self.noise_strategy.setup(
            self._clean_problem, self._lb, self._ub, self.true_optimum, seed=seed
        )
        self.noise_std: float = self.noise_strategy.noise_std
        self.noise_model: str = self.noise_strategy.name

    def _add_noise(self, true_value: float) -> float:
        """Inject noise into the objective value by delegating to configured noise_strategy."""
        return self.noise_strategy.add_noise(true_value)

    def __call__(self, x: np.ndarray) -> float:
        """Evaluate the objective function at point `x`.

        Args:
            x: The candidate search point vector.

        Returns:
            float: Evaluated objective value (noisy if self.noise_std > 0 else clean).
        """
        arr = np.asarray(x, dtype=float)
        f_clean = self._clean_problem(arr.tolist())
        if self.noise_std <= 0.0:
            return f_clean

        return self._add_noise(f_clean)

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
    def lb(self) -> np.ndarray:
        """Return cached lower bounds numpy array."""
        return self._lb

    @property
    def ub(self) -> np.ndarray:
        """Return cached upper bounds numpy array."""
        return self._ub

    @property
    def lower_bound(self) -> np.ndarray:
        """Alias for `lb`."""
        return self._lb

    @property
    def upper_bound(self) -> np.ndarray:
        """Alias for `ub`."""
        return self._ub

    @property
    def optimum_x(self) -> np.ndarray:
        """Return the coordinates of the global optimum in the search space."""
        return np.array(self._clean_problem.optimum.x, dtype=float)

    @property
    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        """Return search space bounds as a (lower_bounds, upper_bounds) tuple."""
        return self._lb, self._ub

    def is_in_bounds(self, x: np.ndarray, tol: float = 1e-5) -> bool:
        """Check if candidate point x lies within search space bounds."""
        arr = np.asarray(x, dtype=float)
        return bool(np.all(arr >= (self._lb - tol)) and np.all(arr <= (self._ub + tol)))

    def clip(self, x: np.ndarray) -> np.ndarray:
        """Clip candidate search point x to fit within search space bounds."""
        arr = np.asarray(x, dtype=float)
        return np.clip(arr, self._lb, self._ub)

    @property
    def evaluations(self) -> int:
        """Return cumulative function evaluation count."""
        return self._clean_problem.state.evaluations

    def eval_clean(self, x: np.ndarray) -> float:
        """Evaluate candidate point x on un-noised ground truth objective."""
        arr = np.asarray(x, dtype=float)
        return self._clean_problem(arr.tolist())

    @property
    def clean_problem(self) -> object:
        """Expose underlying clean IOH problem instance."""
        return self._clean_problem

    def attach_logger(self, logger: object) -> None:
        """Attach an external logger/analyzer to the underlying clean IOH problem."""
        if logger is not None and getattr(self, "_clean_problem", None) is not None:
            self._clean_problem.attach_logger(logger)

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
        # Exclude C++ unpicklable wrappers
        state["_clean_problem"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Re-initialize clean IOH problem instance on unpickling
        self._clean_problem = get_problem(
            self.problem_id, self.instance_id, self.dim, ProblemClass.BBOB
        )
