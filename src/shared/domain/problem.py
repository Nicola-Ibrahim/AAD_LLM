from abc import ABC, abstractmethod
from typing import NamedTuple

import numpy as np


class ObservationSample(NamedTuple):
    evaluations: int
    observed_y: float


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
    def lower_bound(self) -> np.ndarray:
        """Lower bounds vector."""
        ...

    @property
    @abstractmethod
    def upper_bound(self) -> np.ndarray:
        """Upper bounds vector."""
        ...

    @abstractmethod
    def __call__(self, x: np.ndarray) -> float:
        """Evaluate objective function at x."""
        ...

    @abstractmethod
    def set_budget(self, budget: int) -> None:
        """Set the objective evaluation budget."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset problem state for reuse."""
        ...

    def get_objective_fn(self) -> "BaseProblem":
        """Return objective function callable."""
        return self

    @abstractmethod
    def is_in_bounds(self, x: np.ndarray, tol: float = 1e-5) -> bool:
        """Check if candidate point x lies within search space bounds."""
        ...

    @abstractmethod
    def clip(self, x: np.ndarray) -> np.ndarray:
        """Clip candidate search point x to fit within search space bounds."""
        ...

    @property
    @abstractmethod
    def evaluations(self) -> int:
        """Return cumulative evaluation count."""
        ...

    @abstractmethod
    def eval_clean(self, x: np.ndarray) -> float:
        """Evaluate candidate point x on un-noised ground truth objective."""
        ...

    def attach_logger(self, logger: object) -> None:
        """Hook to attach an external logger/analyzer to the problem."""
        pass

    def configure_observation_checkpoints(self, budget: int, points: int) -> None:
        """Optionally sample values returned to an optimizer, without extra queries."""

    def observation_samples(self) -> tuple[ObservationSample, ...]:
        """Return sampled observations; IOH traces remain separate clean data."""
        return ()
