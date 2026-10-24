"""Construct the benchmark workflow and its notebook-facing collaborators."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from benchmarking.application.benchmark.run import BenchmarkService
from benchmarking.application.benchmark.trials import BenchmarkTrialRunner
from benchmarking.application.benchmark.workload import BenchmarkWorkload
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import BenchmarkStateRepository
from benchmarking.infra.logging import BenchmarkLogger
from benchmarking.infra.solvers.baselines import get_baseline_runner
from benchmarking.infra.storage import (
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
    model_names: ModelNames


@contextmanager
def build_benchmark_workflow(
    project_root: Path = PROJECT_ROOT,
    *,
    planned_target_conditions: tuple[tuple[int, float, int], ...] = (),
) -> Iterator[BenchmarkWorkflow]:
    database = Database()
    try:
        sqlite_repo = SQLiteSynthesisReadRepository(database.session_factory)
        champions_repo = ChampionsReadRepository(database.session_factory)
        selection = ChampionSelectionService(champions_repo)
        state = BenchmarkStateRepository()
        logger = BenchmarkLogger()
        code_reader = FilesystemCodeReader(project_root)
        model_names = configured_model_names()

        workload = BenchmarkWorkload(
            sqlite_repo=sqlite_repo,
            champion_selection=selection,
            state_repo=state,
            code_reader=code_reader,
            model_names=model_names,
            planned_target_conditions=planned_target_conditions,
        )

        trials = BenchmarkTrialRunner(
            state_repo=state,
            logger=logger,
            problem_factory=BBOBProblemFactory(),
            executor_factory=create_candidate_executor,
            baseline_resolver=get_baseline_runner,
            code_reader=code_reader,
            model_names=model_names,
        )

        yield BenchmarkWorkflow(
            service=BenchmarkService(
                workload=workload,
                trials=trials,
                baseline_labels={
                    "cmaes": "CMA-ES",
                    "de": "Differential Evolution",
                    "pso": "Particle Swarm Optimization",
                },
                logger=logger,
            ),
            sqlite_repo=sqlite_repo,
            champion_selection=selection,
            model_names=model_names,
        )
    finally:
        database.dispose()
