"""Port for executing generated optimizer code."""

from collections.abc import Callable
from typing import Protocol

import numpy as np


class CandidateTimeout(TimeoutError):
    """Application-level signal that generated code exceeded its time limit."""


class CandidateExecutor(Protocol):
    """Execution capability required by the candidate evaluation use case."""

    last_captured_warnings: list[str]

    def execute_algorithm(
        self, code: str, name: str, dim: int, problem: Callable[..., float], budget: int
    ) -> tuple[np.ndarray | None, float]: ...
