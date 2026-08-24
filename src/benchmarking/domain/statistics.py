"""Pure computational mathematics engine for statistical testing, effect sizes, and convergence analysis."""

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu, pearsonr
from statsmodels.stats.multitest import multipletests

from benchmarking.domain.taxonomy import BBOB_CLASSES, BBOB_NAMES


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
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
    ) -> pd.DataFrame:
        """Execute omnibus Kruskal-Wallis H-tests across all solvers per problem condition."""
        master_omnibus: list[dict[str, Any]] = []

        for (dim, noise_std, p_id), s_dict in benchmark_data.items():
            p_name = BBOB_NAMES.get(p_id, f"f{p_id}")
            p_class = BBOB_CLASSES.get(p_id, "Unknown")
            residuals = {
                s: [r[1][-1] for r in runs if len(r[1]) > 0]
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
                    "Dim": dim,
                    "Noise Std": noise_std,
                    "Problem ID": p_id,
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
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        alpha: float = 0.05,
    ) -> pd.DataFrame:
        """Execute pairwise Mann-Whitney U tests with Benjamini-Hochberg FDR correction."""
        master_pairwise: list[dict[str, Any]] = []

        for (dim, noise_std, p_id), s_dict in benchmark_data.items():
            solvers = sorted(s_dict.keys())
            residuals = {
                s: [r[1][-1] for r in runs if len(r[1]) > 0]
                for s, runs in s_dict.items()
            }

            p_name = BBOB_NAMES.get(p_id, f"f{p_id}")
            p_class = BBOB_CLASSES.get(p_id, "Unknown")

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
                            "Dim": dim,
                            "Noise Std": noise_std,
                            "Problem ID": p_id,
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
        runs: list[tuple[np.ndarray, np.ndarray]],
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

        for evals, raw_vals in runs:
            if len(evals) == 0:
                continue
            cum_best = np.minimum.accumulate(raw_vals)
            y_interp = np.interp(
                eval_grid,
                evals,
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
        runs: list[tuple[np.ndarray, np.ndarray]],
        threshold: float = 1e-8,
    ) -> float:
        """Compute empirical success rate (fraction of runs reaching delta_y <= threshold)."""
        if not runs:
            return 0.0
        successes = sum(
            1 for _, raw_vals in runs if len(raw_vals) > 0 and np.min(raw_vals) <= threshold
        )
        return successes / len(runs)

    def compute_fragility_matrix(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
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
            p_name = BBOB_NAMES.get(p_id, f"f{p_id}")
            p_class = BBOB_CLASSES.get(p_id, "")
            problem_labels.append(f"<b>{p_name}</b><br><sup>{p_class}</sup>")

            c_key = (dim, clean_std, p_id)
            n_key = (dim, noisy_std, p_id)

            for c_idx, solver in enumerate(solvers):
                c_runs = benchmark_data.get(c_key, {}).get(solver, [])
                n_runs = benchmark_data.get(n_key, {}).get(solver, [])
                c_succ = self.compute_success_rate(c_runs, threshold=threshold)
                n_succ = self.compute_success_rate(n_runs, threshold=threshold)
                matrix[r_idx, c_idx] = c_succ - n_succ

        return matrix, problem_labels

    def compute_hardness_success_rates(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
        dim: int,
        solvers_list: list[str],
        noise_level: float,
        threshold: float = 1e-8,
    ) -> pd.DataFrame:
        """Aggregate solver success rates grouped by BBOB landscape hardness class."""
        prob_records = []
        for (d, n_std, p_id), solvers in benchmark_data.items():
            if d != dim or not np.isclose(n_std, noise_level):
                continue
            p_name = BBOB_NAMES.get(p_id, f"f{p_id}")
            p_class = BBOB_CLASSES.get(p_id, "Unknown")
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
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
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
            p_name = BBOB_NAMES.get(p_id, f"f{p_id}")
            p_class = BBOB_CLASSES.get(p_id, "")
            problem_labels.append(f"<b>{p_name}</b><br><sup>{p_class}</sup>")

            c_key = (dim, clean_std, p_id)
            c_finals = []
            if c_key in benchmark_data:
                for s, runs in benchmark_data[c_key].items():
                    for evals, raw_vals in runs:
                        if len(raw_vals) > 0:
                            c_finals.append(raw_vals[-1])
            clean_medians.append(float(np.median(c_finals)) if c_finals else 1e-16)

            n_key = (dim, noisy_std, p_id)
            n_finals = []
            if n_key in benchmark_data:
                for s, runs in benchmark_data[n_key].items():
                    for evals, raw_vals in runs:
                        if len(raw_vals) > 0:
                            n_finals.append(raw_vals[-1])
            noisy_medians.append(float(np.median(n_finals)) if n_finals else 1e-16)

        return clean_medians, noisy_medians, problem_labels

    def compute_trajectory_and_ecdf(
        self,
        runs: list[tuple[np.ndarray, np.ndarray]],
        eval_grid: np.ndarray,
        targets: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute convergence trajectory (median, Q25, Q75) and ECDF empirical curve."""
        if not runs:
            nan_arr = np.full(len(eval_grid), np.nan)
            return nan_arr, nan_arr, nan_arr, np.zeros(len(targets))

        interp_matrix = []
        min_vals = []
        for evals, raw_vals in runs:
            if len(evals) == 0:
                continue
            cum_best = np.minimum.accumulate(raw_vals)
            y_interp = np.interp(
                eval_grid,
                evals,
                cum_best,
                left=cum_best[0],
                right=cum_best[-1],
            )
            interp_matrix.append(y_interp)
            min_vals.append(cum_best[-1])

        if not interp_matrix:
            nan_arr = np.full(len(eval_grid), np.nan)
            return nan_arr, nan_arr, nan_arr, np.zeros(len(targets))

        arr = np.array(interp_matrix)
        med = np.median(arr, axis=0)
        q25 = np.percentile(arr, 25, axis=0)
        q75 = np.percentile(arr, 75, axis=0)

        min_arr = np.array(min_vals)
        ecdf_curve = np.array([np.mean(min_arr <= t) for t in targets])
        return med, q25, q75, ecdf_curve

    def compute_robustness_profile(
        self,
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
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
                c_key = (dim, clean_std, p_id)
                if c_key in benchmark_data and s in benchmark_data[c_key]:
                    runs = benchmark_data[c_key][s]
                    for _, raw_vals in runs:
                        c_tot += 1
                        if len(raw_vals) > 0 and np.min(raw_vals) <= threshold:
                            c_succ += 1

                n_key = (dim, noisy_std, p_id)
                if n_key in benchmark_data and s in benchmark_data[n_key]:
                    runs = benchmark_data[n_key][s]
                    for _, raw_vals in runs:
                        n_tot += 1
                        if len(raw_vals) > 0 and np.min(raw_vals) <= threshold:
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
        benchmark_data: dict[tuple[int, float, int], dict[str, list[tuple[np.ndarray, np.ndarray]]]],
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
                c_key = (dim, clean_std, p_id)
                if c_key in benchmark_data and s_name in benchmark_data[c_key]:
                    for _, raw_vals in benchmark_data[c_key][s_name]:
                        c_tot += 1
                        if len(raw_vals) > 0 and np.min(raw_vals) <= threshold:
                            c_succ += 1

                n_key = (dim, noisy_std, p_id)
                if n_key in benchmark_data and s_name in benchmark_data[n_key]:
                    for _, raw_vals in benchmark_data[n_key][s_name]:
                        n_tot += 1
                        if len(raw_vals) > 0 and np.min(raw_vals) <= threshold:
                            n_succ += 1

            clean_succ_rates.append(c_succ / max(1, c_tot))
            noisy_succ_rates.append(n_succ / max(1, n_tot))

        return strat_labels, clean_succ_rates, noisy_succ_rates
