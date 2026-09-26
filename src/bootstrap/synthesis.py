"""Construct the synthesis campaign from concrete adapters."""

from evolution.application.campaign.run import SynthesisCampaignCoordinator
from evolution.infra.concurrency.runner import ProcessPoolRunner
from evolution.infra.concurrency.worker import run_synthesis_worker
from evolution.infra.engines.llamea import LLaMEAEngine
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.infra.database import Database
from shared.infra.problems.factory import BBOBProblemFactory


def build_synthesis_campaign(llm_client: LLMClient) -> SynthesisCampaignCoordinator:
    config_repo = SynthesisConfigRepository()
    config = config_repo.load_config()
    database = Database()
    return SynthesisCampaignCoordinator(
        sqlite_repo=SQLiteSynthesisRepository(database.session_factory),
        config=config,
        model_name=llm_client.model.name,
        logger=SynthesisLogger(verbose=True),
        engine=LLaMEAEngine(llm_client=llm_client, code_repo=CodeRepository()),
        problem_factory=BBOBProblemFactory(),
        dispatcher=ProcessPoolRunner(max_workers=config.num_processes),
        worker_fn=run_synthesis_worker,
    )
