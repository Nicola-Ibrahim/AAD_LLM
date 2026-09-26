"""Pure condition validity, accounting, and ranking policy checks."""

import pandas as pd
import pytest

from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.domain.evaluation import EVALUATION_SCHEMA_VERSION, ERROR_DEFINITION
from benchmarking.domain.services.condition_status import inspect_condition


@pytest.mark.parametrize(
    "code,directory,schema,hash_value,count,state,reusable,reason",
    [
        (False, True, 2, "current", 20, "MISSING_CODE", 0, "missing_code"),
        (True, False, 2, "current", 20, "PENDING", 0, "missing_provenance"),
        (True, True, 1, "current", 20, "NEEDS_RERUN", 0, "stale_schema"),
        (True, True, 2, "old", 20, "NEEDS_RERUN", 0, "stale_champion"),
        (True, True, 2, "current", 20, "COMPLETED", 20, "complete"),
        (True, True, 2, "current", 4, "PENDING", 4, "partial"),
        (True, True, 2, "current", 0, "PENDING", 0, "not_started"),
    ],
)
def test_condition_policy(
    code: bool,
    directory: bool,
    schema: int,
    hash_value: str,
    count: int,
    state: str,
    reusable: int,
    reason: str,
) -> None:
    result = inspect_condition(
        code_available=code,
        directory_exists=directory,
        provenance={
            "evaluation_schema_version": schema,
            "error_definition": ERROR_DEFINITION,
            "code_hash": hash_value,
            "clean_errors": [0.0] * count,
        },
        expected_code_hash="current",
        expected_trials=20,
    )
    assert result.status == state
    assert result.reusable_trials == reusable
    assert result.recorded_trials == count
    assert result.reason == reason


def test_confirmed_failure_counts_but_historical_skipped_tail_does_not() -> None:
    result = inspect_condition(
        code_available=True,
        directory_exists=True,
        expected_code_hash=None,
        expected_trials=20,
        provenance={
            "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
            "error_definition": ERROR_DEFINITION,
            "clean_errors": [float("inf")] * 20,
            "runtimes": [0.1] * 2 + [0.0] * 18,
            "evaluations_used": [0] * 20,
        },
    )
    assert result.reusable_trials == 2
    assert result.status == "PENDING"


def test_ranking_is_owned_by_selection_and_preserves_sqlite_null_order() -> None:
    base = dict(
        llm_name="model",
        problem_id=1,
        dim=2,
        prompt_strategy="baseline",
        mode="explicit",
        noise_std=0.0,
        experiment_id=1,
        algorithm_name="optimizer",
        code_path="candidate.py",
    )
    rows = pd.DataFrame(
        [
            dict(base, iteration_id=3, final_error=2.0, evaluations_used=1),
            dict(base, iteration_id=2, final_error=1.0, evaluations_used=4),
            dict(base, iteration_id=1, final_error=1.0, evaluations_used=None),
            dict(base, iteration_id=4, final_error=1.0, evaluations_used=None),
        ]
    )
    selected = ChampionSelectionService.select_candidates(rows)
    winner = next(iter(selected["model"].values()))
    assert winner["iteration_id"] == 1
    assert winner["evaluations_used"] is None
    assert set(winner) == {
        "problem_id",
        "dim",
        "mode",
        "noise_std",
        "prompt_strategy",
        "experiment_id",
        "iteration_id",
        "algorithm_name",
        "final_error",
        "evaluations_used",
        "code_path",
        "llm_name",
    }
