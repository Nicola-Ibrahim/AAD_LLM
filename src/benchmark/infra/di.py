"""Benchmark-owned Dishka bindings for execution, audit and analysis."""

from pathlib import Path

from dishka import AnyOf, Provider, Scope, from_context, provide
from sqlalchemy.orm import Session, sessionmaker

from benchmark.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmark.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
from benchmark.application.analysis.analyze_performance import AnalyzePerformance
from benchmark.application.analysis.analyze_reliability import AnalyzeReliability
from benchmark.application.analysis.data_loader import AnalysisDataLoader
from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.interfaces.benchmark_state_store import BenchmarkStateStore
from benchmark.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmark.application.interfaces.champion_repository import ChampionRepository
from benchmark.application.interfaces.logger import BenchmarkLoggerInterface
from benchmark.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmark.application.select_champions import ChampionSelectionService
from benchmark.application.trials.audit import BenchmarkAuditService, SynthesisConditionSpec
from benchmark.application.trials.coordinator import BenchmarkCoordinator
from benchmark.application.trials.runner import BenchmarkTrialRunner
from benchmark.application.trials.workload import BenchmarkWorkload
from benchmark.domain.services.ecdf import EcdfConvergenceEngine
from benchmark.domain.services.performance import PerformanceMetricsEngine
from benchmark.domain.services.reliability import ReliabilityEngine
from benchmark.domain.services.resolvers import ModelNames
from benchmark.domain.services.transfer import TransferAnalysisEngine
from benchmark.infra.io.code_reader import FilesystemCodeReader
from benchmark.infra.io.trace_repository import BenchmarkStateRepository, IOHTraceReader
from benchmark.infra.logging import BenchmarkLogger
from benchmark.infra.solvers.baselines import get_baseline_runner
from benchmark.infra.storage import ChampionsReadRepository, SQLiteSynthesisReadRepository
from benchmark.infra.storage.analysis_results_store import AnalysisResultsStore
from benchmark.infra.storage.model_registry import configured_model_names
from shared.config import PROJECT_ROOT, RESULTS_DIR
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.infra.execution.candidate_executor import create_candidate_executor


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
    ) -> BenchmarkCoordinator:
        return BenchmarkCoordinator(
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
