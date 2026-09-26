"""Abstract persistence interface for synthesized source code."""

from abc import ABC, abstractmethod
from pathlib import Path


class SynthesisCodeStore(ABC):
    """Store and retrieve source code produced during synthesis."""

    @abstractmethod
    def save_code(self, code: str, iteration_num: int, experiment_id: int) -> Path:
        """Persist one generated candidate and return its path."""

    @abstractmethod
    def load_code(self, code_path: str | Path) -> str:
        """Load generated source code from its stored path."""
