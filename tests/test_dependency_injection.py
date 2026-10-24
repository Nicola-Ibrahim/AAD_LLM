"""Dishka owns resource lifetimes; core workflows remain framework-independent."""

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dishka import Provider, Scope, make_container

import benchmark.infra.di as benchmark_di
import evolution.infra.di as evolution_di
import shared.infra.di as shared_di
from benchmark.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.interfaces.benchmark_state_store import BenchmarkStateStore
from benchmark.application.interfaces.candidate_code_reader import CandidateCodeReader
from benchmark.application.interfaces.champion_repository import ChampionRepository
from benchmark.application.interfaces.logger import BenchmarkLoggerInterface
from benchmark.application.interfaces.synthesis_read_repository import SynthesisReadRepository
from benchmark.application.trials.audit import BenchmarkAuditService
from benchmark.application.trials.coordinator import BenchmarkCoordinator
from benchmark.infra.di import BenchmarkProvider
from evolution.application.campaign.models import CampaignTask
from evolution.application.campaign.run import SynthesisCampaignCoordinator
from evolution.application.interfaces.code_store import SynthesisCodeStore
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.synthesis_engine import SynthesisEngine
from evolution.application.interfaces.task_dispatcher import TaskDispatcher
from evolution.application.synthesis.models import SessionResult
from evolution.application.synthesis.run import SingleSynthesisUseCase
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.infra.di import EvolutionProvider
from evolution.infra.llm.client import LLMClient
from shared.domain.interfaces.problem_factory import ProblemFactory
from shared.infra.di import SharedProvider, container_scope
from shared.infra.problems.factory import BBOBProblemFactory


@pytest.mark.parametrize("context", ["synthesis", "benchmark", "analysis", "worker"])
@pytest.mark.parametrize("interrupted", [False, True])
def test_container_disposes_database_on_success_and_failure(monkeypatch, context, interrupted):
    database = MagicMock()
    monkeypatch.setattr(shared_di, "Database", lambda: database)
    monkeypatch.setattr(benchmark_di, "ChampionsReadRepository", MagicMock())
    dependency = {
        "synthesis": SynthesisCampaignCoordinator,
        "worker": SingleSynthesisUseCase,
        "analysis": AnalyzeEcdfAndConvergence,
        "benchmark": BenchmarkCoordinator,
    }[context]
    provider = EvolutionProvider() if context in {"synthesis", "worker"} else BenchmarkProvider()
    manager = container_scope(
        provider,
        context={LLMClient: MagicMock()},
        request_context={SynthesisEngine: MagicMock(), BenchmarkConfig: BenchmarkConfig()},
    )

    def resolve():
        with manager as scope:
            service = scope.get(dependency)
            assert isinstance(service, dependency)
            database.dispose.assert_not_called()
            if interrupted:
                raise RuntimeError("interrupted")

    if interrupted:
        with pytest.raises(RuntimeError, match="interrupted"):
            resolve()
    else:
        resolve()
    database.dispose.assert_called_once_with()


@pytest.mark.parametrize(
    "provider,repository,dependency",
    [
        (EvolutionProvider, "SQLiteSynthesisRepository", SynthesisCampaignCoordinator),
        (BenchmarkProvider, "SQLiteSynthesisReadRepository", BenchmarkCoordinator),
    ],
)
def test_repository_construction_failure_still_disposes_database(
    monkeypatch, provider, repository, dependency
):
    database = MagicMock()
    monkeypatch.setattr(shared_di, "Database", lambda: database)
    module = evolution_di if provider is EvolutionProvider else benchmark_di
    monkeypatch.setattr(
        getattr(module, repository), "__init__", MagicMock(side_effect=RuntimeError("construction"))
    )
    with pytest.raises(RuntimeError, match="construction"):
        with container_scope(
            provider(), context={LLMClient: MagicMock()}, request_context={}
        ) as container:
            container.get(dependency)
    database.dispose.assert_called_once()


def test_request_scopes_isolate_workflows_and_share_only_the_application_engine(monkeypatch):
    database = MagicMock()
    create_database = MagicMock(return_value=database)
    monkeypatch.setattr(shared_di, "Database", create_database)
    repository = MagicMock(return_value=None)
    monkeypatch.setattr(evolution_di.SQLiteSynthesisRepository, "__init__", repository)
    root = make_container(SharedProvider(), EvolutionProvider(), context={LLMClient: MagicMock()})
    try:
        with root() as request:
            first = request.get(SynthesisCampaignCoordinator)
            assert request.get(SynthesisCampaignCoordinator) is first
        database.dispose.assert_not_called()
        with root() as request:
            second = request.get(SynthesisCampaignCoordinator)
            assert first is not second
            assert first.logger is not second.logger
        create_database.assert_called_once()
        assert repository.call_count == 2
    finally:
        root.close()
    database.dispose.assert_called_once()


def test_unused_container_does_not_open_database(monkeypatch):
    create_database = MagicMock()
    monkeypatch.setattr(shared_di, "Database", create_database)
    with container_scope(BenchmarkProvider(), context={}, request_context={}):
        pass
    create_database.assert_not_called()


