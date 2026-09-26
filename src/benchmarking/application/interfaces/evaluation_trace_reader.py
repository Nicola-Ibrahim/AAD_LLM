"""Abstract interface for reading IOH evaluation traces."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from benchmarking.domain.vos import EvaluationDataset


class EvaluationTraceReader(ABC):
    @property
    @abstractmethod
    def eval_dir(self) -> Path: ...

    @abstractmethod
    def get_run_count(self, solver_dir: Path) -> int: ...

    @abstractmethod
    def load_evaluation_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
        solver_resolver: Callable[[str], str] | None = None,
    ) -> EvaluationDataset: ...
