"""Construct analysis data access from concrete repositories."""

from benchmarking.application.analysis.data import AnalysisData
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage import SQLiteSynthesisReadRepository
from benchmarking.infra.storage.model_registry import configured_model_names
from shared.infra.database import Database


def build_analysis_data() -> AnalysisData:
    database = Database()
    return AnalysisData(
        sqlite_repo=SQLiteSynthesisReadRepository(database.session_factory),
        trace_repo=IOHTraceReader(),
        model_names=configured_model_names(),
    )
