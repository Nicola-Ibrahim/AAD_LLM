"""Post-evaluation review does not mutate results or automatically request synthesis."""

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from benchmarking.application.evaluation.summary import summarize_evaluations
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.domain.services.evaluation_outcomes import summarize_trial_outcomes


@pytest.mark.parametrize(
    "errors, category, failed",
    [
        ([float("inf")] * 20, "all_failed", 20),
        ([float("inf")] * 11 + [0.0] * 9, "mostly_failed", 11),
        ([float("inf")] + [0.0] * 19, "some_failed", 1),
        ([100.0] * 20, "large_error", 0),
        ([0.0] * 20, "finite_results", 0),
        ([float("inf")] * 2, "incomplete", 2),
    ],
)
def test_outcome_classification(errors: list[float], category: str, failed: int) -> None:
    result = summarize_trial_outcomes({"clean_errors": errors}, 20, 1e-8, 1e-2)
    assert result.category == category
    assert result.failed_trials == failed


def test_historical_tail_is_not_twenty_failed_trials() -> None:
    result = summarize_trial_outcomes(
        {
            "clean_errors": [float("inf")] * 20,
            "runtimes": [1.0] * 2 + [0.0] * 18,
            "evaluations_used": [10] * 2 + [0] * 18,
        },
        20,
        1e-8,
        1e-2,
    )
    assert result.recorded_trials == 20
    assert result.executed_trials == result.failed_trials == 2
    assert result.category == "incomplete"


def test_stale_results_and_baselines_do_not_suggest_synthesis() -> None:
    native = dict(
        key="current",
        raw_key="current",
        solver_type="champion",
        solver="llm",
        model="model",
        strategy="baseline",
        problem_id=1,
        dim=2,
        noise_std=0.0,
        target_dir="/traces/current",
        reason="complete",
    )
    stale = dict(
        native, key="stale", raw_key="stale", target_dir="/traces/stale", reason="stale_champion"
    )
    baseline = dict(native, key="pso", solver_type="baseline", solver="pso", model="pso")
    workload = MagicMock()
    workload.audit_champions_workload.return_value = pd.DataFrame([native, stale])
    workload.audit_baselines_workload.return_value = pd.DataFrame([baseline])
    selection = MagicMock()
    selection.flatten_champions.return_value = {
        "current": {"experiment_id": 7},
        "stale": {"experiment_id": 8},
    }
    state = MagicMock()
    state.eval_dir = Path("/traces")
    state.read_provenance.return_value = {"clean_errors": [float("inf")] * 20}
    table = summarize_evaluations(workload, selection, state, EvaluationConfig())
    assert table.loc[table["Rerun candidate"], "Experiment ID"].tolist() == [7]
    assert table.loc[table["Category"] == "missing_or_stale", "Valid trials"].tolist() == [0]
    current = table.loc[table["Category"] == "all_failed"]
    assert current["Executed trials"].tolist() == [20, 20]
    assert current["Valid trials"].tolist() == [0, 0]
    assert current["Execution rate"].tolist() == [0.0, 0.0]
    assert current["Failure rate"].tolist() == [1.0, 1.0]
    state.write_provenance.assert_not_called()
    state.remove_solver_traces.assert_not_called()
    state.open_run_logger.assert_not_called()


def test_partial_execution_failure_rates_include_all_executed_trials() -> None:
    native = dict(
        key="current",
        raw_key="current",
        solver_type="champion",
        solver="llm",
        model="model",
        strategy="baseline",
        problem_id=1,
        dim=5,
        noise_std=0.05,
        target_dir="/traces/current",
        reason="complete",
    )
    workload = MagicMock()
    workload.audit_champions_workload.return_value = pd.DataFrame([native])
    workload.audit_baselines_workload.return_value = pd.DataFrame()
    selection = MagicMock()
    selection.flatten_champions.return_value = {"current": {"experiment_id": 7}}
    state = MagicMock()
    state.eval_dir = Path("/traces")
    state.read_provenance.return_value = {"clean_errors": [float("inf")] * 11 + [0.008] * 9}

    table = summarize_evaluations(workload, selection, state, EvaluationConfig())

    assert table.loc[0, "Executed trials"] == 20
    assert table.loc[0, "Valid trials"] == 9
    assert table.loc[0, "Failed trials"] == 11
    assert table.loc[0, "Execution rate"] == pytest.approx(0.45)
    assert table.loc[0, "Failure rate"] == pytest.approx(0.55)
    assert table.loc[0, "Primary target rate"] == 0.0
    assert table.loc[0, "Median error"] == float("inf")
    assert table.loc[0, "Median finite error"] == pytest.approx(0.008)
