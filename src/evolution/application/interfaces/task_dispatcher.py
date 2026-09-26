"""Abstract interface for dispatching independent application tasks."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

Task = TypeVar("Task")
Result = TypeVar("Result")


class TaskDispatcher(ABC, Generic[Task, Result]):
    """Run keyed tasks using an infrastructure-selected execution strategy."""

    @abstractmethod
    def run(
        self, fn: Callable[[Task], Result], items: list[Task], key_fn: Callable[[Task], str]
    ) -> dict[str, Result]:
        """Dispatch all tasks and return results indexed by task key."""
