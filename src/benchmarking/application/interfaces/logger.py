"""Abstract interface for benchmark evaluation logging."""

from abc import ABC, abstractmethod
from collections.abc import Mapping

from evolution.domain.enums import SynthesisMode


class EvaluationLoggerInterface(ABC):
    @property
    @abstractmethod
    def verbose(self) -> bool: ...

    @verbose.setter
    @abstractmethod
    def verbose(self, value: bool) -> None: ...

    @abstractmethod
    def header(self, title: str, subtitle: str | None = None, width: int = 80) -> None: ...

    @abstractmethod
    def condition_start(
        self,
        index: int,
        total: int,
        solver_type: str,
        solver_name: str,
        dim: int,
        noise_std: float,
        problem_id: int,
        problem_name: str,
        mode: SynthesisMode | str | None = None,
        strategy: str | None = None,
    ) -> None: ...

    @abstractmethod
    def trial(
        self,
        trial_idx: int,
        total_trials: int,
        best_clean: float,
        runtime: float,
        evals_used: int,
        best_objective: float | None,
        true_optimum: float | None,
    ) -> None: ...

    @abstractmethod
    def cached(self, runs_count: int, median_error: float | None) -> None: ...

    @abstractmethod
    def resuming(self, existing_runs: int, target_runs: int) -> None: ...

    @abstractmethod
    def condition_complete(self, n_runs: int, median_error: float | None) -> None: ...

    @abstractmethod
    def missing_code(self, code_path: str) -> None: ...

    @abstractmethod
    def summary(self, title: str, stats: Mapping[str, object], width: int = 80) -> None: ...
