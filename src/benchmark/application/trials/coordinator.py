from typing import Literal

import numpy as np
import pandas as pd
from pydantic import validate_call

from benchmark.application.benchmark_config import BenchmarkConfig, ReliabilityConfig
from benchmark.application.interfaces.logger import BenchmarkLoggerInterface
from benchmark.application.trials.runner import BenchmarkTrialRunner
from benchmark.application.trials.summary import summarize_benchmarks
from benchmark.application.trials.workload import BenchmarkWorkload
from benchmark.domain.enums import BBOBFunction


class BenchmarkCoordinator:
    """Coordinate workload auditing and benchmark trial execution."""

    def __init__(
        self,
        workload: BenchmarkWorkload,
        trials: BenchmarkTrialRunner,
        baseline_labels: dict[str, str],
        logger: BenchmarkLoggerInterface,
    ) -> None:
        self.workload = workload
        self.trials = trials
        self.baseline_labels = baseline_labels
        self.logger = logger

    @validate_call(config={"strict": True})
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
        """Read current outcomes with explicit protocol settings and thresholds."""
        config = BenchmarkConfig(
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
            baseline_labels=self.baseline_labels,
            reliability=ReliabilityConfig(
                primary_target=primary_target, secondary_target=secondary_target
            ),
        )
        return summarize_benchmarks(self.workload, self.workload.state_repo, config)

    @validate_call(config={"strict": True})
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
        """Inspect the same protocol as execution without modifying stored results."""
        config = BenchmarkConfig(
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
            baseline_labels=self.baseline_labels,
        )
        return self.workload.audit_workload(solver_type, config=config)

    @validate_call(config={"strict": True})
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
        """Run pending/partial conditions using validated, invocation-local settings."""
        config = BenchmarkConfig(
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
            baseline_labels=self.baseline_labels,
        )
        self.logger.verbose = verbose
        tasks = self.workload.discover(solver_type, config=config)
        if not tasks:
            return pd.DataFrame()
        active = [task for task in tasks if task.inspection.status != "MISSING_CODE"]
        results: list[dict[str, object]] = []

        total_active = len(active)
        self.logger.header(
            title=f"Starting Benchmarks for {solver_type.upper()}",
            subtitle=f"{total_active} target conditions to evaluate",
        )
        cached_count = 0
        executed_count = 0

        for idx, task in enumerate(active, start=1):
            stype = task.solver_type
            dim = task.dim
            noise_std = task.noise_std
            p_id = task.problem_id

            self.logger.condition_start(
                index=idx,
                total=total_active,
                solver_type=stype,
                solver_name=task.display_name,
                dim=dim,
                noise_std=noise_std,
                problem_id=p_id,
                problem_name=BBOBFunction.get_name(p_id),
                mode=task.mode if task.champion is not None else None,
                strategy=task.strategy if task.champion is not None else None,
            )

            if task.champion is not None:
                res = self.trials.run_champion_trials(
                    task.champion,
                    config=config,
                    target_noise_std=noise_std,
                    solver_folder=task.solver,
                    verbose=verbose,
                    target_problem_id=p_id if stype == "cross_function" else None,
                )
            else:
                res = self.trials.run_baseline_trials(
                    config=config,
                    baseline_slug=task.solver,
                    dim=dim,
                    noise_std=noise_std,
                    p_id=p_id,
                    verbose=verbose,
                )

            if res.get("status") == "CACHED":
                cached_count += 1
            else:
                executed_count += 1

            results.append(
                {
                    "solver_type": stype,
                    "solver": task.solver,
                    "display_name": task.display_name,
                    "problem_id": p_id,
                    "source_problem_id": (
                        task.champion["problem_id"] if task.champion is not None else None
                    ),
                    "dim": dim,
                    "noise_std": noise_std,
                    "status": res["status"],
                    "median_error": res.get("median_clean_error"),
                    "median_best_objective": (
                        float(np.median(res["best_objectives"]))
                        if res.get("best_objectives")
                        else None
                    ),
                    "median_true_optimum": (
                        float(np.median(res["true_optima"])) if res.get("true_optima") else None
                    ),
                }
            )

        self.logger.summary(
            title=f"Completed {solver_type.title()} Benchmarks",
            stats={
                "Total": total_active,
                "Cached": cached_count,
                "Executed/Resumed": executed_count,
            },
        )
        return pd.DataFrame(results)
