"""Application port for persisted synthesized source code."""

from pathlib import Path
from typing import Protocol


class SynthesisCodeStore(Protocol):
    """Store and retrieve source code produced during synthesis."""

    def save_code(self, code: str, iteration_num: int, experiment_id: int) -> Path: ...

    def load_code(self, code_path: str | Path) -> str: ...
