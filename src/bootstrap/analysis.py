"""Compose analysis use cases; notebook results outlive database resources."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from benchmarking.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmarking.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
from benchmarking.application.analysis.analyze_performance import AnalyzePerformance
from benchmarking.application.analysis.analyze_reliability import AnalyzeReliability
from benchmarking.application.analysis.data_loader import AnalysisDataLoader
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage import (
    ChampionsReadRepository,
    EvaluationConfigRepository,
    SQLiteSynthesisReadRepository,
)
from benchmarking.infra.storage.analysis_results_store import AnalysisResultsStore
from benchmarking.infra.storage.model_registry import configured_model_names
from shared.config import PROJECT_ROOT, RESULTS_DIR
from shared.infra.database import Database


@dataclass(frozen=True)
class AnalysisUseCases:
    ecdf_and_convergence: AnalyzeEcdfAndConvergence
    reliability: AnalyzeReliability
    noise_robustness: AnalyzeNoiseRobustness
    performance: AnalyzePerformance


def build_analysis_results_store() -> AnalysisResultsStore:
    """Compose numeric persistence independently of database-backed calculation."""
    return AnalysisResultsStore(RESULTS_DIR / "analysis")


@contextmanager
def build_analysis_use_cases() -> Iterator[AnalysisUseCases]:
    database = Database()
    try:
        classifier = TransferAnalysisEngine()
        loader = AnalysisDataLoader(
            SQLiteSynthesisReadRepository(database.session_factory),
            IOHTraceReader(),
            IOHTraceReader(RESULTS_DIR / "cross_function_traces"),
            FilesystemCodeReader(PROJECT_ROOT),
            ChampionSelectionService(ChampionsReadRepository(database.session_factory)),
            configured_model_names(),
            EvaluationConfigRepository().load_config(),
            classifier,
        )
        yield AnalysisUseCases(
            AnalyzeEcdfAndConvergence(loader, EcdfConvergenceEngine()),
            AnalyzeReliability(loader, classifier, ReliabilityEngine()),
            AnalyzeNoiseRobustness(loader, classifier),
            AnalyzePerformance(loader, EcdfConvergenceEngine(), PerformanceMetricsEngine()),
        )
    finally:
        database.dispose()
