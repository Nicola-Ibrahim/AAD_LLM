"""Abstract interface for writing analysis reports."""

from abc import ABC, abstractmethod
from pathlib import Path


class MarkdownReportWriter(ABC):
    @abstractmethod
    def write(self, path: Path, content: str) -> None: ...
