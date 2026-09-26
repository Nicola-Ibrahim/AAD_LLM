"""Application contract for isolated execution of generated optimizers."""

from abc import ABC, abstractmethod
from collections.abc import Callable

import numpy as np


class CandidateTimeout(TimeoutError):
    """Generated code exceeded the configured execution time limit."""


class CandidateExecutor(ABC):
    """Execute generated optimizer code behind a timeout/sandbox boundary."""

    @property
    @abstractmethod
    def last_captured_warnings(self) -> list[str]:
        """Warnings produced by the most recent candidate execution."""

    @abstractmethod
    def execute_algorithm(
        self, code: str, name: str, dim: int, problem: Callable[..., float], budget: int
    ) -> tuple[np.ndarray, float]:
        """Execute candidate code and return its best point and observed objective."""
