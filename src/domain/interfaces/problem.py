from abc import ABC, abstractmethod

import numpy as np

from domain.enums import ProblemMode


class BaseProblem(ABC):
    """Abstract base class interface for any callable optimization problem."""

    problem_id: int
    dim: int
    instance_id: int
    noise_std: float
    noise_model: str
    true_optimum: float

    @property
    @abstractmethod
    def mode(self) -> ProblemMode:
        """Return ProblemMode (NOISY or CLEAN)."""
        ...

    @property
    @abstractmethod
    def lb(self) -> np.ndarray:
        """Lower bounds vector."""
        ...

    @property
    @abstractmethod
    def ub(self) -> np.ndarray:
        """Upper bounds vector."""
        ...

    @property
    @abstractmethod
    def lower_bound(self) -> np.ndarray:
        """Lower bounds vector alias."""
        ...

    @property
    @abstractmethod
    def upper_bound(self) -> np.ndarray:
        """Upper bounds vector alias."""
        ...

    @abstractmethod
    def __call__(self, x: np.ndarray) -> float:
        """Evaluate objective function at x."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset problem state for reuse."""
        ...

    @abstractmethod
    def get_objective_fn(self) -> "BaseProblem":
        """Return objective function callable."""
        ...

    @abstractmethod
    def is_in_bounds(self, x: np.ndarray, tol: float = 1e-5) -> bool:
        """Check if candidate point x lies within search space bounds."""
        ...

    @abstractmethod
    def clip(self, x: np.ndarray) -> np.ndarray:
        """Clip candidate search point x to fit within search space bounds."""
        ...
