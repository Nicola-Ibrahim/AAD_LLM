from pathlib import Path

import ioh
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
        problem_id: The BBOB function ID. Must be an integer in [1, 24].
        dim: The search space dimensionality.
        instance_id: The BBOB instance ID, by default 1.
        noise_strategy: Noise strategy instance. Defaults to NoNoiseStrategy().
        seed: Random seed for landscape scale estimation.

    Raises:
        ValueError: If `problem_id` is not in the range [1, 24].
    """

    VALID_IDS: range = range(1, 25)  # Valid BBOB problem IDs: 1 to 24 inclusive

    def __init__(
        self,
        problem_id: int,
        dim: int,
        noise_strategy: BaseNoiseStrategy,
        ioh_logger: ioh.logger.Analyzer | None = None,
        instance_id: int = 1,
        seed: int = 42,
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

        # Attach IOH logger
        self._ioh_logger = ioh_logger
        if ioh_logger is not None:
            self._clean_problem.attach_logger(ioh_logger)

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

    def is_in_bounds(self, x: np.ndarray, tol: float = 1e-5) -> bool:
        """Check if candidate point x lies within search space bounds [lb - tol, ub + tol]."""
        arr = np.asarray(x, dtype=float)
        return bool(np.all(arr >= self._lb - tol) and np.all(arr <= self._ub + tol))

    def clip(self, x: np.ndarray) -> np.ndarray:
        """Clip candidate search point x to fit within search space bounds [lb, ub]."""
        return np.clip(np.asarray(x, dtype=float), self._lb, self._ub)

    @property
    def evaluations(self) -> int:
        """Return cumulative function evaluation count."""
        return self._clean_problem.state.evaluations

    def eval_clean(self, x: np.ndarray) -> float:
        """Evaluate candidate point x on un-noised ground truth objective."""
        arr = np.asarray(x, dtype=float)
        return float(self._clean_problem(arr.tolist()))

    def attach_logger(self, logger: object) -> None:
        """Attach an experiment logger to the clean underlying problem."""
        self._ioh_logger = logger
        if logger is not None and getattr(self, "_clean_problem", None) is not None:
            self._clean_problem.attach_logger(logger)

    def attach_analyzer(
        self,
        log_dir: str | Path,
        folder_name: str,
        algorithm_name: str,
        algorithm_info: str = "",
        store_positions: bool = False,
    ) -> object | None:
        """Initialize and attach an IOH Analyzer logger directly to the problem."""
        try:
            self._triggers = [ioh.logger.trigger.OnImprovement()]
            logger = ioh.logger.Analyzer(
                triggers=self._triggers,
                root=str(log_dir),
                folder_name=folder_name,
                algorithm_name=algorithm_name,
                algorithm_info=algorithm_info or "algorithm_info",
                store_positions=store_positions,
            )
            self.attach_logger(logger)
            return logger
        except Exception as e:
            print(f"[!] Could not attach IOH Logger: {e}")
            return None

    def close_logger(self) -> None:
        """Safely close any attached experiment logger."""
        if getattr(self, "_ioh_logger", None) is not None:
            try:
                self._ioh_logger.close()
            except Exception:
                pass
            self._ioh_logger = None
            self._triggers = None

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
        state["_ioh_logger"] = None
        state["_triggers"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Re-initialize clean IOH problem instance on unpickling
        self._clean_problem = get_problem(
            self.problem_id, self.instance_id, self.dim, ProblemClass.BBOB
        )
        if getattr(self, "_ioh_logger", None) is not None:
            self._clean_problem.attach_logger(self._ioh_logger)
