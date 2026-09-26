"""Filesystem adapter for reading synthesized candidate code."""

from pathlib import Path

from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from shared.config import PROJECT_ROOT


class FilesystemCodeReader(CandidateCodeReader):
    def __init__(self, project_root: Path = PROJECT_ROOT) -> None:
        self.project_root = Path(project_root)

    def resolve(self, code_path: str | Path) -> Path:
        path = Path(code_path)
        return path if path.is_absolute() else self.project_root / path

    def exists(self, code_path: str | Path) -> bool:
        return self.resolve(code_path).is_file()

    def read(self, code_path: str | Path) -> str:
        return self.resolve(code_path).read_text(encoding="utf-8")
