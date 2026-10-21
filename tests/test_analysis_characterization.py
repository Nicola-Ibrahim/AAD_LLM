"""Numerical contracts recorded before migrating analysis orchestration."""

import numpy as np
import pandas as pd
import pytest

from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.vos import BenchmarkCondition, BenchmarkDataset, RunTrace


@pytest.mark.parametrize("noise_std", [0.0, 0.05, 0.2])
@pytest.mark.parametrize("include_failed_trace", [False, True])
def test_adaptive_target_fallbacks(noise_std: float, include_failed_trace: bool) -> None:
    dataset = BenchmarkDataset()
    if include_failed_trace:
        dataset.add_run(
            BenchmarkCondition(dim=2, noise_std=noise_std, problem_id=1),
            "Model / baseline",
            RunTrace(evaluations=np.array([1]), raw_objectives=np.array([np.inf])),
        )
    targets = EcdfConvergenceEngine().compute_adaptive_targets(dataset, noise_std)
    expected = np.logspace(-8, 2, 51) if noise_std == 0.0 else np.logspace(-2, 3, 51)
    np.testing.assert_array_equal(targets, expected)


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
    dataset = BenchmarkDataset()
    dataset.add_run(
        BenchmarkCondition(dim=2, noise_std=0.0, problem_id=1),
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
        budget=100,
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


def test_auc_excludes_attainment_after_fixed_budget() -> None:
    dataset = BenchmarkDataset()
    for dim in [2, 5]:
        dataset.add_run(
            BenchmarkCondition(dim=dim, noise_std=0.0, problem_id=1),
            "Model / baseline",
            RunTrace(
                evaluations=np.array([1, 201]),
                raw_objectives=np.array([10.0, 0.0]),
            ),
        )
    engine = EcdfConvergenceEngine()
    table = engine.compute_auc_ecdf_matrix(
        dataset,
        ["Model / baseline"],
        np.array([1.0]),
        group_by="condition",
        budget=200,
    )
    np.testing.assert_array_equal(table["AUC-ECDF (%)"], [0.0, 0.0])
    extended = engine.compute_auc_ecdf_matrix(
        dataset,
        ["Model / baseline"],
        np.array([1.0]),
        group_by="condition",
        budget=1000,
    )
    assert (extended["AUC-ECDF (%)"] > 0).all()

    # Identical traces and targets produce identical fixed-budget AUC across dimensions.
    assert extended["AUC-ECDF (%)"].nunique() == 1
