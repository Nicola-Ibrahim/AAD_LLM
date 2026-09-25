"""Ports for creating campaign problems and dispatching worker tasks."""

from collections.abc import Callable
from typing import Protocol, TypeVar

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


Task = TypeVar("Task")
Result = TypeVar("Result")


class TaskDispatcher(Protocol[Task, Result]):
    def run(
        self, fn: Callable[[Task], Result], items: list[Task], key_fn: Callable[[Task], str]
    ) -> dict[str, Result]: ...
