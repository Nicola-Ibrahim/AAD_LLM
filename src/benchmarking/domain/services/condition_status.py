"""Pure validity and completion rules shared by readiness, audit, and resumption."""

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal

from benchmarking.domain.evaluation import (
    EVALUATION_SCHEMA_VERSION,
    ERROR_DEFINITION,
    executed_trial_count,
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
) -> ConditionStatus:
    """Preserve existing cache validity without imposing new protocol requirements."""
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
        provenance.get("evaluation_schema_version") != EVALUATION_SCHEMA_VERSION
        or provenance.get("error_definition") != ERROR_DEFINITION
    ):
        return ConditionStatus("NEEDS_RERUN", recorded, 0, expected_trials, None, "stale_schema")
    if expected_code_hash and provenance.get("code_hash") != expected_code_hash:
        return ConditionStatus(
            "NEEDS_RERUN", recorded, 0, expected_trials, median_error, "stale_champion"
        )
    complete = recorded >= expected_trials
    return ConditionStatus(
        "COMPLETED" if complete else "PENDING",
        recorded,
        recorded,
        expected_trials,
        median_error,
        "complete" if complete else "partial" if recorded else "not_started",
    )
