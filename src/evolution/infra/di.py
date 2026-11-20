"""Evolution-owned Dishka bindings for campaigns and process-local synthesis workers."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from dishka import AnyOf, Provider, Scope, provide

from evolution.application.campaign.audit import CampaignAudit
from evolution.application.campaign.experiment_task import ExperimentTask
from evolution.application.campaign.service import SynthesisCampaign
from evolution.application.interfaces.experiment_worker_pool import ExperimentWorkerPool
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngineFactory
from evolution.application.synthesis.result import SynthesisResult
from evolution.application.synthesis.service import Synthesis
from evolution.domain.interfaces.code_repository import CodeRepository
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.infra.concurrency.process_worker_pool import ProcessWorkerPool
from evolution.infra.concurrency.worker import run_synthesis_worker
from evolution.infra.engines.llamea.factory import LLaMEAEngineFactory
from evolution.infra.logging import SynthesisLogger
from evolution.infra.storage.code.memory import MemoryCodeRepository
from evolution.infra.storage.code.repository import FileCodeRepository
from evolution.infra.storage.synthesis.memory import MemorySynthesisRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.config import DATA_DIR
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.infra.cpu import available_cpu_count
from shared.infra.di import container_scope


class EvolutionProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(
        SQLiteSynthesisRepository, provides=AnyOf[SQLiteSynthesisRepository, SynthesisRepository]
    )

    @provide
    def checkpoint_root(self) -> Path:
        return DATA_DIR / "evolution_state"

    @provide
    def engine_factory(
        self, code_repo: CodeRepository, checkpoint_root: Path
    ) -> AnyOf[LLaMEAEngineFactory, SynthesisEngineFactory]:
        return LLaMEAEngineFactory(code_repo, checkpoint_root)

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
    ) -> CampaignAudit:
        return CampaignAudit(repository, logger)

    @provide
    def campaign(
        self,
        repository: SynthesisRepository,
        logger: BaseLogger,
        problem_factory: ProblemFactory,
        worker_pool: ExperimentWorkerPool[ExperimentTask, SynthesisResult],
        workers: int,
    ) -> SynthesisCampaign:
        return SynthesisCampaign(
            sqlite_repo=repository,
            logger=logger,
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


@contextmanager
def synthesis_worker_scope() -> Iterator[Synthesis]:
    """Resolve synthesis resources inside the worker process, not in task payloads."""
    with container_scope(
        EvolutionProvider(),
        context={},
        request_context={},
    ) as container:
        yield container.get(Synthesis)
