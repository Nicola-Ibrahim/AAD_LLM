EVALUATION_SCHEMA_VERSION = 2
ERROR_DEFINITION = "max(0, best_clean_objective - true_optimum)"


def executed_trial_count(provenance: dict[str, object]) -> int:
    """Exclude the unexecuted tail produced by the historical failure shortcut."""
    errors = provenance.get("clean_errors", provenance.get("errors", []))
    runtimes = provenance.get("runtimes", [])
    evaluations = provenance.get("evaluations_used", [])
    for index, (error, runtime, used) in enumerate(zip(errors, runtimes, evaluations)):
        if float(error) == float("inf") and runtime == 0.0 and used == 0:
            return index
    return len(errors)
