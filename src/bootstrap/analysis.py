"""Construct analysis data access from concrete repositories."""

from benchmarking.application.analysis.data import AnalysisData
from benchmarking.application.analysis.view_data import AnalysisInputs, load_analysis_inputs
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage import (
    ChampionsReadRepository,
    EvaluationConfigRepository,
    SQLiteSynthesisReadRepository,
)
from benchmarking.infra.storage.model_registry import configured_model_names
from shared.config import PROJECT_ROOT, RESULTS_DIR
from shared.infra.database import Database


def build_analysis_data() -> AnalysisData:
    database = Database()
    return AnalysisData(
        sqlite_repo=SQLiteSynthesisReadRepository(database.session_factory),
        trace_repo=IOHTraceReader(),
        model_names=configured_model_names(),
    )


def build_analysis_inputs(
    *,
    include_transfer: bool = False,
    dims: list[int] | None = None,
    problems: list[int] | None = None,
    noise_stds: list[float] | None = None,
) -> AnalysisInputs:
    database = Database()
    try:
        service = AnalysisData(
            sqlite_repo=SQLiteSynthesisReadRepository(database.session_factory),
            trace_repo=IOHTraceReader(),
            model_names=configured_model_names(),
        )
        champions = ChampionSelectionService(
            ChampionsReadRepository(database.session_factory)
        ).get_champions()
        return load_analysis_inputs(
            service,
            champions,
            FilesystemCodeReader(PROJECT_ROOT),
            IOHTraceReader(RESULTS_DIR / "cross_function_traces"),
            EvaluationConfigRepository().load_config(),
            include_transfer=include_transfer,
            dims=dims,
            problems=problems,
            noise_stds=noise_stds,
        )
    finally:
        database.dispose()
