"""Read-only audit of synthesis availability and executable benchmark coverage."""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import pandas as pd

from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.champions import Champion
from benchmark.application.interfaces.logger import BenchmarkLoggerInterface
from benchmark.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmark.application.trials.workload import BenchmarkWorkload
from shared.application.result import Result


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
    invalid_artifact_cells: int = 0


@dataclass(frozen=True)
class AuditSnapshot:
    benchmarks: pd.DataFrame
    synthesis_gaps: pd.DataFrame
    coverage_summary: AuditCoverageSummary
    completed_models: tuple[str, ...]
    synthesis_coverage: pd.DataFrame = field(default_factory=pd.DataFrame)
    coverage_by_model: pd.DataFrame = field(default_factory=pd.DataFrame)
    synthesis_issues: pd.DataFrame = field(default_factory=pd.DataFrame)


def _champion_condition(candidate: Champion) -> SynthesisConditionSpec:
    return SynthesisConditionSpec(
        candidate["problem_id"],
        candidate["dim"],
        candidate["noise_std"],
        candidate["mode"],
        candidate["prompt_strategy"],
    )


def _planned_synthesis_coverage(
    plan: Mapping[str, set[SynthesisConditionSpec]],
    experiments: pd.DataFrame,
    iterations: pd.DataFrame,
    champions: dict[str, Champion],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    champion_ids = {
        (candidate["llm_name"], _champion_condition(candidate)): candidate["experiment_id"]
        for candidate in champions.values()
    }
    history: dict[tuple[str, SynthesisConditionSpec], list[int]] = defaultdict(list)
    observed: dict[tuple[str, SynthesisConditionSpec], set[str]] = defaultdict(set)
    candidate_counts = iterations["experiment_id"].value_counts().to_dict()
    issues = []
    for experiment in experiments.itertuples(index=False):
        condition = SynthesisConditionSpec(
            experiment.problem_id,
            experiment.dim,
            0.0 if pd.isna(experiment.noise_std) else experiment.noise_std,
            experiment.mode,
            experiment.prompt_strategy,
        )
        key = (experiment.llm_name, condition)
        if condition not in plan.get(experiment.llm_name, ()):
            continue
        observed[key].add(experiment.status)
        count = candidate_counts.get(experiment.id, 0)
        if (
            experiment.status == "completed"
            and pd.notna(experiment.max_iterations)
            and experiment.max_iterations > 0
            and count == experiment.max_iterations
        ):
            history[key].append(experiment.id)
        else:
            reason = (
                "Experiment is not completed."
                if experiment.status != "completed"
                else "Configured generation count is missing."
                if pd.isna(experiment.max_iterations)
                else "Recorded generation count does not match the configured count."
            )
            issues.append(
                (
                    experiment.llm_name,
                    condition.problem_id,
                    condition.dim,
                    condition.noise_std,
                    condition.mode,
                    condition.strategy,
                    experiment.id,
                    experiment.status,
                    experiment.max_iterations,
                    count,
                    reason,
                )
            )

    rows = []
    for model, conditions in plan.items():
        for spec in sorted(
            conditions, key=lambda c: (c.problem_id, c.dim, c.noise_std, c.mode, c.strategy)
        ):
            key = (model, spec)
            champion_id = champion_ids.get(key)
            history_ids = tuple(sorted(history[key]))
            statuses = observed[key]
            if not statuses:
                reason = "No synthesis experiment is recorded for this condition."
            elif not history_ids and "completed" not in statuses:
                reason = "Synthesis statuses here are " + ", ".join(sorted(statuses)) + "."
            elif not history_ids:
                reason = "No completed experiment has its full configured generation history."
            elif champion_id is None:
                reason = "Complete generation history exists, but there is no valid champion."
            else:
                reason = ""
            rows.append(
                {
                    "model": model,
                    "problem_id": spec.problem_id,
                    "dim": spec.dim,
                    "noise_std": spec.noise_std,
                    "mode": spec.mode,
                    "strategy": spec.strategy,
                    "has_champion": champion_id is not None,
                    "champion_experiment_id": champion_id,
                    "has_full_history": bool(history_ids),
                    "full_history_experiment_ids": history_ids,
                    "status": "MISSING_CHAMPION"
                    if champion_id is None
                    else "MISSING_FULL_HISTORY"
                    if not history_ids
                    else "COMPLETE",
                    "reason": reason,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(
        issues,
        columns=[
            "model",
            "problem_id",
            "dim",
            "noise_std",
            "mode",
            "strategy",
            "experiment_id",
            "experiment_status",
            "configured_generations",
            "recorded_generations",
            "reason",
        ],
    )


def _benchmark_coverage_summary(
    benchmarks: pd.DataFrame, synthesis_gap_cells: int
) -> AuditCoverageSummary:
    eligible = benchmarks.loc[benchmarks["eligible"]] if not benchmarks.empty else benchmarks
    total = len(eligible)
    status = eligible["status"] if total else pd.Series(dtype=str)
    counts = eligible["runs_found"] if total else pd.Series(dtype=int)
    complete = int(status.eq("COMPLETED").sum())
    return AuditCoverageSummary(
        total_cells=total,
        completed_cells=complete,
        partial_cells=int((status.eq("PENDING") & counts.gt(0)).sum()),
        missing_cells=int((status.eq("PENDING") & counts.eq(0)).sum()),
        stale_cells=int(status.eq("NEEDS_RERUN").sum()),
        invalid_artifact_cells=int(status.eq("INVALID_ARTIFACT").sum()),
        missing_code_cells=int(benchmarks["status"].eq("MISSING_CODE").sum())
        if not benchmarks.empty
        else 0,
        synthesis_gap_cells=synthesis_gap_cells,
        coverage_pct=100.0 * complete / total if total else 0.0,
    )


def _planned_model_summary(synthesis: pd.DataFrame, benchmarks: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, benchmarks_by_model in benchmarks.groupby("model", sort=False):
        synth_cells = synthesis.loc[synthesis["model"].eq(model)]
        status = benchmarks_by_model["status"]
        rows.append(
            {
                "model": model,
                "planned_cells": len(benchmarks_by_model),
                "champion_cells": int(synth_cells["has_champion"].sum())
                if not synth_cells.empty
                else pd.NA,
                "full_history_cells": int(synth_cells["has_full_history"].sum())
                if not synth_cells.empty
                else pd.NA,
                "benchmark_completed_cells": int(status.eq("COMPLETED").sum()),
                "benchmark_pending_cells": int(status.eq("PENDING").sum()),
                "benchmark_partial_cells": int(
                    (status.eq("PENDING") & benchmarks_by_model["runs_found"].gt(0)).sum()
                ),
                "benchmark_stale_cells": int(status.eq("NEEDS_RERUN").sum()),
                "benchmark_invalid_cells": int(status.eq("INVALID_ARTIFACT").sum()),
                "benchmark_missing_code_cells": int(status.eq("MISSING_CODE").sum()),
                "benchmark_missing_champion_cells": int(status.eq("MISSING_CHAMPION").sum()),
            }
        )
    return pd.DataFrame(rows)


class BenchmarkAuditService:
    """Report the same condition validity used by evaluation without writing traces."""

    def __init__(
        self,
        workload: BenchmarkWorkload,
        synthesis_reader: SynthesisReadRepository,
        planned_conditions: tuple[SynthesisConditionSpec, ...],
        logger: BenchmarkLoggerInterface,
    ) -> None:
        self.logger = logger
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
        cross_function_enabled: bool = False,
        cross_function_problem_ids: Sequence[int] = (1, 8, 11, 15, 21),
        planned_models: Mapping[str, Sequence[SynthesisConditionSpec]] | None = None,
    ) -> Result[AuditSnapshot]:
        try:
            with self.logger.operation("coverage audit"):
                config = BenchmarkConfig(
                    trials_per_condition=trials_per_condition,
                    random_seed=random_seed,
                    first_instance_id=first_instance_id,
                    budget=budget,
                    trial_timeout_seconds=trial_timeout_seconds,
                    observation_trace_points=observation_trace_points,
                    force_rerun=force_rerun,
                    classical_baselines=list(classical_baselines),
                    cross_function_enabled=cross_function_enabled,
                    cross_function_problem_ids=list(cross_function_problem_ids),
                )
                experiments, iterations = self.synthesis_reader.get_synthesis_dataframes()
                champions = self.workload.champion_selection.flatten_champions()
                if planned_models is not None:
                    return Result.success(
                        self._audit_plan(planned_models, experiments, iterations, champions, config)
                    )
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
                        if (
                            model,
                            spec.problem_id,
                            spec.dim,
                            spec.noise_std,
                            spec.mode,
                            spec.strategy,
                        )
                        not in available
                    ],
                    columns=[
                        "model",
                        "problem_id",
                        "dim",
                        "noise_std",
                        "mode",
                        "strategy",
                        "status",
                    ],
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
                summary = _benchmark_coverage_summary(benchmarks, len(gaps))
                return Result.success(AuditSnapshot(benchmarks, gaps, summary, models))
        except Exception as error:
            return Result.failure("coverage audit", error)

    def _audit_plan(
        self,
        planned_models: Mapping[str, Sequence[SynthesisConditionSpec]],
        experiments: pd.DataFrame,
        iterations: pd.DataFrame,
        champions: dict[str, Champion],
        config: BenchmarkConfig,
    ) -> AuditSnapshot:
        """Audit only the declared model conditions and classical native targets."""
        plan = {
            model: set(conditions) for model, conditions in planned_models.items() if conditions
        }
        if not plan:
            raise ValueError("The study plan must contain at least one model condition.")
        selected = {
            key: candidate
            for key, candidate in champions.items()
            if _champion_condition(candidate) in plan.get(candidate["llm_name"], ())
        }
        coverage, issues = _planned_synthesis_coverage(plan, experiments, iterations, selected)
        gaps = coverage.loc[~coverage["has_champion"]].copy()
        targets = sorted(
            {
                (spec.dim, spec.noise_std, spec.problem_id)
                for spec in self.planned_conditions
                or tuple(spec for conditions in plan.values() for spec in conditions)
            }
        )
        benchmarks = self.workload.audit_planned_native_workload(selected, targets, config=config)
        if not benchmarks.empty:
            benchmarks["eligible"] = ~benchmarks["is_filtered"] & (
                benchmarks["status"] != "MISSING_CODE"
            )
        if not gaps.empty:
            missing = gaps[
                ["model", "problem_id", "dim", "noise_std", "mode", "strategy", "status", "reason"]
            ].assign(
                solver_type="champion",
                eligible=False,
                is_filtered=False,
                target_runs=config.trials_per_condition,
                runs_found=0,
                recorded_trials=0,
            )
            benchmarks = pd.concat([benchmarks, missing], ignore_index=True)
        benchmarks["evaluation_kind"] = "native"
        by_model = _planned_model_summary(coverage, benchmarks)
        return AuditSnapshot(
            benchmarks,
            gaps,
            _benchmark_coverage_summary(benchmarks, len(gaps)),
            tuple(
                sorted(
                    set(experiments.loc[experiments["status"] == "completed", "llm_name"])
                    & plan.keys()
                )
            ),
            coverage,
            by_model,
            issues,
        )
