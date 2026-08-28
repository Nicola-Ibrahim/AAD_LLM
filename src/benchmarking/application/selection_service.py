"""Champion Selection Application Service (Notebook 03 Use Case).

Coordinates database balance audits, dynamic champion algorithm discovery,
and JSON serialization for empirical benchmarking.
"""

from pathlib import Path
from typing import Any
import pandas as pd

from benchmarking.infra.storage.champions_repository import ChampionsReadRepository
from benchmarking.infra.storage.sqlite_repository import SQLiteSynthesisReadRepository


class ChampionSelectionService:
    """Application use case for selecting and exporting problem-specific champions."""

    def __init__(
        self,
        sqlite_repo: SQLiteSynthesisReadRepository,
        champions_repo: ChampionsReadRepository,
    ):
        self.sqlite_repo = sqlite_repo
        self.champions_repo = champions_repo

    def get_experiment_balance(self) -> tuple[pd.DataFrame, int]:
        """Query DB for completed experiments balance summary."""
        return self.sqlite_repo.get_experiment_balance()

    def get_target_conditions(self) -> list[tuple[int, float, int]]:
        """Discover unique (dim, noise_std, problem_id) experimental conditions from DB."""
        return self.sqlite_repo.get_target_conditions()

    def get_champions(self) -> dict[str, dict[str, Any]]:
        """Extract best Clean and Noisy champions per LLM model and experimental condition."""
        return self.champions_repo.extract_champions()

    def get_champions_flat(
        self,
        champions_dict: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Flatten model-nested champions dictionary into a single key-value mapping."""
        return self.champions_repo.get_champions_flat(champions_dict)

    def export_champions(
        self,
        output_path: Path | None = None,
    ) -> tuple[dict[str, dict[str, Any]], pd.DataFrame]:
        """Discover champions from DB, export to champions.json, and return summary DataFrame."""
        return self.champions_repo.export_champions_json(output_path)
