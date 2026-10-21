"""Construct the benchmark workflow and its notebook-facing collaborators."""

from dataclasses import dataclass
from pathlib import Path

from benchmarking.application.benchmark.run import BenchmarkService
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import BenchmarkStateRepository
from benchmarking.infra.logging import BenchmarkLogger
from benchmarking.infra.solvers.baselines import get_baseline_runner
from benchmarking.infra.storage import (
    BenchmarkConfigRepository,
    ChampionsReadRepository,
    SQLiteSynthesisReadRepository,
)
from benchmarking.infra.storage.model_registry import configured_model_names
from shared.config import PROJECT_ROOT
from shared.infra.database import Database
from shared.infra.execution.candidate_executor import create_candidate_executor
from shared.infra.problems.factory import BBOBProblemFactory


@dataclass(frozen=True)
class BenchmarkWorkflow:
    service: BenchmarkService
    sqlite_repo: SQLiteSynthesisReadRepository
    champion_selection: ChampionSelectionService


def build_benchmark_workflow(
    project_root: Path = PROJECT_ROOT,
    *,
    planned_target_conditions: tuple[tuple[int, float, int], ...] = (),
) -> BenchmarkWorkflow:
    database = Database()
    sqlite_repo = SQLiteSynthesisReadRepository(database.session_factory)
    champions_repo = ChampionsReadRepository(database.session_factory)
    config = BenchmarkConfigRepository().load_config()
    return BenchmarkWorkflow(
        service=BenchmarkService(
            sqlite_repo=sqlite_repo,
            champions_repo=champions_repo,
            state_repo=BenchmarkStateRepository(),
            config=config,
            logger=BenchmarkLogger(),
            problem_factory=BBOBProblemFactory(),
            executor_factory=create_candidate_executor,
            baseline_resolver=get_baseline_runner,
            code_reader=FilesystemCodeReader(project_root),
            model_names=configured_model_names(),
            planned_target_conditions=planned_target_conditions,
        ),
        sqlite_repo=sqlite_repo,
        champion_selection=ChampionSelectionService(champions_repo),
    )