def test_analysis_settings_are_job_scoped_not_application_globals(monkeypatch):
    database = MagicMock()
    monkeypatch.setattr(shared_di, "Database", lambda: database)
    monkeypatch.setattr(benchmark_di, "ChampionsReadRepository", MagicMock())
    first_settings = BenchmarkConfig(budget=100_000)
    second_settings = BenchmarkConfig(budget=200_000)
    root = make_container(SharedProvider(), BenchmarkProvider())
    try:
        with root(context={BenchmarkConfig: first_settings}) as request:
            first = request.get(AnalyzeEcdfAndConvergence)
            assert first.loader.config is first_settings
        with root(context={BenchmarkConfig: second_settings}) as request:
            second = request.get(AnalyzeEcdfAndConvergence)
            assert second.loader.config is second_settings
            assert second is not first
            assert second.loader is not first.loader
        assert first.loader.config.budget == 100_000
    finally:
        root.close()
    database.dispose.assert_called_once()


def test_worker_resolves_the_supplied_engine_without_an_llm_connection(monkeypatch):
    database = MagicMock()
    monkeypatch.setattr(shared_di, "Database", lambda: database)
    engine = MagicMock(spec=SynthesisEngine)
    with evolution_di.synthesis_worker_scope(engine) as use_case:
        assert use_case.engine is engine
    database.dispose.assert_called_once()


def test_nested_workflows_have_ready_collaborators_and_independent_lifetimes(monkeypatch):
    outer_db, inner_db = MagicMock(), MagicMock()
    monkeypatch.setattr(shared_di, "Database", MagicMock(side_effect=[outer_db, inner_db]))
    monkeypatch.setattr(benchmark_di, "ChampionsReadRepository", MagicMock())
    with container_scope(BenchmarkProvider(), context={}, request_context={}) as outer_scope:
        outer = outer_scope.get(BenchmarkCoordinator)
        assert outer_scope.get(BenchmarkAuditService).workload is outer.workload
        with container_scope(BenchmarkProvider(), context={}, request_context={}) as inner_scope:
            inner = inner_scope.get(BenchmarkCoordinator)
            assert inner is not outer
            assert inner.logger is not outer.logger
        inner_db.dispose.assert_called_once()
        outer_db.dispose.assert_not_called()
    outer_db.dispose.assert_called_once()


def test_direct_class_bindings_share_instances_with_their_interfaces(monkeypatch):
    database = MagicMock()
    monkeypatch.setattr(shared_di, "Database", lambda: database)
    root = make_container(
        SharedProvider(), EvolutionProvider(), BenchmarkProvider(), context={LLMClient: MagicMock()}
    )
    try:
        with root() as request:
            bindings = (
                (SynthesisRepository, evolution_di.SQLiteSynthesisRepository),
                (BaseLogger, evolution_di.SynthesisLogger),
                (SynthesisCodeStore, evolution_di.CodeRepository),
                (SynthesisReadRepository, benchmark_di.SQLiteSynthesisReadRepository),
                (ChampionRepository, benchmark_di.ChampionsReadRepository),
                (BenchmarkLoggerInterface, benchmark_di.BenchmarkLogger),
                (ProblemFactory, BBOBProblemFactory),
                (BenchmarkStateStore, benchmark_di.BenchmarkStateRepository),
                (CandidateCodeReader, benchmark_di.FilesystemCodeReader),
                (
                    TaskDispatcher[CampaignTask, SessionResult],
                    evolution_di.ProcessPoolRunner[CampaignTask, SessionResult],
                ),
            )
            for interface, implementation in bindings:
                assert request.get(interface) is request.get(implementation)
            engine = request.get(evolution_di.LLaMEAEngine)
            assert engine.code_repo is request.get(SynthesisCodeStore)
            selection = request.get(benchmark_di.ChampionSelectionService)
            assert selection.champions_repo is request.get(ChampionRepository)
    finally:
        root.close()
    database.dispose.assert_called_once()


def test_non_web_composition_can_replace_an_external_interface(monkeypatch):
    """A console/worker composition root can override an adapter, with no HTTP machinery."""

    class UnavailableCodeReader(CandidateCodeReader):
        def exists(self, code_path: str | Path) -> bool:
            return False

        def read(self, code_path: str | Path) -> str:
            raise FileNotFoundError(code_path)

    database = MagicMock()
    monkeypatch.setattr(shared_di, "Database", lambda: database)
    replacements = Provider(scope=Scope.REQUEST)
    replacements.provide(UnavailableCodeReader, provides=CandidateCodeReader, override=True)
    root = make_container(SharedProvider(), BenchmarkProvider(), replacements)
    try:
        with root() as request:
            workload = request.get(benchmark_di.BenchmarkWorkload)
            assert isinstance(workload.code_reader, UnavailableCodeReader)
            assert workload.code_reader is request.get(CandidateCodeReader)
            assert workload.state_repo is request.get(BenchmarkStateStore)
            assert workload.sqlite_repo is request.get(SynthesisReadRepository)
        database.dispose.assert_not_called()
    finally:
        root.close()
    database.dispose.assert_called_once()


def test_reusable_providers_do_not_import_notebook_lifecycle():
    root = Path(__file__).resolve().parents[1] / "src"
    for package in ("shared", "evolution", "benchmark"):
        path = root / package / "infra" / "di.py"
        tree = ast.parse(path.read_text())
        imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]
        imports.extend(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert not any(name.endswith(".infra.notebook") for name in imports), path
        assert "atexit" not in imports, path
