"""Empirical Runtime ECDF curves, AUC-ECDF rankings, and convergence trajectory analytics."""

from collections.abc import Callable
from typing import Literal, cast

import numpy as np
import pandas as pd

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.vos import EvaluationDataset, RunTrace

# ─── Declarative Dispatch Table for AUC-ECDF Grouping Strategies ──────────────
_AUC_GROUPING_DISPATCH: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "condition": lambda df: df,
    "dim": lambda df: (
        cast(
            pd.DataFrame,
            df.groupby(["Solver", "Dim", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
        ).assign(GroupKey=lambda d: d["Dim"].astype(str) + "D")
    ),
    "noise_std": lambda df: (
        cast(
            pd.DataFrame,
            df.groupby(["Solver", "Noise Std", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
        ).assign(
            GroupKey=lambda d: d["Noise Std"].apply(
                lambda n: "Clean (σ=0.0)" if n == 0.0 else f"Noisy (σ={n})"
            )
        )
    ),
    "problem_id": lambda df: (
        cast(
            pd.DataFrame,
            df.groupby(["Solver", "Problem ID", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
        ).assign(GroupKey=lambda d: d["Problem ID"].apply(BBOBFunction.get_name))
    ),
    "dim_noise": lambda df: cast(
        pd.DataFrame,
        df.groupby(["Solver", "Dim", "Noise Std", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
    ),
    "problem_noise": lambda df: cast(
        pd.DataFrame,
        df.groupby(["Solver", "Problem ID", "Noise Std", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
    ),
}


class EcdfConvergenceEngine:
    """Computational engine for ECDF convergence, trapezoidal AUC integration, and trajectory statistics."""

    def compute_convergence_iqr(
        self,
        runs: list[RunTrace],
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
            min_len = min(len(run.evaluations), len(run.raw_objectives))
            if min_len == 0:
                continue
            evals = run.evaluations[:min_len]
            raws = run.raw_objectives[:min_len]
            cum_best = np.minimum.accumulate(raws)
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

    def compute_trajectory_and_ecdf(
        self,
        runs: list[RunTrace],
        eval_grid: np.ndarray,
        targets: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute convergence trajectory (median, Q25, Q75) and BBOB Empirical Runtime ECDF curve."""
        if not runs:
            nan_arr = np.full(len(eval_grid), np.nan)
            return nan_arr, nan_arr, nan_arr, np.zeros(len(eval_grid))

        interp_matrix = []
        for run in runs:
            min_len = min(len(run.evaluations), len(run.raw_objectives))
            if min_len == 0:
                continue
            evals = run.evaluations[:min_len]
            raws = run.raw_objectives[:min_len]
            cum_best = np.minimum.accumulate(raws)
            y_interp = np.interp(
                eval_grid,
                evals,
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

    def compute_auc_ecdf_ranking(
        self,
        benchmark_data: EvaluationDataset,
        solvers: list[str],
        targets: np.ndarray | dict[float, np.ndarray],
        max_evals: int | None = 1_000_000,
        n_grid_points: int = 200,
    ) -> pd.DataFrame:
        """Compute Area Under the Runtime ECDF Curve (AUC-ECDF) for each solver across all conditions.

        AUC is integrated over log10(evaluations) using trapezoidal integration and normalized to [0, 1].
        Standardized to 10^6 max evaluations budget across all conditions.
        Targets can be a single np.ndarray or a dictionary mapping noise_std to target arrays.
        """
        solver_aucs = {s: [] for s in solvers}

        for cond, s_dict in benchmark_data.items():
            dim_budget = max_evals if max_evals is not None else cond.dim * 10000
            c_grid = np.logspace(0, np.log10(dim_budget), n_grid_points)
            log_x = np.log10(c_grid)
            x_range = float(log_x[-1] - log_x[0])

            if isinstance(targets, dict):
                c_targets = targets.get(cond.noise_std)
                if c_targets is None:
                    c_targets = next(
                        (t for k, t in targets.items() if np.isclose(k, cond.noise_std)),
                        next(iter(targets.values())),
                    )
            else:
                c_targets = targets

            for s in solvers:
                runs = s_dict.get(s, [])
                if runs:
                    _, _, _, ecdf = self.compute_trajectory_and_ecdf(runs, c_grid, c_targets)
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
        benchmark_data: EvaluationDataset,
        solvers: list[str],
        targets: np.ndarray | dict[float, np.ndarray],
        group_by: Literal["dim", "problem_id", "noise_std", "dim_noise", "problem_noise", "condition"] = "dim",
        max_evals: int | None = 1_000_000,
        n_grid_points: int = 200,
    ) -> pd.DataFrame:
        """Compute Area Under the Runtime ECDF (AUC-ECDF) matrix disaggregated by grouping axis.

        Returns a long-format DataFrame with percentage AUC values scaled to [0, 100].
        Standardized to 10^6 max evaluations budget across all conditions.
        Targets can be a single np.ndarray or a dictionary mapping noise_std to target arrays.
        """
        rows = []

        for cond, s_dict in benchmark_data.items():
            dim_budget = max_evals if max_evals is not None else cond.dim * 10000
            c_grid = np.logspace(0, np.log10(dim_budget), n_grid_points)
            log_x = np.log10(c_grid)
            x_range = float(log_x[-1] - log_x[0])

            if isinstance(targets, dict):
                c_targets = targets.get(cond.noise_std)
                if c_targets is None:
                    c_targets = next(
                        (t for k, t in targets.items() if np.isclose(k, cond.noise_std)),
                        next(iter(targets.values())),
                    )
            else:
                c_targets = targets

            for s in solvers:
                runs = s_dict.get(s, [])
                if runs:
                    _, _, _, ecdf = self.compute_trajectory_and_ecdf(runs, c_grid, c_targets)
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

        handler = _AUC_GROUPING_DISPATCH.get(group_by)
        if handler is None:
            raise ValueError(
                f"Unknown group_by: '{group_by}'. Valid options are: {list(_AUC_GROUPING_DISPATCH.keys())}"
            )

        return handler(df_raw)

    def compute_adaptive_targets(
        self,
        benchmark_data: EvaluationDataset,
        noise_std: float,
        n_targets: int = 51,
    ) -> np.ndarray:
        """Compute noise-aware adaptive logarithmic target thresholds spanning empirical error range."""
        if not benchmark_data:
            if noise_std <= 0.0:
                return np.logspace(-8, 2, n_targets)
            return np.logspace(-2, 3, n_targets)

        mins: list[float] = []
        maxs: list[float] = []
        for cond, s_dict in benchmark_data.items():
            if np.isclose(cond.noise_std, noise_std):
                for runs in s_dict.values():
                    for r in runs:
                        if len(r.raw_objectives) > 0:
                            fin = r.raw_objectives[np.isfinite(r.raw_objectives)]
                            pos = fin[fin > 0]
                            if len(pos) > 0:
                                mins.append(float(np.min(pos)))
                                maxs.append(float(pos[0]))

        if not mins or not maxs:
            if noise_std <= 0.0:
                return np.logspace(-8, 2, n_targets)
            return np.logspace(-2, 3, n_targets)

        if noise_std <= 0.0:
            t_min = max(float(np.min(mins)), 1e-8)
            t_max = min(max(float(np.median(maxs)), 1e2), 1e4)
        else:
            # In noisy regimes, precision floor reflects realistic solver resolution
            # Floor at 1e-3 / 1e-2 to ensure dense target coverage across active solver trajectories
            p5 = float(np.percentile(mins, 5))
            t_min = max(p5, 1e-3)
            t_max = min(max(float(np.median(maxs)), 1e2), 1e4)

        if t_min >= t_max:
            t_min, t_max = (1e-8, 1e2) if noise_std <= 0.0 else (1e-2, 1e3)

        return np.logspace(np.log10(t_min), np.log10(t_max), n_targets)
