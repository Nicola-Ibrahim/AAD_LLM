"""Abstract interface for loading champion source code."""

from abc import ABC, abstractmethod
from pathlib import Path


class CandidateCodeReader(ABC):
    @abstractmethod
    def exists(self, code_path: str | Path) -> bool: ...

    @abstractmethod
    def read(self, code_path: str | Path) -> str: ...
