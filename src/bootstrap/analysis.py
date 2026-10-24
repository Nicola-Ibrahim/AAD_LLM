"""Compose analysis use cases; notebook results outlive database resources."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass

from benchmarking.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmarking.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
from benchmarking.application.analysis.analyze_performance import AnalyzePerformance
from benchmarking.application.analysis.analyze_reliability import AnalyzeReliability
from benchmarking.application.analysis.data_loader import AnalysisDataLoader
from benchmarking.application.benchmark_config import BenchmarkConfig, ReliabilityConfig
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.infra.storage import (
    ChampionsReadRepository,
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
def build_analysis_use_cases(
    *,
    budget: int = 100_000,
    trials_per_condition: int = 20,
    random_seed: int = 42,
    first_instance_id: int = 2,
    trial_timeout_seconds: float = 30.0,
    observation_trace_points: int = 64,
    classical_baselines: Sequence[str] = ("cmaes", "de", "pso"),
    noise_robustness_enabled: bool = True,
    cross_function_enabled: bool = False,
    cross_function_problem_ids: Sequence[int] = (1, 8, 11, 15, 21),
    primary_prompt_strategy: str = "baseline",
    primary_target: float = 1e-8,
    secondary_target: float = 1e-2,
    bootstrap_samples: int = 1000,
    bootstrap_seed: int = 20260923,
    checkpoint_fractions: Sequence[float] = (0.01, 0.1, 0.5, 1.0),
) -> Iterator[AnalysisUseCases]:
    config = BenchmarkConfig(
        budget=budget,
        trials_per_condition=trials_per_condition,
        random_seed=random_seed,
        first_instance_id=first_instance_id,
        trial_timeout_seconds=trial_timeout_seconds,
        observation_trace_points=observation_trace_points,
        classical_baselines=list(classical_baselines),
        noise_robustness_enabled=noise_robustness_enabled,
        cross_function_enabled=cross_function_enabled,
        cross_function_problem_ids=list(cross_function_problem_ids),
        reliability=ReliabilityConfig(
            primary_prompt_strategy=primary_prompt_strategy,
            primary_target=primary_target,
            secondary_target=secondary_target,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
            checkpoint_fractions=list(checkpoint_fractions),
        ),
    )
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
            config,
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
