"""
Noisy BBOB problem wrapper injecting additive Gaussian noise.
"""

from typing import Callable, List
import numpy as np
from ioh import get_problem, ProblemClass

class NoisyBBOBWrapper:
    """
    Stateful wrapper for a BBOB problem that tracks evaluation history
    and injects additive Gaussian noise.
    """

    def __init__(self, clean_problem, noise_std: float = 0.05):
        self.clean_problem = clean_problem
        self.noise_std = noise_std
        self.true_optimum = float(clean_problem.optimum.y)
        self.clean_values: List[float] = []
        self.best_clean_values: List[float] = []
        self._current_best = float('inf')

    def __call__(self, x: np.ndarray) -> float:
        # Evaluate clean problem (suppress mypy/pyright warning on restrictive typeshed)
        true_value = float(self.clean_problem(x))  # type: ignore
        
        # Inject additive noise
        noise = np.random.normal(0.0, self.noise_std)
        noisy_value = true_value + noise
        
        # Track history of clean evaluations
        self.clean_values.append(true_value)
        if true_value < self._current_best:
            self._current_best = true_value
        self.best_clean_values.append(self._current_best)
        
        return float(noisy_value)

def get_noisy_bbob(
    problem_id: int, 
    instance_id: int, 
    dim: int, 
    noise_std: float = 0.05
) -> NoisyBBOBWrapper:
    """
    Load a BBOB problem and wrap it with additive Gaussian noise.

    Parameters
    ----------
    problem_id : int
        The BBOB problem ID (1 to 24).
    instance_id : int
        The problem instance ID.
    dim : int
        The search space dimensionality.
    noise_std : float
        The standard deviation of the additive Gaussian noise.

    Returns
    -------
    wrapper : NoisyBBOBWrapper
        Stateful objective function wrapper.
    """
    clean_problem = get_problem(problem_id, instance_id, dim, ProblemClass.BBOB)
    return NoisyBBOBWrapper(clean_problem, noise_std)
