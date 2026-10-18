"""Abstract interface for evaluation trace and provenance state."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ContextManager


class EvaluationStateStore(ABC):
    @property
    @abstractmethod
    def eval_dir(self) -> Path: ...

    @abstractmethod
    def solver_directory_exists(self, solver_dir: Path) -> bool: ...

    @abstractmethod
    def remove_solver_traces(self, solver_dir: Path) -> None: ...

    @abstractmethod
    def read_provenance(self, solver_dir: Path) -> dict[str, object] | None: ...

    @abstractmethod
    def write_provenance(self, solver_dir: Path, data: dict[str, object]) -> None: ...

    @abstractmethod
    def get_trace_run_count(self, solver_dir: Path) -> int:
        """Count nonempty trace runs, including interrupted attempts without terminal records."""
        ...

    @abstractmethod
    def open_run_logger(
        self, target_dir: Path, algorithm_name: str, incremental: bool
    ) -> ContextManager[object]: ...
