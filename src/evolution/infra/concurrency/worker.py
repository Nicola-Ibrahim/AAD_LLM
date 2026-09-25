"""Picklable process-pool worker entry point for one synthesis session."""

from typing import Any

from evolution.application.interfaces.engine import SessionResult


def run_synthesis_worker(item: dict[str, Any]) -> SessionResult:
    from shared.database.engine import initialize_sqlite_storage
    from evolution.application.single_synthesis_usecase import SingleSynthesisUseCase

    repository = initialize_sqlite_storage()
    use_case = SingleSynthesisUseCase(engine=item["engine"], sqlite_repo=repository)
    return use_case.execute(
        problem=item["problem"],
        experiment_id=item["experiment_id"],
        config=item["config"],
        prompt_strategy=item["prompt_strategy"],
        synthesis_mode=item["synthesis_mode"],
        initial_iteration=item["initial_iteration"],
        key=item["key"],
        verbose=False,
    )
