"""Small application ports shared by benchmarking use cases."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import ContextManager, Protocol, TypedDict

import numpy as np
import pandas as pd

from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.domain.vos import EvaluationDataset
from evolution.domain.enums import NoiseModelEnum, SynthesisMode
from evolution.domain.interfaces import BaseProblem


class Champion(TypedDict, total=False):
    """Typed fields stored for a selected synthesis candidate."""

    problem_id: int
    dim: int
    mode: str
    noise_std: float
    prompt_strategy: str
    experiment_id: int
    iteration_id: int
    algorithm_name: str
    final_error: float
    evaluations_used: int | None
    code_path: str
    llm_name: str


ChampionCatalog = dict[str, dict[str, Champion]]


class MarkdownReportWriter(Protocol):
    def write(self, path: Path, content: str) -> None: ...


class CandidateCodeReader(Protocol):
    def exists(self, code_path: str | Path) -> bool: ...

    def read(self, code_path: str | Path) -> str: ...


class SynthesisReadRepository(Protocol):
    """Read-only experiment queries used by evaluation and analysis workflows."""

    def get_experiment_balance(self) -> tuple[pd.DataFrame, int]: ...

    def get_target_conditions(self) -> list[tuple[int, float, int]]: ...

    def get_completed_experiments_matrix(self) -> pd.DataFrame: ...

    def get_synthesis_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]: ...


class ChampionRepository(Protocol):
    """Read and export selected champion records."""

    def query_candidates(self) -> pd.DataFrame: ...

    def write_champions_json(
        self, champions: ChampionCatalog, output_path: Path | None = None
    ) -> Path: ...


class EvaluationConfigReader(Protocol):
    def load_config(self) -> EvaluationConfig: ...


class EvaluationTraceReader(Protocol):
    @property
    def eval_dir(self) -> Path: ...

    def get_run_count(self, solver_dir: Path) -> int: ...

    def load_evaluation_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
        solver_resolver: Callable[[str], str] | None = None,
    ) -> EvaluationDataset: ...


class EvaluationStateStore(Protocol):
    @property
    def eval_dir(self) -> Path: ...

    def solver_directory_exists(self, solver_dir: Path) -> bool: ...

    def remove_solver_traces(self, solver_dir: Path) -> None: ...

    def read_provenance(self, solver_dir: Path) -> dict[str, object] | None: ...

    def write_provenance(self, solver_dir: Path, data: dict[str, object]) -> None: ...

    def open_run_logger(
        self, target_dir: Path, algorithm_name: str, incremental: bool
    ) -> ContextManager[object]: ...


class EvaluationLoggerPort(Protocol):
    @property
    def verbose(self) -> bool: ...

    @verbose.setter
    def verbose(self, value: bool) -> None: ...

    def header(self, title: str, subtitle: str | None = None, width: int = 80) -> None: ...

    def condition_start(
        self,
        index: int,
        total: int,
        solver_type: str,
        solver_name: str,
        dim: int,
        noise_std: float,
        problem_id: int,
        problem_name: str,
        mode: SynthesisMode | str | None = None,
        strategy: str | None = None,
    ) -> None: ...

    def trial(
        self,
        trial_idx: int,
        total_trials: int,
        best_clean: float,
        runtime: float,
        evals_used: int,
        best_objective: float | None,
        true_optimum: float | None,
    ) -> None: ...

    def cached(self, runs_count: int, median_error: float | None) -> None: ...

    def resuming(self, existing_runs: int, target_runs: int) -> None: ...

    def condition_complete(self, n_runs: int, median_error: float | None) -> None: ...

    def missing_code(self, code_path: str) -> None: ...

    def summary(self, title: str, stats: Mapping[str, object], width: int = 80) -> None: ...


class ProblemFactory(Protocol):
    def create(
        self,
        problem_id: int,
        dim: int,
        noise_std: float,
        noise_model: NoiseModelEnum,
        instance_id: int,
        seed: int,
    ) -> BaseProblem: ...


class CandidateExecutorFactory(Protocol):
    def __call__(self, timeout_seconds: float) -> CandidateExecutor: ...


class CandidateExecutor(Protocol):
    def execute_algorithm(
        self,
        code: str,
        name: str,
        dim: int,
        problem: BaseProblem,
        budget: int,
    ) -> tuple[np.ndarray | None, float]: ...


class BaselineResolver(Protocol):
    def __call__(
        self, baseline_slug: str
    ) -> Callable[[BaseProblem, int], tuple[float, float, int]]: ...
