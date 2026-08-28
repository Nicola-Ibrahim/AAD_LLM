"""Pure computational mathematics engine for statistical testing, effect sizes, and convergence analysis."""

from collections.abc import Mapping, Sequence
from typing import Any, Literal

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu, pearsonr
from statsmodels.stats.multitest import multipletests

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace


class StatisticalEngine:
    """Pure computational mathematics engine for hypothesis testing, effect sizes, and convergence analysis."""

    @staticmethod
    def vargha_delaney_a12(sample1: Sequence[float], sample2: Sequence[float]) -> tuple[float, str]:
        """Compute the Vargha-Delaney A12 non-parametric effect size.

        A12 > 0.5 indicates sample1 stochastic dominance (or higher values).
        Magnitude is categorized as 'negligible', 'small', 'medium', or 'large'.
        """
        m, n = len(sample1), len(sample2)
        if m == 0 or n == 0:
            return 0.5, "negligible"

        s1 = np.asarray(sample1, dtype=float)
        s2 = np.asarray(sample2, dtype=float)

        r1 = np.sum([np.sum(x < s2) + 0.5 * np.sum(x == s2) for x in s1])
        a12 = float(r1 / (m * n))
        d = abs(a12 - 0.5)
        mag = (
            "negligible"
            if d < 0.06
            else ("small" if d < 0.14 else ("medium" if d < 0.21 else "large"))
        )
        return a12, mag

    def run_omnibus_kruskal(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
    ) -> pd.DataFrame:
        """Execute omnibus Kruskal-Wallis H-tests across all solvers per problem condition."""
        master_omnibus: list[dict[str, Any]] = []

        for cond, s_dict in benchmark_data.items():
            p_name = BBOBFunction.get_name(cond.problem_id)
            p_class = BBOBFunction.get_class(cond.problem_id)
            residuals = {
                s: [r.final_value for r in runs if not np.isnan(r.final_value)]
                for s, runs in s_dict.items()
            }
            valid_solvers = [s for s, vals in residuals.items() if len(vals) >= 2]

            if len(valid_solvers) >= 2:
                all_vals = np.concatenate([residuals[s] for s in valid_solvers])
                if np.all(all_vals == all_vals[0]):
                    stat, p_val, sig_badge = 0.0, 1.0, "Identical"
                else:
                    try:
                        stat, p_val = kruskal(*[residuals[s] for s in valid_solvers])
                        if np.isinf(stat) or np.isnan(stat):
                            stat, p_val, sig_badge = 0.0, 1.0, "Identical"
                        else:
                            sig_badge = "Yes" if p_val < 0.05 else "No"
                    except Exception:
                        stat, p_val, sig_badge = np.nan, np.nan, "Error"

                master_omnibus.append({
                    "Dim": cond.dim,
                    "Noise Std": cond.noise_std,
                    "Problem ID": cond.problem_id,
                    "Problem Name": p_name,
                    "Function Class": p_class,
                    "H-Statistic": stat,
                    "p-value": p_val,
                    "Significant": sig_badge,
                    "Solvers Count": len(valid_solvers),
                })

        return pd.DataFrame(master_omnibus)

    def run_pairwise_fdr(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
        alpha: float = 0.05,
    ) -> pd.DataFrame:
        """Execute pairwise Mann-Whitney U tests with Benjamini-Hochberg FDR correction."""
        master_pairwise: list[dict[str, Any]] = []

        for cond, s_dict in benchmark_data.items():
            solvers = sorted(s_dict.keys())
            residuals = {
                s: [r.final_value for r in runs if not np.isnan(r.final_value)]
                for s, runs in s_dict.items()
            }

            p_name = BBOBFunction.get_name(cond.problem_id)
            p_class = BBOBFunction.get_class(cond.problem_id)

            for i in range(len(solvers)):
                for j in range(i + 1, len(solvers)):
                    s1 = solvers[i]
                    s2 = solvers[j]
                    v1 = residuals[s1]
                    v2 = residuals[s2]

                    if len(v1) >= 2 and len(v2) >= 2:
                        med1 = float(np.median(v1))
                        med2 = float(np.median(v2))
                        a12, mag = self.vargha_delaney_a12(v1, v2)

                        if np.array_equal(v1, v2):
                            u_stat, p_val = 0.5 * len(v1) * len(v2), 1.0
                        else:
                            try:
                                u_stat, p_val = mannwhitneyu(v1, v2, alternative="two-sided")
                            except Exception:
                                u_stat, p_val = np.nan, np.nan

                        def get_tier(a: str, b: str) -> str:
                            is_a = "llamea" in a.lower()
                            is_b = "llamea" in b.lower()
                            if (is_a and not is_b) or (is_b and not is_a):
                                return "Tier 2 (LLaMEA vs. Classical)"
                            elif is_a and is_b:
                                return "Tier 1 (LLaMEA Intra-Model / Strategies)"
                            return "Tier 3 (Classical vs. Classical)"

                        master_pairwise.append({
                            "Dim": cond.dim,
                            "Noise Std": cond.noise_std,
                            "Problem ID": cond.problem_id,
                            "Problem Name": p_name,
                            "Function Class": p_class,
                            "Solver 1": s1,
                            "Solver 2": s2,
                            "Median 1": med1,
                            "Median 2": med2,
                            "Solver 1 Med": med1,
                            "Solver 2 Med": med2,
                            "U-Stat": u_stat,
                            "p-value": p_val,
                            "A12": a12,
                            "A12 Magnitude": mag,
                            "Comparison Tier": get_tier(s1, s2),
                        })

        df_pairwise = pd.DataFrame(master_pairwise)
        if df_pairwise.empty:
            return df_pairwise

        # Apply Benjamini-Hochberg FDR correction
        valid_mask = df_pairwise["p-value"].notnull()
        p_vals = df_pairwise.loc[valid_mask, "p-value"].values
        if len(p_vals) > 0:
            reject, pvals_corr, _, _ = multipletests(p_vals, alpha=alpha, method="fdr_bh")
            df_pairwise["p-adjusted"] = np.nan
            df_pairwise["Significant (FDR)"] = False
            df_pairwise.loc[valid_mask, "p-adjusted"] = pvals_corr
            df_pairwise.loc[valid_mask, "Significant (FDR)"] = reject
        else:
            df_pairwise["p-adjusted"] = np.nan
            df_pairwise["Significant (FDR)"] = False

        # Aliases for notebook compatibility
        df_pairwise["p-value-adj"] = df_pairwise["p-adjusted"]
        df_pairwise["FDR_Sig"] = df_pairwise["Significant (FDR)"]

        def get_outcome(row: pd.Series) -> str:
            if not row["Significant (FDR)"]:
                return "Tie"
            if row["Median 1"] < row["Median 2"]:
                return f"{row['Solver 1']} Wins"
            elif row["Median 2"] < row["Median 1"]:
                return f"{row['Solver 2']} Wins"
            return "Tie"

        df_pairwise["Outcome"] = df_pairwise.apply(get_outcome, axis=1)
        return df_pairwise

    def compute_convergence_iqr(
        self,
        runs: Sequence[RunTrace],
        max_evals: int = 1000000,
        n_points: int = 500,
        grid_points: int | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Interpolate irregular run traces onto a uniform log/linear grid and compute Median, Q25, Q75."""
        if grid_points is not None:
            n_points = grid_points
        if not runs:
            grid = np.linspace(1, max_evals, n_points)
            nan_arr = np.full(n_points, np.nan)
            return grid, nan_arr, nan_arr, nan_arr

        eval_grid = np.logspace(0, np.log10(max_evals), n_points)
        interpolated = []

        for run in runs:
            if len(run.evaluations) == 0:
                continue
            cum_best = np.minimum.accumulate(run.raw_objectives)
            y_interp = np.interp(
                eval_grid,
                run.evaluations,
                cum_best,
                left=cum_best[0],
                right=cum_best[-1],
            )
            interpolated.append(y_interp)

        if not interpolated:
            grid = np.linspace(1, max_evals, n_points)
            nan_arr = np.full(n_points, np.nan)
            return grid, nan_arr, nan_arr, nan_arr

        arr = np.array(interpolated)
        medians = np.median(arr, axis=0)
        q25 = np.percentile(arr, 25, axis=0)
        q75 = np.percentile(arr, 75, axis=0)
        return eval_grid, medians, q25, q75

    @staticmethod
    def compute_synthesis_transfer_correlation(df_exp: pd.DataFrame) -> tuple[float, float]:
        """Compute Pearson correlation between synthesis final error and validation performance."""
        if df_exp.empty or "final_error" not in df_exp.columns:
            return 0.0, 1.0
        valid = df_exp.dropna(subset=["final_error"])
        if len(valid) < 3:
            return 0.0, 1.0
        y = valid["final_error"].values
        x = valid["best_fitness"].values if "best_fitness" in valid.columns else y
        r_val, p_val = pearsonr(x, y)
        return float(r_val), float(p_val)

    @staticmethod
    def compute_success_rate(
        runs: Sequence[RunTrace],
        threshold: float = 1e-8,
    ) -> float:
        """Compute empirical success rate (fraction of runs reaching delta_y <= threshold)."""
        if not runs:
            return 0.0
        successes = sum(1 for r in runs if r.is_success(threshold))
        return successes / len(runs)

    def compute_fragility_matrix(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
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
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
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
        return df.groupby(["Class", "Solver"])["Success Rate"].mean().reset_index()

    def compute_validation_medians(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
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

    def compute_trajectory_and_ecdf(
        self,
        runs: Sequence[RunTrace],
        eval_grid: np.ndarray,
        targets: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute convergence trajectory (median, Q25, Q75) and BBOB Empirical Runtime ECDF curve."""
        if not runs:
            nan_arr = np.full(len(eval_grid), np.nan)
            return nan_arr, nan_arr, nan_arr, np.zeros(len(eval_grid))

        interp_matrix = []
        for run in runs:
            if len(run.evaluations) == 0:
                continue
            cum_best = np.minimum.accumulate(run.raw_objectives)
            y_interp = np.interp(
                eval_grid,
                run.evaluations,
                cum_best,
                left=cum_best[0],
                right=cum_best[-1],
            )
            interp_matrix.append(y_interp)

        if not interp_matrix:
            nan_arr = np.full(len(eval_grid), np.nan)
            return nan_arr, nan_arr, nan_arr, np.zeros(len(eval_grid))

        arr = np.array(interp_matrix)
        med = np.median(arr, axis=0)
        q25 = np.percentile(arr, 25, axis=0)
        q75 = np.percentile(arr, 75, axis=0)

        # Standard BBOB/COCO Runtime ECDF:
        # Proportion of (run, target) pairs solved at or before each evaluation step
        ecdf_curve = np.mean(arr[:, :, None] <= targets[None, None, :], axis=(0, 2))
        return med, q25, q75, ecdf_curve

    def compute_robustness_profile(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
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

    def compute_scaffolding_ablation(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
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

    def compute_auc_ecdf_ranking(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
        solvers: list[str],
        eval_grid: np.ndarray,
        targets: np.ndarray,
    ) -> pd.DataFrame:
        """Compute Area Under the Runtime ECDF Curve (AUC-ECDF) for each solver across all conditions.

        AUC is integrated over log10(evaluations) using trapezoidal integration and normalized to [0, 1].
        """
        log_x = np.log10(eval_grid)
        x_range = float(log_x[-1] - log_x[0])

        solver_aucs = {s: [] for s in solvers}
        for cond, s_dict in benchmark_data.items():
            for s in solvers:
                runs = s_dict.get(s, [])
                if runs:
                    _, _, _, ecdf = self.compute_trajectory_and_ecdf(runs, eval_grid, targets)
                    auc = float(np.trapezoid(ecdf, log_x) / x_range)
                    solver_aucs[s].append(auc)

        records = []
        for s in solvers:
            aucs = solver_aucs[s]
            mean_auc = float(np.mean(aucs)) if aucs else 0.0
            records.append({
                "Solver": s,
                "AUC-ECDF": mean_auc,
                "Type": "Classical Baseline" if " / " not in s else "LLaMEA Evolved",
            })

        df_auc = pd.DataFrame(records).sort_values(by="AUC-ECDF", ascending=True)
        return df_auc

    def compute_auc_ecdf_matrix(
        self,
        benchmark_data: EvaluationDataset | Mapping[EvaluationCondition, dict[str, list[RunTrace]]],
        solvers: list[str],
        eval_grid: np.ndarray,
        targets: np.ndarray,
        group_by: Literal["dim", "problem_id", "noise_std", "dim_noise", "problem_noise", "condition"] = "dim",
    ) -> pd.DataFrame:
        """Compute Area Under the Runtime ECDF (AUC-ECDF) matrix disaggregated by grouping axis.

        Returns a long-format DataFrame with percentage AUC values scaled to [0, 100].
        """
        log_x = np.log10(eval_grid)
        x_range = float(log_x[-1] - log_x[0])

        rows = []
        for cond, s_dict in benchmark_data.items():
            for s in solvers:
                runs = s_dict.get(s, [])
                if runs:
                    _, _, _, ecdf = self.compute_trajectory_and_ecdf(runs, eval_grid, targets)
                    auc_raw = float(np.trapezoid(ecdf, log_x) / x_range)
                    auc_pct = auc_raw * 100.0
                    rows.append({
                        "Solver": s,
                        "Dim": cond.dim,
                        "Noise Std": cond.noise_std,
                        "Problem ID": cond.problem_id,
                        "AUC-ECDF (%)": auc_pct,
                        "AUC-ECDF": auc_raw,
                        "Type": "Classical Baseline" if " / " not in s else "LLaMEA Evolved",
                    })

        df_raw = pd.DataFrame(rows)
        if df_raw.empty:
            return pd.DataFrame(columns=["Solver", "GroupKey", "AUC-ECDF (%)", "Type"])

        if group_by == "dim":
            df_grp = df_raw.groupby(["Solver", "Dim", "Type"], as_index=False)["AUC-ECDF (%)"].mean()
            df_grp["GroupKey"] = df_grp["Dim"].astype(str) + "D"
            return df_grp
        elif group_by == "noise_std":
            df_grp = df_raw.groupby(["Solver", "Noise Std", "Type"], as_index=False)["AUC-ECDF (%)"].mean()
            df_grp["GroupKey"] = df_grp["Noise Std"].apply(lambda n: "Clean (σ=0.0)" if n == 0.0 else f"Noisy (σ={n})")
            return df_grp
        elif group_by == "problem_id":
            df_grp = df_raw.groupby(["Solver", "Problem ID", "Type"], as_index=False)["AUC-ECDF (%)"].mean()
            df_grp["GroupKey"] = df_grp["Problem ID"].apply(BBOBFunction.get_name)
            return df_grp
        elif group_by == "dim_noise":
            df_grp = df_raw.groupby(["Solver", "Dim", "Noise Std", "Type"], as_index=False)["AUC-ECDF (%)"].mean()
            return df_grp
        elif group_by == "problem_noise":
            df_grp = df_raw.groupby(["Solver", "Problem ID", "Noise Std", "Type"], as_index=False)["AUC-ECDF (%)"].mean()
            return df_grp
        elif group_by == "condition":
            return df_raw
        else:
            raise ValueError(f"Unknown group_by: {group_by}")

