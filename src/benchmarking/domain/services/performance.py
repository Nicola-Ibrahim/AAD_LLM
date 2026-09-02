"""Performance metrics, robustness profiles, and BBOB hardness evaluations."""

from typing import Any, cast

import numpy as np
import pandas as pd

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace


class PerformanceMetricsEngine:
    """Computational engine for success rates, fragility index matrices, and problem hardness breakdown."""

    @staticmethod
    def compute_success_rate(
        runs: list[RunTrace],
        threshold: float = 1e-8,
    ) -> float:
        """Compute empirical success rate (fraction of runs reaching delta_y <= threshold)."""
        if not runs:
            return 0.0
        successes = sum(1 for r in runs if r.is_success(threshold))
        return successes / len(runs)

    def compute_fragility_matrix(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[np.ndarray, list[str]]:
        """Compute the Fragility Index matrix (Clean Success Rate - Noisy Success Rate) per problem & solver."""
        matrix = np.zeros((len(problem_ids), len(solvers)))
        problem_labels: list[str] = []

        for r_idx, p_id in enumerate(problem_ids):
            p_name = BBOBFunction.get_name(p_id)
            p_class = BBOBFunction.get_class(p_id)
            problem_labels.append(f"<b>{p_name}</b><br><sup>{p_class}</sup>")

            c_key = EvaluationCondition(dim=dim, noise_std=clean_std, problem_id=p_id)
            n_key = EvaluationCondition(dim=dim, noise_std=noisy_std, problem_id=p_id)

            for c_idx, solver in enumerate(solvers):
                c_runs = benchmark_data.get(c_key, {}).get(solver, [])
                n_runs = benchmark_data.get(n_key, {}).get(solver, [])
                c_succ = self.compute_success_rate(c_runs, threshold=threshold)
                n_succ = self.compute_success_rate(n_runs, threshold=threshold)
                matrix[r_idx, c_idx] = c_succ - n_succ

        return matrix, problem_labels

    def compute_hardness_success_rates(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers_list: list[str],
        noise_level: float,
        threshold: float = 1e-8,
    ) -> pd.DataFrame:
        """Aggregate solver success rates grouped by BBOB landscape hardness class."""
        prob_records = []
        for cond, solvers in benchmark_data.items():
            if cond.dim != dim or not np.isclose(cond.noise_std, noise_level):
                continue
            p_name = BBOBFunction.get_name(cond.problem_id)
            p_class = BBOBFunction.get_class(cond.problem_id)
            for s in solvers_list:
                if s not in solvers:
                    continue
                runs = solvers[s]
                succ = self.compute_success_rate(runs, threshold=threshold)
                prob_records.append({
                    "Problem": p_name,
                    "Class": p_class,
                    "Solver": s,
                    "Success Rate": succ,
                })

        if not prob_records:
            return pd.DataFrame()

        df = pd.DataFrame(prob_records)
        return cast(
            pd.DataFrame,
            df.groupby(["Class", "Solver"], as_index=False)[["Success Rate"]].mean(),
        )

    def compute_validation_medians(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
    ) -> tuple[list[float], list[float], list[str]]:
        """Compute median terminal error across all solvers for Clean vs. Noisy validation."""
        clean_medians: list[float] = []
        noisy_medians: list[float] = []
        problem_labels: list[str] = []

        for p_id in problem_ids:
            p_name = BBOBFunction.get_name(p_id)
            p_class = BBOBFunction.get_class(p_id)
            problem_labels.append(f"<b>{p_name}</b><br><sup>{p_class}</sup>")

            c_key = EvaluationCondition(dim=dim, noise_std=clean_std, problem_id=p_id)
            c_finals = []
            if c_key in benchmark_data:
                for s, runs in benchmark_data[c_key].items():
                    for run in runs:
                        if not np.isnan(run.final_value):
                            c_finals.append(run.final_value)
            clean_medians.append(float(np.median(c_finals)) if c_finals else 1e-16)

            n_key = EvaluationCondition(dim=dim, noise_std=noisy_std, problem_id=p_id)
            n_finals = []
            if n_key in benchmark_data:
                for s, runs in benchmark_data[n_key].items():
                    for run in runs:
                        if not np.isnan(run.final_value):
                            n_finals.append(run.final_value)
            noisy_medians.append(float(np.median(n_finals)) if n_finals else 1e-16)

        return clean_medians, noisy_medians, problem_labels

    def compute_robustness_profile(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers_order: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[list[str], list[float], list[float], list[float]]:
        """Compute clean vs. noisy success rates and delta robustness drops across solvers."""
        clean_rates = []
        noisy_rates = []
        valid_solvers = []
        deltas = []

        for s in solvers_order:
            c_succ, c_tot = 0, 0
            n_succ, n_tot = 0, 0
            for p_id in problem_ids:
                c_key = EvaluationCondition(dim=dim, noise_std=clean_std, problem_id=p_id)
                if c_key in benchmark_data and s in benchmark_data[c_key]:
                    runs = benchmark_data[c_key][s]
                    for r in runs:
                        c_tot += 1
                        if r.is_success(threshold):
                            c_succ += 1

                n_key = EvaluationCondition(dim=dim, noise_std=noisy_std, problem_id=p_id)
                if n_key in benchmark_data and s in benchmark_data[n_key]:
                    runs = benchmark_data[n_key][s]
                    for r in runs:
                        n_tot += 1
                        if r.is_success(threshold):
                            n_succ += 1

            if c_tot > 0 and n_tot > 0:
                c_r = c_succ / c_tot
                n_r = n_succ / n_tot
                clean_rates.append(c_r)
                noisy_rates.append(n_r)
                deltas.append(c_r - n_r)
                valid_solvers.append(s)

        return valid_solvers, clean_rates, noisy_rates, deltas

    def compute_multi_noise_summary(
        self,
        benchmark_data: EvaluationDataset,
        solvers: list[str] | None = None,
        dims: list[int] | None = None,
        noise_stds: list[float] | None = None,
        problem_ids: list[int] | None = None,
        threshold: float = 1e-8,
    ) -> pd.DataFrame:
        """Compute comprehensive performance degradation and robustness drop across arbitrary noise levels.

        For each combination of (Solver, Dim, Noise Std), computes:
        - Success Rate (fraction of runs reaching delta_y <= threshold)
        - Median Terminal Error
        - Mean Log10 Terminal Error
        - Absolute Fragility Drop (Clean Success Rate - Noisy Success Rate)
        - Relative Fragility Drop Percentage ((Clean - Noisy) / Clean * 100)

        Returns:
            pd.DataFrame with columns:
            ['Solver', 'Dim', 'Noise Std', 'Total Runs', 'Successes', 'Success Rate',
             'Median Error', 'Mean Log Error', 'Clean Success Rate', 'Fragility Drop', 'Relative Drop Pct']
        """
        target_dims = dims if dims is not None else benchmark_data.dims
        target_solvers = solvers if solvers is not None else benchmark_data.solvers
        target_noises = sorted(noise_stds if noise_stds is not None else benchmark_data.noise_stds)
        target_problems = problem_ids if problem_ids is not None else benchmark_data.problem_ids
        clean_noise = (
            0.0
            if 0.0 in target_noises
            else (0.0 if 0.0 in benchmark_data.noise_stds else (target_noises[0] if target_noises else 0.0))
        )

        records: list[dict[str, Any]] = []
        for dim in target_dims:
            clean_success_rates: dict[str, float] = {}
            for s in target_solvers:
                c_succ, c_tot = 0, 0
                for p_id in target_problems:
                    c_key = EvaluationCondition(dim=dim, noise_std=clean_noise, problem_id=p_id)
                    for r in benchmark_data.get(c_key, {}).get(s, []):
                        c_tot += 1
                        if r.is_success(threshold):
                            c_succ += 1
                clean_success_rates[s] = (c_succ / c_tot) if c_tot > 0 else 0.0

            for n_std in target_noises:
                for s in target_solvers:
                    tot_runs = 0
                    succ_runs = 0
                    final_values: list[float] = []

                    for p_id in target_problems:
                        cond = EvaluationCondition(dim=dim, noise_std=n_std, problem_id=p_id)
                        for r in benchmark_data.get(cond, {}).get(s, []):
                            tot_runs += 1
                            if r.is_success(threshold):
                                succ_runs += 1
                            if not np.isnan(r.best_value):
                                final_values.append(r.best_value)

                    if tot_runs == 0:
                        continue

                    succ_rate = succ_runs / tot_runs
                    med_err = float(np.median(final_values)) if final_values else 1e-16
                    clamped_errs = np.clip(np.array(final_values) if final_values else np.array([1e-16]), 1e-16, None)
                    mean_log_err = float(np.mean(np.log10(clamped_errs)))
                    clean_rate = clean_success_rates.get(s, succ_rate)
                    frag_drop = clean_rate - succ_rate
                    rel_drop = (
                        (frag_drop / clean_rate * 100.0)
                        if clean_rate > 0
                        else (0.0 if succ_rate == 0 else -100.0)
                    )

                    records.append({
                        "Solver": s,
                        "Dim": dim,
                        "Noise Std": n_std,
                        "Total Runs": tot_runs,
                        "Successes": succ_runs,
                        "Success Rate": succ_rate,
                        "Median Error": med_err,
                        "Mean Log Error": mean_log_err,
                        "Clean Success Rate": clean_rate,
                        "Fragility Drop": frag_drop,
                        "Relative Drop Pct": rel_drop,
                    })

        cols = [
            "Solver", "Dim", "Noise Std", "Total Runs", "Successes", "Success Rate",
            "Median Error", "Mean Log Error", "Clean Success Rate", "Fragility Drop", "Relative Drop Pct"
        ]
        if not records:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame(records)

    def compute_scaffolding_ablation(
        self,
        benchmark_data: EvaluationDataset,
        dim: int,
        solvers_list: list[str],
        problem_ids: list[int],
        clean_std: float = 0.0,
        noisy_std: float = 0.05,
        threshold: float = 1e-8,
    ) -> tuple[list[str], list[float], list[float]]:
        """Compute prompt scaffolding ablation success rates for a model family."""
        strategies = [s.split(" / ")[1] if " / " in s else s for s in solvers_list]
        strat_labels = [f"<b>{s.title()}</b>" for s in strategies]
        clean_succ_rates = []
        noisy_succ_rates = []

        for s_name in solvers_list:
            c_succ, c_tot = 0, 0
            n_succ, n_tot = 0, 0
            for p_id in problem_ids:
                c_key = EvaluationCondition(dim=dim, noise_std=clean_std, problem_id=p_id)
                if c_key in benchmark_data and s_name in benchmark_data[c_key]:
                    for r in benchmark_data[c_key][s_name]:
                        c_tot += 1
                        if r.is_success(threshold):
                            c_succ += 1

                n_key = EvaluationCondition(dim=dim, noise_std=noisy_std, problem_id=p_id)
                if n_key in benchmark_data and s_name in benchmark_data[n_key]:
                    for r in benchmark_data[n_key][s_name]:
                        n_tot += 1
                        if r.is_success(threshold):
                            n_succ += 1

            clean_succ_rates.append(c_succ / max(1, c_tot))
            noisy_succ_rates.append(n_succ / max(1, n_tot))

        return strat_labels, clean_succ_rates, noisy_succ_rates

    def compute_convergence_tiers(
        self,
        benchmark_data: EvaluationDataset,
        dims: list[int] | None = None,
        solvers: list[str] | None = None,
        noise_stds: list[float] | None = None,
        problem_ids: list[int] | None = None,
    ) -> pd.DataFrame:
        """Classify each execution run into 4 rigorous convergence tiers based on terminal error.

        Tiers:
        - High Precision (Solved): best_value <= 1e-8 (global optimum basin reached)
        - Moderate Convergence: 1e-8 < best_value <= 1e-2 (strong local convergence)
        - Minor Progress: 1e-2 < best_value <= 1.0 (partial descent)
        - Severe Stagnation / Failure: best_value > 1.0 (premature stagnation or divergence)

        Returns:
            DataFrame containing individual run records with classified convergence tiers.
        """
        records: list[dict[str, Any]] = []

        for cond, s_dict in benchmark_data.items():
            if dims is not None and cond.dim not in dims:
                continue
            if noise_stds is not None and not any(np.isclose(cond.noise_std, n) for n in noise_stds):
                continue
            if problem_ids is not None and cond.problem_id not in problem_ids:
                continue

            for s_name, runs in s_dict.items():
                if solvers is not None and s_name not in solvers:
                    continue

                for r in runs:
                    if len(r.raw_objectives) == 0:
                        continue
                    err = r.best_value
                    if np.isnan(err):
                        tier = "Severe Stagnation / Failure (Δy > 1.0)"
                        tier_code = "severe_stagnation"
                    elif err <= 1e-8:
                        tier = "High Precision (Δy ≤ 10⁻⁸)"
                        tier_code = "high_precision"
                    elif err <= 1e-2:
                        tier = "Moderate Convergence (10⁻⁸ < Δy ≤ 10⁻²)"
                        tier_code = "moderate_convergence"
                    elif err <= 1.0:
                        tier = "Minor Progress (10⁻² < Δy ≤ 1.0)"
                        tier_code = "minor_progress"
                    else:
                        tier = "Severe Stagnation / Failure (Δy > 1.0)"
                        tier_code = "severe_stagnation"

                    records.append({
                        "Solver": s_name,
                        "Dim": cond.dim,
                        "Noise Std": cond.noise_std,
                        "Problem ID": cond.problem_id,
                        "Best Error": err,
                        "Tier": tier,
                        "Tier Code": tier_code,
                    })

        if not records:
            return pd.DataFrame(columns=["Solver", "Dim", "Noise Std", "Problem ID", "Best Error", "Tier", "Tier Code"])

        return pd.DataFrame(records)

