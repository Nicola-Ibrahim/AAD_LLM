from typing import Any
from core.schema import ExperimentSummary, IterationMetadata, ProblemProfile


def build_experiment_summary(
    history: list[Any],
    problem: ProblemProfile,
    mode: str,
    llm_name: str,
) -> ExperimentSummary:
    """Assembles an ExperimentSummary model instance from raw run history."""
    iterations_data: list[IterationMetadata] = []

    best_iteration = None
    best_error = float("inf")
    best_algo = None

    for i, solution in enumerate(history):
        iteration_num = i + 1
        meta: IterationMetadata | None = getattr(solution, "metadata", None)

        if not meta:
            continue

        # Use existing iteration if set by Evaluator, otherwise fall back to enumeration index.
        # Use model_copy to avoid mutating solution.metadata in place.
        effective_iteration = meta.iteration if meta.iteration is not None else iteration_num
        meta_copy = meta.model_copy(update={"iteration": effective_iteration})
        iterations_data.append(meta_copy)

        if meta_copy.fitness.final_error is not None and meta_copy.fitness.final_error < best_error:
            best_error = meta_copy.fitness.final_error
            best_iteration = effective_iteration
            best_algo = meta_copy.algorithm_name

    best_err_val = best_error if best_error != float("inf") else None

    return ExperimentSummary(
        mode=mode,
        llm_name=llm_name,
        problem=problem,
        best_iteration=best_iteration,
        best_algorithm=best_algo,
        best_final_error=best_err_val,
        iterations=iterations_data,
    )
