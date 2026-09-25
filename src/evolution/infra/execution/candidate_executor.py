"""Infrastructure adapter around the shared sandboxed Python algorithm executor."""

from collections.abc import Callable

import numpy as np

from evolution.application.ports.candidate_executor import CandidateExecutor, CandidateTimeout
from shared.infra.execution import AlgorithmExecutor, AlgorithmTimeoutException


class AlgorithmExecutorAdapter(CandidateExecutor):
    """Translate shared executor behavior into the candidate-execution application port."""

    def __init__(self, executor: AlgorithmExecutor) -> None:
        self._executor = executor

    @property
    def last_captured_warnings(self) -> list[str]:
        return self._executor.last_captured_warnings

    def execute_algorithm(
        self, code: str, name: str, dim: int, problem: Callable[..., float], budget: int
    ) -> tuple[np.ndarray | None, float]:
        try:
            return self._executor.execute_algorithm(code, name, dim, problem, budget)
        except AlgorithmTimeoutException as exc:
            raise CandidateTimeout(str(exc)) from exc


def create_candidate_executor(timeout_seconds: float) -> AlgorithmExecutorAdapter:
    return AlgorithmExecutorAdapter(AlgorithmExecutor(timeout_seconds=timeout_seconds))
