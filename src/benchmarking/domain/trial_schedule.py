"""Identity-based selection of recorded benchmark trials, without changing history."""

from collections.abc import Mapping

import numpy as np

from benchmarking.domain.evaluation import executed_trial_count

TrialIdentity = tuple[int, int]  # BBOB instance ID, optimizer/noise seed.


def matching_trial_indices(
    provenance: Mapping[str, object], schedule: tuple[TrialIdentity, ...]
) -> list[int]:
    """Select one completed observation per requested identity; never infer missing seeds."""
    count = executed_trial_count(provenance)
    if not schedule:
        return list(range(count))
    wanted = set(schedule)
    seen: set[TrialIdentity] = set()
    indices: list[int] = []
    for index, (instance, seed) in enumerate(
        zip(provenance.get("instance_ids", []), provenance.get("trial_seeds", []))
    ):
        if index >= count:
            break
        identity = (instance, seed)
        if identity in wanted and identity not in seen:
            indices.append(index)
            seen.add(identity)
    return indices


def select_scheduled_trials(
    provenance: Mapping[str, object], schedule: tuple[TrialIdentity, ...]
) -> dict[str, object]:
    """Return a detached terminal-data view; original arrays and trace order stay intact."""
    indices = matching_trial_indices(provenance, schedule)
    selected = dict(provenance)
    for key in (
        "clean_errors",
        "errors",
        "best_objectives",
        "true_optima",
        "instance_ids",
        "trial_seeds",
        "runtimes",
        "evaluations_used",
        "observed_objectives",
        "trial_records",
    ):
        if key in provenance:
            values = provenance[key]
            selected[key] = [values[i] for i in indices if i < len(values)]
    errors = selected.get("clean_errors", selected.get("errors", []))
    selected["n_runs"] = len(indices)
    selected["median_error"] = float(np.median(errors)) if errors else float("inf")
    selected["median_clean_error"] = selected["median_error"]
    return selected
