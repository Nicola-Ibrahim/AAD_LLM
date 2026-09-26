"""Picklable process-pool worker entry point for one synthesis session."""

from evolution.application.campaign.models import CampaignTask
from evolution.application.synthesis.models import SessionResult


def run_synthesis_worker(item: CampaignTask) -> SessionResult:
    from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
    from shared.infra.database import Database
    from evolution.application.synthesis.run import SingleSynthesisUseCase
    from evolution.infra.logging import SynthesisLogger

    database = Database()
    repository = SQLiteSynthesisRepository(database.session_factory)
    use_case = SingleSynthesisUseCase(
        engine=item["engine"],
        sqlite_repo=repository,
        logger=SynthesisLogger(verbose=False),
    )
    try:
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
    finally:
        database.dispose()
