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

        meta.iteration = iteration_num
        iterations_data.append(meta)

        if meta.fitness.final_error is not None and meta.fitness.final_error < best_error:
            best_error = meta.fitness.final_error
            best_iteration = iteration_num
            best_algo = meta.algorithm_name

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
