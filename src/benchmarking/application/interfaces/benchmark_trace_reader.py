"""Abstract interface for reading IOH evaluation traces."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path

from benchmarking.domain.trial_schedule import TrialIdentity
from benchmarking.domain.vos import BenchmarkDataset


class BenchmarkTraceReader(ABC):
    @property
    @abstractmethod
    def benchmark_dir(self) -> Path: ...

    @abstractmethod
    def get_run_count(self, solver_dir: Path) -> int: ...

    @abstractmethod
    def load_provenance_records(self) -> list[dict[str, object]]: ...

    @abstractmethod
    def load_benchmark_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
        solver_resolver: Callable[[str], str] | None = None,
        trial_schedule: tuple[TrialIdentity, ...] = (),
    ) -> BenchmarkDataset: ...
