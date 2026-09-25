"""Construct benchmark evaluation and its notebook-facing collaborators."""

from dataclasses import dataclass
from pathlib import Path

from benchmarking.application.evaluation.run import EvaluationService
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import EvaluationStateRepository
from benchmarking.infra.logging import EvaluationLogger
from benchmarking.infra.solvers.baselines import get_baseline_runner
from benchmarking.infra.storage import (
    ChampionsReadRepository,
    EvaluationConfigRepository,
    SQLiteSynthesisReadRepository,
)
from benchmarking.infra.storage.model_registry import configured_model_names
from evolution.infra.execution.candidate_executor import create_candidate_executor
from evolution.infra.problems.factory import BBOBProblemFactory
from shared.config import PROJECT_ROOT
from shared.infra.database.engine import create_db_session_factory


@dataclass(frozen=True)
class EvaluationWorkflow:
    service: EvaluationService
    sqlite_repo: SQLiteSynthesisReadRepository
    champion_selection: ChampionSelectionService


def build_evaluation_workflow(project_root: Path = PROJECT_ROOT) -> EvaluationWorkflow:
    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    champions_repo = ChampionsReadRepository(session_factory)
    return EvaluationWorkflow(
        service=EvaluationService(
            sqlite_repo=sqlite_repo,
            champions_repo=champions_repo,
            state_repo=EvaluationStateRepository(),
            config_repo=EvaluationConfigRepository(),
            logger=EvaluationLogger(),
            problem_factory=BBOBProblemFactory(),
            executor_factory=create_candidate_executor,
            baseline_resolver=get_baseline_runner,
            code_reader=FilesystemCodeReader(project_root),
            model_names=configured_model_names(),
        ),
        sqlite_repo=sqlite_repo,
        champion_selection=ChampionSelectionService(champions_repo),
    )
