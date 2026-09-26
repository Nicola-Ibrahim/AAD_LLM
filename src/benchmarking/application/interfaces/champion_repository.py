"""Abstract read/export interface for selected champions."""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from benchmarking.application.champions import ChampionCatalog


class ChampionRepository(ABC):
    @abstractmethod
    def query_candidates(self) -> pd.DataFrame: ...

    @abstractmethod
    def write_champions_json(
        self, champions: ChampionCatalog, output_path: Path | None = None
    ) -> Path: ...
