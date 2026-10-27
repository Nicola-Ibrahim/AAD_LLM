"""Domain persistence contract for code belonging to synthesis iterations."""

from abc import ABC, abstractmethod


class CodeRepository(ABC):
    """Persist generated code under its owning experiment and iteration."""

    @abstractmethod
    def save_code(self, code: str, iteration_num: int, experiment_id: int) -> str:
        """Persist one generated candidate and return its stored reference."""

    @abstractmethod
    def clear_experiment(self, experiment_id: int) -> None:
        """Remove generated code belonging only to the selected experiment."""
