"""Evolution-owned Dishka bindings for campaigns and process-local synthesis workers."""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from dishka import AnyOf, Provider, Scope, from_context, provide

from evolution.application.campaign.audit import CampaignAudit
from evolution.application.campaign.experiment_task import ExperimentTask
from evolution.application.campaign.service import SynthesisCampaign
from evolution.application.interfaces.experiment_worker_pool import ExperimentWorkerPool
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.synthesis.result import SynthesisResult
from evolution.application.synthesis.service import Synthesis
from evolution.domain.interfaces.code_repository import CodeRepository
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.infra.concurrency.process_worker_pool import ProcessWorkerPool
from evolution.infra.concurrency.worker import run_synthesis_worker
from evolution.infra.engines.llamea import LLaMEAEngine
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from evolution.infra.storage.code.memory import MemoryCodeRepository
from evolution.infra.storage.code.repository import FileCodeRepository
from evolution.infra.storage.synthesis.memory import MemorySynthesisRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.application.diagnostics import preserve_primary_failure
from shared.config import DATA_DIR
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.infra.cpu import available_cpu_count
from shared.infra.di import container_scope


class EvolutionProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, *, test_generation_on_startup: bool = False) -> None:
        super().__init__()
        self.test_generation_on_startup = test_generation_on_startup

    @provide(scope=Scope.APP)
    def llm(self) -> Iterator[LLMClient]:
        client = LLMClient(os.getenv("LLM_PROVIDER", "local"))
        try:
            if self.test_generation_on_startup:
                client.ping()
            yield client
        finally:
            with preserve_primary_failure("LLM client close"):
                client.close()

    repository = provide(
        SQLiteSynthesisRepository, provides=AnyOf[SQLiteSynthesisRepository, SynthesisRepository]
    )

    @provide
    def checkpoint_root(self) -> Path:
        return DATA_DIR / "evolution_state"

    @provide
    def engine(
        self, llm_client: LLMClient, code_repo: CodeRepository, checkpoint_root: Path
    ) -> AnyOf[LLaMEAEngine, SynthesisEngine]:
        return LLaMEAEngine(llm_client, code_repo, checkpoint_root)

    synthesis = provide(Synthesis)

    @provide
    def logger(self) -> AnyOf[SynthesisLogger, BaseLogger]:
        # Keep logger defaults local rather than registering generic bool/str/stream values.
        return SynthesisLogger(verbose=True)

    @provide
    def code_repository(self) -> AnyOf[FileCodeRepository, CodeRepository]:
        return FileCodeRepository()

    @provide(scope=Scope.APP)
    def workers(self) -> int:
        return available_cpu_count()

    @provide
    def worker_pool(
        self, workers: int
    ) -> AnyOf[
        ProcessWorkerPool[ExperimentTask, SynthesisResult],
        ExperimentWorkerPool[ExperimentTask, SynthesisResult],
    ]:
        return ProcessWorkerPool(max_workers=workers)

    @provide
    def audit(
        self,
        repository: SynthesisRepository,
        logger: BaseLogger,
        engine: SynthesisEngine,
    ) -> CampaignAudit:
        return CampaignAudit(repository, logger, engine.model_name)

    @provide
    def campaign(
        self,
        repository: SynthesisRepository,
        logger: BaseLogger,
        engine: SynthesisEngine,
        problem_factory: ProblemFactory,
        worker_pool: ExperimentWorkerPool[ExperimentTask, SynthesisResult],
        workers: int,
    ) -> SynthesisCampaign:
        return SynthesisCampaign(
            sqlite_repo=repository,
            logger=logger,
            engine=engine,
            model_name=engine.model_name,
            problem_factory=problem_factory,
            worker_pool=worker_pool,
            worker_fn=run_synthesis_worker,
            worker_count=workers,
        )


class TransientEvolutionProvider(EvolutionProvider):
    """Single-process synthesis with memory-only study storage and temporary checkpoints.

    No research database is resolved. Operational logs and gateway pacing remain
    host-owned; checkpoint files are removed when the provider scope closes.
    """

    repository = provide(MemorySynthesisRepository, provides=SynthesisRepository, override=True)

    @provide(override=True)
    def code_repository(self) -> CodeRepository:
        return MemoryCodeRepository()

    @provide(override=True)
    def checkpoint_root(self) -> Iterator[Path]:
        with TemporaryDirectory(prefix="aad-transient-synthesis-") as directory:
            yield Path(directory)


class SynthesisWorkerProvider(Provider):
    """Workers reuse their serialized engine and must not open another LLM client."""

    worker_engine = from_context(provides=SynthesisEngine, scope=Scope.REQUEST, override=True)


@contextmanager
def synthesis_worker_scope(engine: SynthesisEngine) -> Iterator[Synthesis]:
    """Open resources in the worker process, never in its serialized task payload."""
    with container_scope(
        EvolutionProvider(),
        SynthesisWorkerProvider(),
        context={},
        request_context={SynthesisEngine: engine},
    ) as container:
        yield container.get(Synthesis)
