import numpy as np

from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace


def _run(values: list[float]) -> RunTrace:
    return RunTrace(
        evaluations=np.array([1, 10, 100], dtype=float),
        raw_objectives=np.array(values, dtype=float),
    )


def _dataset() -> EvaluationDataset:
    data = EvaluationDataset()
    cond = EvaluationCondition(dim=2, noise_std=0.0, problem_id=1)
    data.add_run(cond, "Qwen-14B / baseline", _run([1.0, 1e-3, 1e-9]))
    data.add_run(cond, "Qwen-14B / baseline", _run([1.0, 1e-2, 1e-3]))
    data.add_run(cond, "Qwen-14B / guided", _run([1.0, 1e-9, 1e-9]))
    data.add_run(cond, "CMA-ES", _run([1.0, 1e-9, 1e-9]))
    return data


def test_reliability_table_discovers_models_and_does_not_include_baselines():
    engine = ReliabilityEngine()
    table = engine.compute_reliability_table(_dataset(), expected_trials=2)

    assert engine.discover_models(_dataset()) == ["Qwen-14B"]
    baseline = table[table["Strategy"] == "baseline"].iloc[0]
    assert baseline["Primary Successes"] == 1
    assert baseline["Trials"] == 2
    assert baseline["Complete"]
    assert baseline["Primary Success Rate"] == 0.5
    assert baseline["Median Evals to Primary Target"] == 100.0


def test_wilson_interval_and_attainment_bootstrap_are_reproducible():
    engine = ReliabilityEngine()
    empty_lower, empty_upper = engine.wilson_interval(0, 0)
    assert np.isnan(empty_lower) and np.isnan(empty_upper)
    lower, upper = engine.wilson_interval(1, 2)
    assert 0.0 < lower < 0.5 < upper < 1.0

    runs = _dataset().get_runs(2, 0.0, 1, "Qwen-14B / baseline")
    grid = np.array([1, 10, 100], dtype=float)
    first = engine.compute_attainment_band(runs, grid, bootstrap_samples=100, bootstrap_seed=7)
    second = engine.compute_attainment_band(runs, grid, bootstrap_samples=100, bootstrap_seed=7)
    for left, right in zip(first, second):
        assert np.array_equal(left, right)
    assert first[0].tolist() == [0.0, 0.0, 0.5]


def test_incomplete_conditions_are_excluded_from_aggregate_not_counted_as_failures():
    engine = ReliabilityEngine()
    table = engine.compute_reliability_table(_dataset(), expected_trials=3)
    aggregate = engine.compute_aggregate_reliability(table, bootstrap_samples=100)
    assert aggregate.empty
