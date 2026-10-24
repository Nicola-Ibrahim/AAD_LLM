"""Construct the synthesis campaign from concrete adapters."""

from collections.abc import Iterator
from contextlib import contextmanager

from evolution.application.campaign.run import SynthesisCampaignCoordinator
from evolution.infra.concurrency.runner import ProcessPoolRunner
from evolution.infra.concurrency.worker import run_synthesis_worker
from evolution.infra.engines.llamea import LLaMEAEngine
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.infra.cpu import available_cpu_count
from shared.infra.database import Database
from shared.infra.problems.factory import BBOBProblemFactory


@contextmanager
def build_synthesis_campaign(llm_client: LLMClient) -> Iterator[SynthesisCampaignCoordinator]:
    workers = available_cpu_count()
    database = Database()
    try:
        yield SynthesisCampaignCoordinator(
            sqlite_repo=SQLiteSynthesisRepository(database.session_factory),
            model_name=llm_client.model.name,
            logger=SynthesisLogger(verbose=True),
            engine=LLaMEAEngine(llm_client=llm_client, code_repo=CodeRepository()),
            problem_factory=BBOBProblemFactory(),
            dispatcher=ProcessPoolRunner(max_workers=workers),
            worker_fn=run_synthesis_worker,
            worker_count=workers,
        )
    finally:
        database.dispose()
