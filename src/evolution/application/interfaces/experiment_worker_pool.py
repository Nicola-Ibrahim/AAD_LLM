"""Application boundary for executing prepared experiments in worker processes."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

Task = TypeVar("Task")
Result = TypeVar("Result")


class ExperimentWorkerPool(ABC, Generic[Task, Result]):
    """Execute independent experiment tasks and collect their results."""

    @abstractmethod
    def execute(
        self, fn: Callable[[Task], Result], items: list[Task], key_fn: Callable[[Task], str]
    ) -> dict[str, Result]:
        """Submit tasks to workers and return results indexed by task key."""
