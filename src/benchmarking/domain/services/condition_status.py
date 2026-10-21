"""Pure validity and completion rules shared by readiness, audit, and resumption."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from benchmarking.domain.benchmark_results import (
    BENCHMARK_SCHEMA_VERSION,
    CHAMPION_RETURN_VALIDATION_VERSION,
    ERROR_DEFINITION,
    executed_trial_count,
)
from benchmarking.domain.trial_schedule import (
    TrialIdentity,
    matching_trial_indices,
    select_scheduled_trials,
)

ConditionState = Literal["MISSING_CODE", "PENDING", "NEEDS_RERUN", "COMPLETED"]


@dataclass(frozen=True, slots=True)
class ConditionStatus:
    status: ConditionState
    recorded_trials: int
    reusable_trials: int
    expected_trials: int
    median_error: float | None
    reason: str


def inspect_condition(
    *,
    code_available: bool,
    directory_exists: bool,
    provenance: Mapping[str, object] | None,
    expected_code_hash: str | None,
    expected_trials: int,
    expected_budget: int | None,
    trial_schedule: tuple[TrialIdentity, ...] = (),
) -> ConditionStatus:
    """Inspect validity; None budget supports budget-agnostic historical readers.

    Execution, readiness and current analysis supply their configured budget.
    """
    recorded = executed_trial_count(provenance) if provenance is not None else 0
    median = (
        provenance.get("median_error", provenance.get("median_clean_error")) if provenance else None
    )
    median_error = float(median) if isinstance(median, (int, float)) else None
    if not code_available:
        return ConditionStatus("MISSING_CODE", recorded, 0, expected_trials, None, "missing_code")
    if not directory_exists or provenance is None:
        return ConditionStatus("PENDING", recorded, 0, expected_trials, None, "missing_provenance")
    if (
        provenance.get("evaluation_schema_version") != BENCHMARK_SCHEMA_VERSION
        or provenance.get("error_definition") != ERROR_DEFINITION
    ):
        return ConditionStatus("NEEDS_RERUN", recorded, 0, expected_trials, None, "stale_schema")
    if (
        provenance.get("model") is not None
        and provenance.get("return_validation_version") != CHAMPION_RETURN_VALIDATION_VERSION
    ):
        return ConditionStatus(
            "NEEDS_RERUN", recorded, 0, expected_trials, None, "stale_return_validation"
        )
    if expected_code_hash and provenance.get("code_hash") != expected_code_hash:
        return ConditionStatus(
            "NEEDS_RERUN", recorded, 0, expected_trials, median_error, "stale_champion"
        )
    if expected_budget is not None and provenance.get("budget") != expected_budget:
        return ConditionStatus("NEEDS_RERUN", recorded, 0, expected_trials, None, "stale_budget")
    reusable = len(matching_trial_indices(provenance, trial_schedule))
    if trial_schedule:
        median_error = (
            select_scheduled_trials(provenance, trial_schedule)["median_error"]
            if reusable
            else None
        )
    complete = reusable >= expected_trials
    return ConditionStatus(
        "COMPLETED" if complete else "PENDING",
        recorded,
        reusable,
        expected_trials,
        median_error,
        "complete" if complete else "partial" if reusable else "not_started",
    )
