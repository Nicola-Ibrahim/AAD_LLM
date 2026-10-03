"""ECDF, paired convergence summaries and condition-level AUC calculations."""

from collections.abc import Callable
from typing import Literal, cast

import numpy as np
import pandas as pd

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.vos import EvaluationDataset, RunTrace

# ─── Declarative Dispatch Table for AUC-ECDF Grouping Strategies ──────────────
_AUC_GROUPING_DISPATCH: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "condition": lambda df: df,
    "dim": lambda df: cast(
        pd.DataFrame,
        df.groupby(["Solver", "Dim", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
    ).assign(GroupKey=lambda d: d["Dim"].astype(str) + "D"),
    "noise_std": lambda df: cast(
        pd.DataFrame,
        df.groupby(["Solver", "Noise Std", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
    ).assign(
        GroupKey=lambda d: d["Noise Std"].apply(
            lambda n: "Clean (σ=0.0)" if n == 0.0 else f"Noisy (σ={n})"
        )
    ),
    "problem_id": lambda df: cast(
        pd.DataFrame,
        df.groupby(["Solver", "Problem ID", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
    ).assign(GroupKey=lambda d: d["Problem ID"].apply(BBOBFunction.get_name)),
    "dim_noise": lambda df: cast(
        pd.DataFrame,
        df.groupby(["Solver", "Dim", "Noise Std", "Type"], as_index=False)[["AUC-ECDF (%)"]].mean(),
    ),
    "problem_noise": lambda df: cast(
        pd.DataFrame,
        df.groupby(["Solver", "Problem ID", "Noise Std", "Type"], as_index=False)[
            ["AUC-ECDF (%)"]
        ].mean(),
    ),
}


class EcdfConvergenceEngine:
    """Computational engine for ECDF convergence, trapezoidal AUC integration, and trajectory statistics."""

    @staticmethod
    def _interpolate_runs(runs: list[RunTrace], eval_grid: np.ndarray) -> np.ndarray:
        """Interpolate each run's incumbent objective values to a shared evaluation grid."""
        interpolated: list[np.ndarray] = []
        for run in runs:
            if len(run.evaluations) == 0:
                interpolated.append(np.full(len(eval_grid), np.inf))
                continue
            incumbent = np.minimum.accumulate(run.raw_objectives)
            indices = np.searchsorted(run.evaluations, eval_grid, side="right") - 1
            values = incumbent[np.maximum(indices, 0)].copy()
            values[indices < 0] = np.inf
            interpolated.append(values)
        return np.asarray(interpolated)

    def compute_trajectory_and_ecdf(
        self,
        runs: list[RunTrace],
        eval_grid: np.ndarray,
        targets: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Compute convergence trajectory (median, Q25, Q75) and BBOB Empirical Runtime ECDF curve."""
        arr = self._interpolate_runs(runs, eval_grid)
        if arr.size == 0:
            nan_arr = np.full(len(eval_grid), np.nan)
            return nan_arr, nan_arr, nan_arr, np.zeros(len(eval_grid))
        med = np.median(arr, axis=0)
        q25 = np.percentile(arr, 25, axis=0)
        q75 = np.percentile(arr, 75, axis=0)

        # Standard BBOB/COCO Runtime ECDF:
        # Proportion of (run, target) pairs solved at or before each evaluation step
        ecdf_curve = self._ecdf_from_interpolated(arr, targets)
        return med, q25, q75, ecdf_curve

    @staticmethod
    def _ecdf_from_interpolated(values: np.ndarray, targets: np.ndarray) -> np.ndarray:
        """Fraction of run/target pairs attained at each evaluation checkpoint."""
        return np.mean(values[:, :, None] <= targets[None, None, :], axis=(0, 2))

    def compute_ecdf(
        self, runs: list[RunTrace], eval_grid: np.ndarray, targets: np.ndarray
    ) -> np.ndarray:
        """Calculate ECDF without unused median/IQR statistics for AUC analysis."""
        values = self._interpolate_runs(runs, eval_grid)
        if values.size == 0:
            return np.zeros(len(eval_grid))
        return self._ecdf_from_interpolated(values, targets)

    def compute_auc_ecdf_matrix(
        self,
        benchmark_data: EvaluationDataset,
        solvers: list[str],
        targets: np.ndarray | dict[float, np.ndarray],
        group_by: Literal[
            "dim", "problem_id", "noise_std", "dim_noise", "problem_noise", "condition"
        ] = "dim",
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
                    ecdf = self.compute_ecdf(runs, c_grid, c_targets)
                    auc_raw = float(np.trapezoid(ecdf, log_x) / x_range)
                    auc_pct = auc_raw * 100.0
                    rows.append(
                        {
                            "Solver": s,
                            "Dim": cond.dim,
                            "Noise Std": cond.noise_std,
                            "Problem ID": cond.problem_id,
                            "AUC-ECDF (%)": auc_pct,
                            "AUC-ECDF": auc_raw,
                            "Type": "Classical Baseline" if " / " not in s else "LLaMEA Evolved",
                        }
                    )

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
