"""Immutable duplicate cleanup data."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Condition:
    model: str
    problem_id: int
    dimension: int
    instance: int
    mode: str
    noise: float
    noise_model: str
    strategy: str
    budget: int | None
    max_iterations: int | None


@dataclass(frozen=True)
class DuplicateRow:
    experiment_id: int
    condition: Condition
    status: str
    iterations: int
    champion_error: float | None
    evaluations: int | None
    code_available: bool
    valid_completed: bool
    action: Literal["keep", "delete"]
    reason: str


@dataclass(frozen=True)
class CleanupPlan:
    fingerprint: str
    rows: tuple[DuplicateRow, ...]
    models: tuple[str, ...]
    collapse_valid_runs: bool

    @property
    def delete_ids(self) -> tuple[int, ...]:
        return tuple(row.experiment_id for row in self.rows if row.action == "delete")

    @property
    def confirmation(self) -> str:
        return f"DELETE {len(self.delete_ids)} EXPERIMENTS"


@dataclass(frozen=True)
class CleanupResult:
    deleted_ids: tuple[int, ...]
    backup_directory: Path
    quarantined_paths: tuple[Path, ...]
