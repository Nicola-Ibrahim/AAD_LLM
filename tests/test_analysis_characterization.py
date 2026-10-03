"""Numerical contracts recorded before migrating analysis orchestration."""

import numpy as np
import pandas as pd
import pytest

from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace


def test_ecdf_and_convergence_characterization():
    runs = [
        RunTrace(evaluations=np.array([1, 3, 5]), raw_objectives=np.array([10.0, 2.0, 4.0])),
        RunTrace(evaluations=np.array([2, 4]), raw_objectives=np.array([6.0, 0.0])),
    ]
    grid = np.array([1, 2, 3, 4, 5, 10])
    engine = EcdfConvergenceEngine()
    median, lower, upper, ecdf = engine.compute_trajectory_and_ecdf(
        runs, grid, np.array([1.0, 5.0])
    )
    expected = np.array([[10.0, 10.0, 2.0, 2.0, 2.0, 2.0], [np.inf, 6.0, 6.0, 0.0, 0.0, 0.0]])
    np.testing.assert_array_equal(median, np.median(expected, axis=0))
    np.testing.assert_array_equal(lower, np.percentile(expected, 25, axis=0))
    np.testing.assert_array_equal(upper, np.percentile(expected, 75, axis=0))
    np.testing.assert_array_equal(ecdf, [0.0, 0.0, 0.25, 0.75, 0.75, 0.75])
    np.testing.assert_array_equal(median[1:], [8.0, 4.0, 1.0, 1.0, 1.0])


@pytest.mark.parametrize("kind", ["missing", "failed", "irregular"])
def test_ecdf_only_matches_paired_calculation(kind: str) -> None:
    runs = []
    if kind == "failed":
        runs = [RunTrace(evaluations=np.array([]), raw_objectives=np.array([]))]
    elif kind == "irregular":
        runs = [
            RunTrace(evaluations=np.array([1, 3, 8]), raw_objectives=np.array([10.0, 2.0, 4.0])),
            RunTrace(evaluations=np.array([2, 7]), raw_objectives=np.array([6.0, 0.0])),
        ]
    grid = np.array([1, 2, 3, 7, 8, 10])
    targets = np.array([1.0, 5.0])
    engine = EcdfConvergenceEngine()
    np.testing.assert_array_equal(
        engine.compute_ecdf(runs, grid, targets),
        engine.compute_trajectory_and_ecdf(runs, grid, targets)[3],
    )


def test_auc_preserves_values_without_convergence_statistics(monkeypatch) -> None:
    dataset = EvaluationDataset()
    dataset.add_run(
        EvaluationCondition(dim=2, noise_std=0.0, problem_id=1),
        "Model / baseline",
        RunTrace(evaluations=np.array([1, 10, 100]), raw_objectives=np.array([10.0, 1.0, 0.0])),
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("AUC must not compute median or IQR.")

    monkeypatch.setattr(np, "median", forbidden)
    monkeypatch.setattr(np, "percentile", forbidden)
    table = EcdfConvergenceEngine().compute_auc_ecdf_matrix(
        dataset,
        ["Model / baseline"],
        np.array([0.5, 5.0]),
        group_by="condition",
        max_evals=100,
        n_grid_points=3,
    )
    expected = pd.DataFrame(
        [
            {
                "Solver": "Model / baseline",
                "Dim": 2,
                "Noise Std": 0.0,
                "Problem ID": 1,
                "AUC-ECDF (%)": 50.0,
                "AUC-ECDF": 0.5,
                "Type": "LLaMEA Evolved",
            }
        ]
    )
    pd.testing.assert_frame_equal(table, expected)
