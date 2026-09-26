"""Abstract read interface for synthesis experiment data in benchmarking."""

from abc import ABC, abstractmethod

import pandas as pd


class SynthesisReadRepository(ABC):
    @abstractmethod
    def get_experiment_balance(self) -> tuple[pd.DataFrame, int]: ...

    @abstractmethod
    def get_target_conditions(self) -> list[tuple[int, float, int]]: ...

    @abstractmethod
    def get_completed_experiments_matrix(self) -> pd.DataFrame: ...

    @abstractmethod
    def get_synthesis_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]: ...
