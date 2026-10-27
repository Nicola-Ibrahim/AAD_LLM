"""Picklable process-pool worker entry point for one synthesis session."""

from evolution.application.campaign.experiment_task import ExperimentTask
from evolution.application.synthesis.result import SynthesisResult
from shared.infra.logging.runtime import diagnostic_context


def run_synthesis_worker(item: ExperimentTask) -> SynthesisResult:
    from evolution.infra.di import synthesis_worker_scope

    with (
        diagnostic_context(experiment_id=item["experiment_id"], task=item["key"]),
        synthesis_worker_scope(item["engine"]) as use_case,
    ):
        return use_case.execute(
            problem=item["problem"],
            experiment_id=item["experiment_id"],
            config=item["config"],
            prompt_strategy=item["prompt_strategy"],
            synthesis_mode=item["synthesis_mode"],
            initial_iteration=item["initial_iteration"],
            key=item["key"],
            verbose=False,
            restart=item.get("restart", False),
        )
