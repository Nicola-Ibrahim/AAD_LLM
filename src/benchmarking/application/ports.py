"""Small application ports shared by benchmarking use cases."""

from pathlib import Path
from collections.abc import Callable
from typing import Any, Protocol


class MarkdownReportWriter(Protocol):
    def write(self, path: Path, content: str) -> None: ...


class CandidateCodeReader(Protocol):
    def exists(self, code_path: str | Path) -> bool: ...

    def read(self, code_path: str | Path) -> str: ...


class ProblemFactory(Protocol):
    def create(
        self,
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: Any,
        instance_id: int,
        seed: int,
    ) -> Any: ...


class CandidateExecutorFactory(Protocol):
    def __call__(self, timeout_seconds: float) -> Any: ...


class BaselineResolver(Protocol):
    def __call__(self, baseline_slug: str) -> Callable[..., Any]: ...
