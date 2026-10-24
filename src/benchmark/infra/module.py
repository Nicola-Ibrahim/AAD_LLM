"""Public benchmark module: scoped trials, audit and independent analysis operations."""

import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, Never

import pandas as pd
from dishka import Container, make_container

from benchmark.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmark.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
from benchmark.application.analysis.analyze_performance import AnalyzePerformance
from benchmark.application.analysis.analyze_reliability import AnalyzeReliability
from benchmark.application.analysis.results import (
    NoiseRobustnessResult,
    PerformanceAnalysisResult,
    ProfileAnalysisResult,
    ProfileMode,
    ReliabilityAnalysisResult,
)
from benchmark.application.benchmark_config import BenchmarkConfig, ReliabilityConfig
from benchmark.application.champions import ChampionCatalog
from benchmark.application.select_champions import ChampionSelectionService
from benchmark.application.trials.audit import (
    AuditSnapshot,
    BenchmarkAuditService,
    SynthesisConditionSpec,
)
from benchmark.application.trials.coordinator import BenchmarkCoordinator
from benchmark.domain.services.resolvers import LLMModelSpec, ModelNames
from benchmark.infra.di import BenchmarkProvider
from benchmark.infra.storage import SQLiteSynthesisReadRepository
from benchmark.infra.storage.analysis_results_store import AnalysisResult, AnalysisResultsStore
from shared.config import PROJECT_ROOT, RESULTS_DIR
from shared.infra.di import SharedProvider


