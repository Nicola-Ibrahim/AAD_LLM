"""Backend preparation of exploratory performance metrics; no presentation or IO."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from benchmarking.application.analysis.view_data import AnalysisInputs
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine


@dataclass(frozen=True)
class PerformanceMetrics:
    targets: dict[float, np.ndarray]
    table: pd.DataFrame
    rankings: pd.Series


def compute_performance_metrics(inputs: AnalysisInputs) -> PerformanceMetrics:
    targets = {
        noise: EcdfConvergenceEngine().compute_adaptive_targets(inputs.dataset, noise_std=noise)
        for noise in inputs.dataset.noise_stds
    }
    table = EcdfConvergenceEngine().compute_auc_ecdf_matrix(
        inputs.dataset, inputs.solver_order, targets=targets, group_by="condition"
    )
    table["Canonical Solver"] = table["Solver"].str.replace(r" \(noise-adapted\)", "", regex=True)
    rankings = table.groupby("Canonical Solver")["AUC-ECDF (%)"].mean().sort_values(ascending=False)
    return PerformanceMetrics(targets, table, rankings)
