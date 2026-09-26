"""Construct the synthesis campaign from concrete adapters."""

from evolution.application.campaign.run import SynthesisCampaignCoordinator
from evolution.infra.llm.client import LLMClient
from evolution.infra.concurrency.runner import ProcessPoolRunner
from evolution.infra.concurrency.worker import run_synthesis_worker
from evolution.infra.engines.llamea import LLaMEAEngine
from evolution.infra.logging import SynthesisLogger
from evolution.infra.problems.factory import BBOBProblemFactory
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.infra.database.engine import initialize_sqlite_storage


def build_synthesis_campaign(llm_client: LLMClient) -> SynthesisCampaignCoordinator:
    config_repo = SynthesisConfigRepository()
    config = config_repo.load_config()
    return SynthesisCampaignCoordinator(
        sqlite_repo=initialize_sqlite_storage(),
        config=config,
        model_name=llm_client.model.name,
        logger=SynthesisLogger(verbose=True),
        engine=LLaMEAEngine(llm_client=llm_client, code_repo=CodeRepository()),
        problem_factory=BBOBProblemFactory(),
        dispatcher=ProcessPoolRunner(max_workers=config.num_processes),
        worker_fn=run_synthesis_worker,
    )
