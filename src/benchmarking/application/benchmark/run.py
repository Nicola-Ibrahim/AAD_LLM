import numpy as np
import pandas as pd

from benchmarking.application.benchmark.summary import summarize_benchmarks
from benchmarking.application.benchmark.trials import BenchmarkTrialRunner
from benchmarking.application.benchmark.workload import BenchmarkWorkload
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.application.interfaces.logger import BenchmarkLoggerInterface
from benchmarking.domain.enums import BBOBFunction


class BenchmarkService:
    """Coordinate workload auditing and benchmark trial execution."""

    def __init__(
        self,
        workload: BenchmarkWorkload,
        trials: BenchmarkTrialRunner,
        config: BenchmarkConfig,
        logger: BenchmarkLoggerInterface,
    ) -> None:
        self.logger = logger
        self.config = config
        self.workload = workload
        self.trials = trials

    def summarize_results(self) -> pd.DataFrame:
        """Inspect current saved outcomes without running or modifying experiments."""
        return summarize_benchmarks(self.workload, self.trials.state_repo, self.config)

    def run_benchmarks(
        self,
        solver_type: str = "all",
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial benchmarks matching the configured workload."""
        self.logger.verbose = verbose

        tasks = self.workload.discover(solver_type)
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
                    target_noise_std=noise_std,
                    solver_folder=task.solver,
                    verbose=verbose,
                    target_problem_id=p_id if stype == "cross_function" else None,
                )
            else:
                res = self.trials.run_baseline_trials(
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

    def run_champions(
        self,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial native champion benchmarks."""
        return self.run_benchmarks(solver_type="champions", verbose=verbose)

    def run_noise_robustness(
        self,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run frozen clean champions on their original functions with added noise."""
        return self.run_benchmarks(solver_type="noise_robustness", verbose=verbose)

    def run_cross_function_benchmarks(self, verbose: bool = True) -> pd.DataFrame:
        """Run opt-in cross-function trials and reuse paired clean baselines."""
        return self.run_benchmarks(solver_type="cross_function", verbose=verbose)

    def run_baselines(
        self,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """Run all pending/partial baseline benchmarks matching the config matrix."""
        return self.run_benchmarks(solver_type="baselines", verbose=verbose)
