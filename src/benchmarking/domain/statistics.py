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
