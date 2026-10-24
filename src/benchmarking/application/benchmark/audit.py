"""Read-only audit of synthesis availability and executable benchmark coverage."""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from benchmarking.application.benchmark.workload import BenchmarkWorkload
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.application.interfaces.synthesis_read_repository import SynthesisReadRepository


@dataclass(frozen=True, slots=True)
class SynthesisConditionSpec:
    problem_id: int
    dim: int
    noise_std: float
    mode: str
    strategy: str


@dataclass(frozen=True, slots=True)
class AuditCoverageSummary:
    total_cells: int
    completed_cells: int
    partial_cells: int
    missing_cells: int
    stale_cells: int
    missing_code_cells: int
    synthesis_gap_cells: int
    coverage_pct: float


@dataclass(frozen=True)
class AuditSnapshot:
    benchmarks: pd.DataFrame
    synthesis_gaps: pd.DataFrame
    coverage_summary: AuditCoverageSummary
    completed_models: tuple[str, ...]


class BenchmarkAuditService:
    """Report the same condition validity used by evaluation without writing traces."""

    def __init__(
        self,
        workload: BenchmarkWorkload,
        synthesis_reader: SynthesisReadRepository,
        planned_conditions: tuple[SynthesisConditionSpec, ...],
    ) -> None:
        self.workload = workload
        self.synthesis_reader = synthesis_reader
        self.planned_conditions = planned_conditions

    def get_audit_data(
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
        config = BenchmarkConfig(
            trials_per_condition=trials_per_condition,
            random_seed=random_seed,
            first_instance_id=first_instance_id,
            budget=budget,
            trial_timeout_seconds=trial_timeout_seconds,
            observation_trace_points=observation_trace_points,
            force_rerun=force_rerun,
            classical_baselines=list(classical_baselines),
            noise_robustness_enabled=noise_robustness_enabled,
            cross_function_enabled=cross_function_enabled,
            cross_function_problem_ids=list(cross_function_problem_ids),
        )
        experiments, _ = self.synthesis_reader.get_synthesis_dataframes()
        models = (
            tuple(
                sorted(
                    experiments.loc[experiments["status"] == "completed", "llm_name"]
                    .dropna()
                    .unique()
                )
            )
            if not experiments.empty
            else ()
        )
        champions = self.workload.champion_selection.flatten_champions()
        available = {
            (
                c["llm_name"],
                c["problem_id"],
                c["dim"],
                float(c.get("noise_std", 0.0)),
                c["mode"],
                c.get("prompt_strategy", "baseline"),
            )
            for c in champions.values()
        }
        gaps = pd.DataFrame(
            [
                {
                    "model": model,
                    "problem_id": spec.problem_id,
                    "dim": spec.dim,
                    "noise_std": spec.noise_std,
                    "mode": spec.mode,
                    "strategy": spec.strategy,
                    "status": "MISSING_CHAMPION",
                }
                for model in models
                for spec in self.planned_conditions
                if (model, spec.problem_id, spec.dim, spec.noise_std, spec.mode, spec.strategy)
                not in available
            ],
            columns=["model", "problem_id", "dim", "noise_std", "mode", "strategy", "status"],
        )
        benchmarks = self.workload.audit_workload(config=config)
        if not benchmarks.empty:
            benchmarks = benchmarks[
                (benchmarks["solver_type"] == "baseline") | benchmarks["model"].isin(models)
            ].copy()
            benchmarks["evaluation_kind"] = benchmarks["solver_type"].replace(
                {
                    "champion": "native",
                    "baseline": "native",
                }
            )
            benchmarks["eligible"] = ~benchmarks["is_filtered"] & (
                benchmarks["status"] != "MISSING_CODE"
            )
            eligible = benchmarks[benchmarks["eligible"]]
        else:
            eligible = benchmarks
        total = len(eligible)
        status = eligible["status"] if total else pd.Series(dtype=str)
        counts = eligible["runs_found"] if total else pd.Series(dtype=int)
        complete = int((status == "COMPLETED").sum())
        summary = AuditCoverageSummary(
            total_cells=total,
            completed_cells=complete,
            partial_cells=int(((status == "PENDING") & (counts > 0)).sum()),
            missing_cells=int(((status == "PENDING") & (counts == 0)).sum()),
            stale_cells=int((status == "NEEDS_RERUN").sum()),
            missing_code_cells=int((benchmarks["status"] == "MISSING_CODE").sum())
            if not benchmarks.empty
            else 0,
            synthesis_gap_cells=len(gaps),
            coverage_pct=100.0 * complete / total if total else 0.0,
        )
        return AuditSnapshot(benchmarks, gaps, summary, models)
