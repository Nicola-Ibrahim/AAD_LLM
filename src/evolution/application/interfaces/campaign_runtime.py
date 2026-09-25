"""Ports for creating campaign problems and dispatching worker tasks."""

from collections.abc import Callable
from typing import Any, Protocol

from evolution.domain.enums import NoiseModelEnum
from evolution.domain.interfaces import BaseProblem


class ProblemFactory(Protocol):
    def create(
        self,
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: NoiseModelEnum,
        instance_id: int,
        seed: int,
    ) -> BaseProblem: ...


class TaskDispatcher(Protocol):
    def run(
        self, fn: Callable[[Any], Any], items: list[Any], key_fn: Callable[[Any], str]
    ) -> dict[str, Any]: ...
