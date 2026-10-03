"""Exploratory AUC summaries and BBOB hardness success rates."""

from typing import cast

import numpy as np
import pandas as pd

from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.vos import EvaluationDataset, RunTrace


class PerformanceMetricsEngine:
    """Calculate performance summaries consumed by the current analysis use case."""

    @staticmethod
    def summarize_auc_results(
        table: pd.DataFrame,
        models: list[str],
        classical_solvers: list[str],
        dims: list[int],
        noise_levels: list[float],
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Preserve the exploratory arithmetic means used by model-scale profiles."""
        rankings = (
            table.groupby("Canonical Solver")["AUC-ECDF (%)"].mean().sort_values(ascending=False)
        )
        scale = []
        for noise in noise_levels:
            for model in models + classical_solvers:
                rows = table[
                    table["Solver"].str.startswith(f"{model} /")
                    if model in models
                    else table["Solver"] == model
                ]
                for dim in dims:
                    values = rows[(rows["Dim"] == dim) & (rows["Noise Std"] == noise)]
                    scale.append(
                        {
                            "Model": model,
                            "Dim": dim,
                            "Noise Std": noise,
                            "AUC-ECDF (%)": values["AUC-ECDF (%)"].mean()
                            if not values.empty
                            else np.nan,
                        }
                    )
        return pd.DataFrame(scale, columns=["Model", "Dim", "Noise Std", "AUC-ECDF (%)"]), rankings

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
                prob_records.append(
                    {
                        "Problem": p_name,
                        "Class": p_class,
                        "Solver": s,
                        "Success Rate": succ,
                    }
                )

        if not prob_records:
            return pd.DataFrame()

        df = pd.DataFrame(prob_records)
        return cast(
            pd.DataFrame,
            df.groupby(["Class", "Solver"], as_index=False)[["Success Rate"]].mean(),
        )
