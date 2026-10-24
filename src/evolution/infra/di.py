"""Evolution-owned Dishka bindings for campaigns and process-local synthesis workers."""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from dishka import AnyOf, Provider, Scope, from_context, provide

from evolution.application.campaign.models import CampaignTask
from evolution.application.campaign.run import SynthesisCampaignCoordinator
from evolution.application.interfaces.code_store import SynthesisCodeStore
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.interfaces.task_dispatcher import TaskDispatcher
from evolution.application.synthesis.models import SessionResult
from evolution.application.synthesis.run import SingleSynthesisUseCase
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.infra.concurrency.runner import ProcessPoolRunner
from evolution.infra.concurrency.worker import run_synthesis_worker
from evolution.infra.engines.llamea import LLaMEAEngine
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.infra.cpu import available_cpu_count
from shared.infra.di import container_scope


class EvolutionProvider(Provider):
    scope = Scope.REQUEST
    worker_engine = from_context(provides=SynthesisEngine)

    @provide(scope=Scope.APP)
    def llm(self) -> Iterator[LLMClient]:
        client = LLMClient(os.getenv("LLM_PROVIDER", "local"))
        try:
            yield client
        finally:
            client.close()

    repository = provide(
        SQLiteSynthesisRepository, provides=AnyOf[SQLiteSynthesisRepository, SynthesisRepository]
    )
    engine = provide(LLaMEAEngine)
    single_synthesis = provide(SingleSynthesisUseCase)

    @provide
    def logger(self) -> AnyOf[SynthesisLogger, BaseLogger]:
        # Keep logger defaults local rather than registering generic bool/str/stream values.
        return SynthesisLogger(verbose=True)

    @provide
    def code_store(self) -> AnyOf[CodeRepository, SynthesisCodeStore]:
        return CodeRepository()

    @provide(scope=Scope.APP)
    def workers(self) -> int:
        return available_cpu_count()

    @provide
    def dispatcher(
        self, workers: int
    ) -> AnyOf[
        ProcessPoolRunner[CampaignTask, SessionResult], TaskDispatcher[CampaignTask, SessionResult]
    ]:
        return ProcessPoolRunner(max_workers=workers)

    @provide
    def campaign(
        self,
        repository: SynthesisRepository,
        logger: BaseLogger,
        engine: LLaMEAEngine,
        llm: LLMClient,
        problem_factory: ProblemFactory,
        dispatcher: TaskDispatcher[CampaignTask, SessionResult],
        workers: int,
    ) -> SynthesisCampaignCoordinator:
        return SynthesisCampaignCoordinator(
            sqlite_repo=repository,
            logger=logger,
            engine=engine,
            model_name=llm.model.name,
            problem_factory=problem_factory,
            dispatcher=dispatcher,
            worker_fn=run_synthesis_worker,
            worker_count=workers,
        )


@contextmanager
def synthesis_worker_scope(engine: SynthesisEngine) -> Iterator[SingleSynthesisUseCase]:
    """Open resources in the worker process, never in its serialized task payload."""
    with container_scope(
        EvolutionProvider(),
        context={},
        request_context={SynthesisEngine: engine},
    ) as container:
        yield container.get(SingleSynthesisUseCase)
