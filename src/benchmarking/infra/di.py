"""Benchmarking-owned Dishka bindings for execution, audit and analysis."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from dishka import AnyOf, Provider, Scope, from_context, provide
from sqlalchemy.orm import Session, sessionmaker

from benchmarking.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmarking.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
from benchmarking.application.analysis.analyze_performance import AnalyzePerformance
from benchmarking.application.analysis.analyze_reliability import AnalyzeReliability
from benchmarking.application.analysis.data_loader import AnalysisDataLoader
from benchmarking.application.benchmark.audit import BenchmarkAuditService, SynthesisConditionSpec
from benchmarking.application.benchmark.run import BenchmarkService
from benchmarking.application.benchmark.trials import BenchmarkTrialRunner
from benchmarking.application.benchmark.workload import BenchmarkWorkload
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.application.interfaces.benchmark_state_store import BenchmarkStateStore
from benchmarking.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmarking.application.interfaces.champion_repository import ChampionRepository
from benchmarking.application.interfaces.logger import BenchmarkLoggerInterface
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import BenchmarkStateRepository, IOHTraceReader
from benchmarking.infra.logging import BenchmarkLogger
from benchmarking.infra.solvers.baselines import get_baseline_runner
from benchmarking.infra.storage import ChampionsReadRepository, SQLiteSynthesisReadRepository
from benchmarking.infra.storage.analysis_results_store import AnalysisResultsStore
from benchmarking.infra.storage.model_registry import configured_model_names
from shared.config import PROJECT_ROOT, RESULTS_DIR
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.infra.di import container_scope
from shared.infra.execution.candidate_executor import create_candidate_executor


@dataclass(frozen=True)
class BenchmarkWorkflow:
    service: BenchmarkService
    sqlite_repo: SQLiteSynthesisReadRepository
    champion_selection: ChampionSelectionService
    model_names: ModelNames
    audit: BenchmarkAuditService


@dataclass(frozen=True)
class AnalysisUseCases:
    ecdf_and_convergence: AnalyzeEcdfAndConvergence
    reliability: AnalyzeReliability
    noise_robustness: AnalyzeNoiseRobustness
    performance: AnalyzePerformance
    results_store: AnalysisResultsStore


class BenchmarkProvider(Provider):
    scope = Scope.REQUEST
    analysis_settings = from_context(provides=BenchmarkConfig)

    ecdf = provide(EcdfConvergenceEngine)
    performance = provide(PerformanceMetricsEngine)
    reliability = provide(ReliabilityEngine)
    conditions = provide(TransferAnalysisEngine)
    profiles = provide(AnalyzeEcdfAndConvergence)
    reliability_analysis = provide(AnalyzeReliability)
    noise_analysis = provide(AnalyzeNoiseRobustness)
    performance_analysis = provide(AnalyzePerformance)
    analysis = provide(AnalysisUseCases)
    workflow = provide(BenchmarkWorkflow)
    synthesis_reader = provide(
        SQLiteSynthesisReadRepository,
        provides=AnyOf[SQLiteSynthesisReadRepository, SynthesisReadRepository],
    )
    champion_selection = provide(ChampionSelectionService)

    @provide
    def logger(self) -> AnyOf[BenchmarkLogger, BenchmarkLoggerInterface]:
        return BenchmarkLogger()

    @provide
    def candidate_reader(
        self, session_factory: sessionmaker[Session]
    ) -> AnyOf[ChampionsReadRepository, ChampionRepository]:
        return ChampionsReadRepository(session_factory)

    def __init__(
        self,
        project_root: Path = PROJECT_ROOT,
        results_dir: Path = RESULTS_DIR,
        planned_conditions: tuple[SynthesisConditionSpec, ...] = (),
    ) -> None:
        super().__init__()
        self.project_root = project_root
        self.results_dir = results_dir
        self.planned_conditions = tuple(dict.fromkeys(planned_conditions))

    @provide
    def state(self) -> AnyOf[BenchmarkStateRepository, BenchmarkStateStore]:
        return BenchmarkStateRepository(benchmark_dir=self.results_dir / "ioh_traces")

    @provide
    def code_reader(self) -> AnyOf[FilesystemCodeReader, CandidateCodeReader]:
        return FilesystemCodeReader(self.project_root)

    @provide
    def model_names(self) -> ModelNames:
        return configured_model_names()

    @provide
    def workload(
        self,
        repository: SynthesisReadRepository,
        selection: ChampionSelectionService,
        state: BenchmarkStateStore,
        code: CandidateCodeReader,
        names: ModelNames,
    ) -> BenchmarkWorkload:
        return BenchmarkWorkload(
            sqlite_repo=repository,
            champion_selection=selection,
            state_repo=state,
            code_reader=code,
            model_names=names,
            planned_target_conditions=tuple(
                sorted(
                    {
                        (spec.dim, spec.noise_std, spec.problem_id)
                        for spec in self.planned_conditions
                    }
                )
            ),
        )

    @provide
    def trials(
        self,
        state: BenchmarkStateStore,
        logger: BenchmarkLoggerInterface,
        problem_factory: ProblemFactory,
        code: CandidateCodeReader,
        names: ModelNames,
    ) -> BenchmarkTrialRunner:
        return BenchmarkTrialRunner(
            state_repo=state,
            logger=logger,
            problem_factory=problem_factory,
            executor_factory=create_candidate_executor,
            baseline_resolver=get_baseline_runner,
            code_reader=code,
            model_names=names,
        )

    @provide
    def service(
        self,
        workload: BenchmarkWorkload,
        trials: BenchmarkTrialRunner,
        logger: BenchmarkLoggerInterface,
    ) -> BenchmarkService:
        return BenchmarkService(
            workload=workload,
            trials=trials,
            logger=logger,
            baseline_labels={
                "cmaes": "CMA-ES",
                "de": "Differential Evolution",
                "pso": "Particle Swarm Optimization",
            },
        )

    @provide
    def audit(
        self,
        workload: BenchmarkWorkload,
        repository: SynthesisReadRepository,
    ) -> BenchmarkAuditService:
        return BenchmarkAuditService(workload, repository, self.planned_conditions)

    @provide
    def analysis_loader(
        self,
        repository: SynthesisReadRepository,
        code: CandidateCodeReader,
        selection: ChampionSelectionService,
        names: ModelNames,
        config: BenchmarkConfig,
        classifier: TransferAnalysisEngine,
    ) -> AnalysisDataLoader:
        return AnalysisDataLoader(
            repository,
            IOHTraceReader(self.results_dir / "ioh_traces"),
            IOHTraceReader(self.results_dir / "cross_function_traces"),
            code,
            selection,
            names,
            config,
            classifier,
        )

    @provide
    def analysis_store(self) -> AnalysisResultsStore:
        return AnalysisResultsStore(self.results_dir / "analysis")


@contextmanager
def benchmark_scope(
    project_root: Path = PROJECT_ROOT,
    *,
    planned_conditions: tuple[SynthesisConditionSpec, ...] = (),
) -> Iterator[BenchmarkWorkflow]:
    """Supply ready execution/audit services; parameters stay on their methods."""
    with container_scope(
        BenchmarkProvider(project_root=project_root, planned_conditions=planned_conditions),
        context={},
        request_context={},
    ) as container:
        yield container.get(BenchmarkWorkflow)


@contextmanager
def analysis_scope(config: BenchmarkConfig) -> Iterator[AnalysisUseCases]:
    """Compose one analysis job from explicit, validated scientific settings."""
    with container_scope(
        BenchmarkProvider(),
        context={},
        request_context={BenchmarkConfig: config},
    ) as container:
        yield container.get(AnalysisUseCases)
