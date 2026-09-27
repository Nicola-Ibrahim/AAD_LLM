"""Pure descriptive classification of completed and historical benchmark trials."""

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from benchmarking.domain.evaluation import executed_trial_count


@dataclass(frozen=True)
class TrialOutcomeSummary:
    recorded_trials: int
    executed_trials: int
    failed_trials: int
    solved_trials: int
    meaningful_trials: int
    success_rate: float
    median_error: float
    median_finite_error: float
    category: str


def summarize_trial_outcomes(
    provenance: Mapping[str, object],
    expected_trials: int,
    primary_target: float,
    secondary_target: float,
) -> TrialOutcomeSummary:
    """Large error is descriptive; infinite errors denote unsuccessful execution."""
    recorded = np.asarray(provenance.get("clean_errors", provenance.get("errors", [])), dtype=float)
    count = min(executed_trial_count(provenance), expected_trials)
    errors = recorded[:count]
    finite = errors[np.isfinite(errors)]
    failed = count - len(finite)
    solved = int(np.count_nonzero(errors <= primary_target))
    meaningful = int(np.count_nonzero(errors <= secondary_target))
    median = float(np.median(errors)) if count else float("nan")
    finite_median = float(np.median(finite)) if len(finite) else float("nan")
    if count < expected_trials:
        category = "incomplete"
    elif failed == count:
        category = "all_failed"
    elif failed > count / 2:
        category = "mostly_failed"
    elif failed:
        category = "some_failed"
    elif median > secondary_target:
        category = "large_error"
    else:
        category = "finite_results"
    return TrialOutcomeSummary(
        len(recorded),
        count,
        failed,
        solved,
        meaningful,
        solved / count if count else float("nan"),
        median,
        finite_median,
        category,
    )