def _analysis_config(
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
) -> BenchmarkConfig:
    """Build the same validated analysis settings previously supplied by notebook setup."""
    return BenchmarkConfig(
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


class BenchmarkModule:
    """Reusable notebook/CLI/API entry point; methods never return live backend services."""

    def __init__(
        self,
        project_root: Path = PROJECT_ROOT,
        *,
        results_dir: Path = RESULTS_DIR,
        planned_conditions: tuple[SynthesisConditionSpec, ...] = (),
    ) -> None:
        self._container = make_container(
            SharedProvider(),
            BenchmarkProvider(
                project_root=project_root,
                results_dir=results_dir,
                planned_conditions=planned_conditions,
            ),
        )
        self._owner_pid = os.getpid()
        self._closed = False

    def get_synthesis_balance(self) -> tuple[pd.DataFrame, int]:
        with self._operation({}) as scope:
            return scope.get(SQLiteSynthesisReadRepository).get_experiment_balance()

    def export_champions(self, output_path: Path) -> tuple[ChampionCatalog, pd.DataFrame]:
        with self._operation({}) as scope:
            return scope.get(ChampionSelectionService).export_champions(output_path)

    def get_model_registry(self) -> tuple[LLMModelSpec, ...]:
        """Return detached, immutable registry entries for caller-owned label formatting."""
        with self._operation({}) as scope:
            return scope.get(ModelNames).registry

    def audit_workload(
        self,
        *,
        trials_per_condition: int,
        random_seed: int,
        first_instance_id: int,
        budget: int,
        trial_timeout_seconds: float,
        observation_trace_points: int,
        force_rerun: bool,
        classical_baselines: list[str],
        noise_robustness_enabled: bool,
        cross_function_enabled: bool,
        cross_function_problem_ids: list[int],
        solver_type: Literal[
            "all", "champions", "baselines", "noise_robustness", "cross_function"
        ] = "all",
    ) -> pd.DataFrame:
        """Delegate within a fresh operation scope; return detached results."""
        with self._operation({}) as scope:
            return scope.get(BenchmarkCoordinator).audit_workload(
                trials_per_condition=trials_per_condition,
                random_seed=random_seed,
                first_instance_id=first_instance_id,
                budget=budget,
                trial_timeout_seconds=trial_timeout_seconds,
                observation_trace_points=observation_trace_points,
                force_rerun=force_rerun,
                classical_baselines=classical_baselines,
                noise_robustness_enabled=noise_robustness_enabled,
                cross_function_enabled=cross_function_enabled,
                cross_function_problem_ids=cross_function_problem_ids,
                solver_type=solver_type,
            )

    def run_benchmarks(
        self,
        *,
        trials_per_condition: int,
        random_seed: int,
        first_instance_id: int,
        budget: int,
        trial_timeout_seconds: float,
        observation_trace_points: int,
        force_rerun: bool,
        classical_baselines: list[str],
        noise_robustness_enabled: bool,
        cross_function_enabled: bool,
        cross_function_problem_ids: list[int],
        solver_type: Literal[
            "all", "champions", "baselines", "noise_robustness", "cross_function"
        ] = "all",
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Delegate within a fresh operation scope; return detached results."""
        with self._operation({}) as scope:
            return scope.get(BenchmarkCoordinator).run_benchmarks(
                trials_per_condition=trials_per_condition,
                random_seed=random_seed,
                first_instance_id=first_instance_id,
                budget=budget,
                trial_timeout_seconds=trial_timeout_seconds,
                observation_trace_points=observation_trace_points,
                force_rerun=force_rerun,
                classical_baselines=classical_baselines,
                noise_robustness_enabled=noise_robustness_enabled,
                cross_function_enabled=cross_function_enabled,
                cross_function_problem_ids=cross_function_problem_ids,
                solver_type=solver_type,
                verbose=verbose,
            )

    def summarize_results(
        self,
        *,
        trials_per_condition: int,
        random_seed: int,
        first_instance_id: int,
        budget: int,
        trial_timeout_seconds: float,
        observation_trace_points: int,
        force_rerun: bool,
        classical_baselines: list[str],
        noise_robustness_enabled: bool,
        cross_function_enabled: bool,
        cross_function_problem_ids: list[int],
        primary_target: float,
        secondary_target: float,
    ) -> pd.DataFrame:
        """Delegate within a fresh operation scope; return detached results."""
        with self._operation({}) as scope:
            return scope.get(BenchmarkCoordinator).summarize_results(
                trials_per_condition=trials_per_condition,
                random_seed=random_seed,
                first_instance_id=first_instance_id,
                budget=budget,
                trial_timeout_seconds=trial_timeout_seconds,
                observation_trace_points=observation_trace_points,
                force_rerun=force_rerun,
                classical_baselines=classical_baselines,
                noise_robustness_enabled=noise_robustness_enabled,
                cross_function_enabled=cross_function_enabled,
                cross_function_problem_ids=cross_function_problem_ids,
                primary_target=primary_target,
                secondary_target=secondary_target,
            )

    def audit_coverage(
        self,
        *,
        trials_per_condition: int = 20,
        random_seed: int = 42,
        first_instance_id: int = 2,
        budget: int = 100_000,
        trial_timeout_seconds: float = 30.0,
        observation_trace_points: int = 64,
        force_rerun: bool = False,
        classical_baselines: Sequence[str] = ("cmaes", "de", "pso"),
        noise_robustness_enabled: bool = True,
        cross_function_enabled: bool = False,
        cross_function_problem_ids: Sequence[int] = (1, 8, 11, 15, 21),
    ) -> AuditSnapshot:
        """Delegate within a fresh operation scope; return detached results."""
        with self._operation({}) as scope:
            return scope.get(BenchmarkAuditService).get_audit_data(
                trials_per_condition=trials_per_condition,
                random_seed=random_seed,
                first_instance_id=first_instance_id,
                budget=budget,
                trial_timeout_seconds=trial_timeout_seconds,
                observation_trace_points=observation_trace_points,
                force_rerun=force_rerun,
                classical_baselines=classical_baselines,
                noise_robustness_enabled=noise_robustness_enabled,
                cross_function_enabled=cross_function_enabled,
                cross_function_problem_ids=cross_function_problem_ids,
            )

    def analyze_ecdf_and_convergence(
        self,
        *,
        mode: ProfileMode,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
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
    ) -> ProfileAnalysisResult:
        """Calculate only this workflow; None filters mean unrestricted conditions."""
        config = _analysis_config(
            budget=budget,
            trials_per_condition=trials_per_condition,
            random_seed=random_seed,
            first_instance_id=first_instance_id,
            trial_timeout_seconds=trial_timeout_seconds,
            observation_trace_points=observation_trace_points,
            classical_baselines=classical_baselines,
            noise_robustness_enabled=noise_robustness_enabled,
            cross_function_enabled=cross_function_enabled,
            cross_function_problem_ids=cross_function_problem_ids,
            primary_prompt_strategy=primary_prompt_strategy,
            primary_target=primary_target,
            secondary_target=secondary_target,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
            checkpoint_fractions=checkpoint_fractions,
        )
        with self._operation({BenchmarkConfig: config}) as scope:
            return scope.get(AnalyzeEcdfAndConvergence).execute(
                mode=mode, dims=dims, problems=problems, noise_stds=noise_stds
            )

    def analyze_reliability(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
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
    ) -> ReliabilityAnalysisResult:
        """Calculate only this workflow; None filters mean unrestricted conditions."""
        config = _analysis_config(
            budget=budget,
            trials_per_condition=trials_per_condition,
            random_seed=random_seed,
            first_instance_id=first_instance_id,
            trial_timeout_seconds=trial_timeout_seconds,
            observation_trace_points=observation_trace_points,
            classical_baselines=classical_baselines,
            noise_robustness_enabled=noise_robustness_enabled,
            cross_function_enabled=cross_function_enabled,
            cross_function_problem_ids=cross_function_problem_ids,
            primary_prompt_strategy=primary_prompt_strategy,
            primary_target=primary_target,
            secondary_target=secondary_target,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
            checkpoint_fractions=checkpoint_fractions,
        )
        with self._operation({BenchmarkConfig: config}) as scope:
            return scope.get(AnalyzeReliability).execute(
                dims=dims, problems=problems, noise_stds=noise_stds
            )

    def analyze_noise_robustness(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
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
    ) -> NoiseRobustnessResult:
        """Calculate only this workflow; None filters mean unrestricted conditions."""
        config = _analysis_config(
            budget=budget,
            trials_per_condition=trials_per_condition,
            random_seed=random_seed,
            first_instance_id=first_instance_id,
            trial_timeout_seconds=trial_timeout_seconds,
            observation_trace_points=observation_trace_points,
            classical_baselines=classical_baselines,
            noise_robustness_enabled=noise_robustness_enabled,
            cross_function_enabled=cross_function_enabled,
            cross_function_problem_ids=cross_function_problem_ids,
            primary_prompt_strategy=primary_prompt_strategy,
            primary_target=primary_target,
            secondary_target=secondary_target,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
            checkpoint_fractions=checkpoint_fractions,
        )
        with self._operation({BenchmarkConfig: config}) as scope:
            return scope.get(AnalyzeNoiseRobustness).execute(
                dims=dims, problems=problems, noise_stds=noise_stds
            )

    def analyze_performance(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
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
    ) -> PerformanceAnalysisResult:
        """Calculate only this workflow; None filters mean unrestricted conditions."""
        config = _analysis_config(
            budget=budget,
            trials_per_condition=trials_per_condition,
            random_seed=random_seed,
            first_instance_id=first_instance_id,
            trial_timeout_seconds=trial_timeout_seconds,
            observation_trace_points=observation_trace_points,
            classical_baselines=classical_baselines,
            noise_robustness_enabled=noise_robustness_enabled,
            cross_function_enabled=cross_function_enabled,
            cross_function_problem_ids=cross_function_problem_ids,
            primary_prompt_strategy=primary_prompt_strategy,
            primary_target=primary_target,
            secondary_target=secondary_target,
            bootstrap_samples=bootstrap_samples,
            bootstrap_seed=bootstrap_seed,
            checkpoint_fractions=checkpoint_fractions,
        )
        with self._operation({BenchmarkConfig: config}) as scope:
            return scope.get(AnalyzePerformance).execute(
                dims=dims, problems=problems, noise_stds=noise_stds
            )

    def save_analysis_results(self, result: AnalysisResult) -> Path:
        """Persist already calculated numerical results; never calculate or render figures."""
        with self._operation({}) as scope:
            return scope.get(AnalysisResultsStore).save(result)

    def load_analysis_results(self, path: Path) -> AnalysisResult:
        with self._operation({}) as scope:
            return scope.get(AnalysisResultsStore).load(path)

    def close(self) -> None:
        """Close the module root once, in its owning process."""
        if self._closed or os.getpid() != self._owner_pid:
            return
        self._closed = True
        self._container.close()

    @contextmanager
    def _operation(self, context: dict[type, object]) -> Iterator[Container]:
        if os.getpid() != self._owner_pid:
            raise RuntimeError("Modules are process-local; create one in the current process.")
        if self._closed:
            raise RuntimeError("Module is closed. Create a new module before calling operations.")
        with self._container(context=context) as scope:
            yield scope

    def __getstate__(self) -> Never:
        raise TypeError("Module containers must not be serialized into worker tasks.")
