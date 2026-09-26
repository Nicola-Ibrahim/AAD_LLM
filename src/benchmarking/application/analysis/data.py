from collections.abc import Callable
import pandas as pd

from benchmarking.application.interfaces.evaluation_trace_reader import EvaluationTraceReader
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.hypothesis import HypothesisTestingEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.domain.vos import EvaluationDataset


class AnalysisData:
    """Load experiment data and expose the scientific engines used by analysis notebooks."""

    def __init__(
        self,
        sqlite_repo: SynthesisReadRepository,
        trace_repo: EvaluationTraceReader,
        model_names: ModelNames,
    ) -> None:
        self.sqlite_repo = sqlite_repo
        self.trace_repo = trace_repo
        self.model_names = model_names
        self.hypothesis_engine = HypothesisTestingEngine()
        self.ecdf_engine = EcdfConvergenceEngine()
        self.performance_engine = PerformanceMetricsEngine()
        self.reliability_engine = ReliabilityEngine()

    def get_synthesis_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        return self.sqlite_repo.get_synthesis_dataframes()

    def load_evaluation_traces(
        self,
        dims: list[int] | None = None,
        problems: list[int] | None = None,
        noise_stds: list[float] | None = None,
        solvers: list[str] | None = None,
        solver_resolver: Callable[[str], str] | None = None,
    ) -> EvaluationDataset:
        return self.trace_repo.load_evaluation_traces(
            dims=dims,
            problems=problems,
            noise_stds=noise_stds,
            solvers=solvers,
            solver_resolver=solver_resolver or self.model_names.resolve_folder_solver_name,
        )
