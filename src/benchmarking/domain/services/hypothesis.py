"""Inferential statistical hypothesis testing, effect size estimation, and correlation analysis."""

from typing import Any, cast

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu, pearsonr
from statsmodels.stats.multitest import multipletests

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.vos import EvaluationDataset


class HypothesisTestingEngine:
    """Computational engine for non-parametric hypothesis testing and effect size estimation."""

    @staticmethod
    def vargha_delaney_a12(sample1: np.ndarray, sample2: np.ndarray) -> tuple[float, str]:
        """Compute the Vargha-Delaney A12 non-parametric effect size.

        A12 > 0.5 indicates sample1 stochastic dominance (or higher values).
        Magnitude is categorized as 'negligible', 'small', 'medium', or 'large'.
        """
        s1 = np.asarray(sample1, dtype=float)
        s2 = np.asarray(sample2, dtype=float)
        m, n = len(s1), len(s2)
        if m == 0 or n == 0:
            return 0.5, "negligible"

        r1 = np.sum(s1[:, None] < s2[None, :]) + 0.5 * np.sum(s1[:, None] == s2[None, :])
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
        benchmark_data: EvaluationDataset,
    ) -> pd.DataFrame:
        """Execute omnibus Kruskal-Wallis H-tests across all solvers per problem condition."""
        master_omnibus: list[dict[str, Any]] = []

        for cond, s_dict in benchmark_data.items():
            p_name = BBOBFunction.get_name(cond.problem_id)
            p_class = BBOBFunction.get_class(cond.problem_id)
            residuals = {
                s: np.array([r.final_value for r in runs if not np.isnan(r.final_value)], dtype=float)
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
        benchmark_data: EvaluationDataset,
        alpha: float = 0.05,
    ) -> pd.DataFrame:
        """Execute pairwise Mann-Whitney U tests with Benjamini-Hochberg FDR correction."""
        master_pairwise: list[dict[str, Any]] = []

        for cond, s_dict in benchmark_data.items():
            solvers = sorted(s_dict.keys())
            residuals = {
                s: np.array([r.final_value for r in runs if not np.isnan(r.final_value)], dtype=float)
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
            if not bool(row["Significant (FDR)"]):
                return "Tie"
            if row["Median 1"] < row["Median 2"]:
                return f"{row['Solver 1']} Wins"
            elif row["Median 2"] < row["Median 1"]:
                return f"{row['Solver 2']} Wins"
            return "Tie"

        df_pairwise["Outcome"] = df_pairwise.apply(get_outcome, axis=1)
        return df_pairwise

    @staticmethod
    def compute_pairwise_a12_matrix(
        df_pairwise: pd.DataFrame,
        solvers_order: list[str] | None = None,
    ) -> tuple[list[str], np.ndarray]:
        """Compute the pairwise Vargha-Delaney A12 matrix across all solvers.

        Args:
            df_pairwise: Pairwise DataFrame containing 'Solver 1', 'Solver 2', and 'A12'.
            solvers_order: Optional list of solver names to order rows and columns.

        Returns:
            Tuple of (solvers_list, a12_matrix_2d_ndarray).
        """
        if df_pairwise.empty:
            return [], np.empty((0, 0))

        all_solvers = set(df_pairwise["Solver 1"]).union(set(df_pairwise["Solver 2"]))
        if solvers_order is not None:
            solvers = [s for s in solvers_order if s in all_solvers]
            remaining = sorted(list(all_solvers - set(solvers)))
            solvers.extend(remaining)
        else:
            solvers = sorted(list(all_solvers))

        n = len(solvers)
        matrix = np.full((n, n), 0.5)

        for i, s1 in enumerate(solvers):
            for j, s2 in enumerate(solvers):
                if i == j:
                    continue
                sub_dir = df_pairwise[(df_pairwise["Solver 1"] == s1) & (df_pairwise["Solver 2"] == s2)]
                sub_rev = df_pairwise[(df_pairwise["Solver 1"] == s2) & (df_pairwise["Solver 2"] == s1)]
                vals: list[float] = []
                if not sub_dir.empty:
                    vals.extend(sub_dir["A12"].astype(float).tolist())
                if not sub_rev.empty:
                    vals.extend((1.0 - sub_rev["A12"].astype(float)).tolist())
                if vals:
                    matrix[i, j] = float(np.mean(vals))

        return solvers, matrix

    @staticmethod
    def compute_pairwise_win_counts(
        df_pairwise: pd.DataFrame,
        solvers_order: list[str] | None = None,
    ) -> pd.DataFrame:
        """Compute pairwise win, tie, and loss totals per solver from pairwise FDR results.

        Args:
            df_pairwise: Pairwise DataFrame containing 'Solver 1', 'Solver 2', and 'Outcome'.
            solvers_order: Optional list of solver names.

        Returns:
            DataFrame with columns ['Solver', 'FDR Wins', 'Losses', 'Ties'].
        """
        if df_pairwise.empty:
            return pd.DataFrame(columns=["Solver", "FDR Wins", "Losses", "Ties"])

        all_solvers = set(df_pairwise["Solver 1"]).union(set(df_pairwise["Solver 2"]))
        solvers = (
            [s for s in solvers_order if s in all_solvers]
            if solvers_order is not None
            else sorted(list(all_solvers))
        )

        rows: list[dict[str, Any]] = []
        for s in solvers:
            wins = int((df_pairwise["Outcome"] == f"{s} Wins").sum())
            losses = int(
                df_pairwise[
                    ((df_pairwise["Solver 1"] == s) | (df_pairwise["Solver 2"] == s))
                    & (df_pairwise["Outcome"] != "Tie")
                    & (df_pairwise["Outcome"] != f"{s} Wins")
                ].shape[0]
            )
            ties = int(
                df_pairwise[
                    ((df_pairwise["Solver 1"] == s) | (df_pairwise["Solver 2"] == s))
                    & (df_pairwise["Outcome"] == "Tie")
                ].shape[0]
            )
            rows.append({"Solver": s, "FDR Wins": wins, "Losses": losses, "Ties": ties})

        return pd.DataFrame(rows).sort_values(by="FDR Wins", ascending=True)

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
        res = pearsonr(x, y)
        return float(cast(Any, res[0])), float(cast(Any, res[1]))
