"""Operational failures remain visible without becoming scientific observations."""

import ast
import io
import logging
import pickle
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest

from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.trials.workload import BenchmarkWorkload
from benchmark.infra.io.trace_repository import BenchmarkStateRepository, IOHTraceReader
from evolution.application.exceptions import OrchestrationError, ProviderError
from evolution.application.synthesis.candidate_evaluation import CandidateEvaluator
from evolution.domain.services.algorithm_scoring import AlgorithmScoringService
from evolution.infra.concurrency.process_worker_pool import ProcessWorkerPool
from evolution.infra.engines.llamea.runtime import FailureAwareLLaMEA
from evolution.infra.llm.client import LLMClient
from evolution.infra.logging import SynthesisLogger
from shared.application.errors import ArtifactError, StorageError
from shared.domain.problem import BaseProblem
from shared.infra.artifacts import atomic_write
from shared.infra.database import Database
from shared.infra.database.session import session_scope
from shared.infra.logging.runtime import LoggingRuntime, diagnostic_context


def test_logging_preserves_context_cause_and_secrets_without_duplicate_failure(tmp_path):
    console = io.StringIO()
    runtime = LoggingRuntime("analysis", tmp_path, console)
    try:
        with pytest.raises(RuntimeError, match="failed"):
            with runtime.operation("analysis"):
                with runtime.operation("nested"):
                    with diagnostic_context(experiment_id=7):
                        SynthesisLogger().info("progress row")
                        logging.getLogger("benchmark.reader").debug("Bearer private-key sk-secret")
                        try:
                            raise ValueError("original cause")
                        except ValueError as error:
                            raise RuntimeError("failed") from error
    finally:
        runtime.close()
    diagnostic = runtime.path.read_text()
    assert diagnostic.count("Operation failed:") == 1
    assert "original cause" in diagnostic
    assert "RuntimeError: failed" in diagnostic
    assert "experiment_id=7" in diagnostic
    assert "Bearer private-key" not in diagnostic
    assert "sk-secret" not in diagnostic
    assert "progress row" in console.getvalue()
    assert "original cause" not in console.getvalue()
    assert "\x1b[" not in diagnostic


def test_concurrent_hosts_do_not_steal_logs_or_handlers(tmp_path):
    root = logging.getLogger("benchmark")
    original = root.level, root.propagate, tuple(root.handlers)
    first = LoggingRuntime("audit", tmp_path, io.StringIO())
    second = LoggingRuntime("analysis", tmp_path, io.StringIO())
    with first.operation("audit"):
        logging.getLogger("benchmark.audit").info("first host only")
    with second.operation("analysis"):
        logging.getLogger("benchmark.analysis").info("second host only")
    first.close()
    with second.operation("analysis"):
        logging.getLogger("benchmark.analysis").info("second still active")
    second.close()
    assert (root.level, root.propagate, tuple(root.handlers)) == original
    assert "second host only" not in first.path.read_text()
    assert "first host only" not in second.path.read_text()
    assert "second still active" in second.path.read_text()


def test_console_coalesces_retries_but_file_retains_attempts(tmp_path):
    console = io.StringIO()
    runtime = LoggingRuntime("synthesis", tmp_path, console)
    with runtime.operation("synthesis"):
        for attempt in range(3):
            logging.getLogger("evolution.gateway").warning("Retry attempt %d", attempt)
    runtime.close()
    assert console.getvalue().count("Retry attempt") == 1
    assert runtime.path.read_text().count("Retry attempt") == 3


def test_unreadable_provenance_is_not_missing_and_audit_is_read_only(tmp_path):
    directory = tmp_path / "condition"
    directory.mkdir()
    provenance = directory / "provenance.json"
    provenance.write_text("{broken")
    repository = BenchmarkStateRepository(tmp_path)
    with pytest.raises(ArtifactError) as failure:
        repository.read_provenance(directory)
    assert failure.value.__cause__ is not None
    workload = BenchmarkWorkload(MagicMock(), MagicMock(), repository, MagicMock())
    status = workload.inspect_status(directory, config=BenchmarkConfig())
    assert status.status == "INVALID_ARTIFACT"
    assert status.reusable_trials == 0
    assert provenance.read_text() == "{broken"
    with pytest.raises(ArtifactError):
        IOHTraceReader(tmp_path).load_provenance_records()
    assert repository.read_provenance(tmp_path / "absent") is None


def test_failed_atomic_replace_keeps_original(tmp_path, monkeypatch):
    path = tmp_path / "result.json"
    path.write_text("original")
    monkeypatch.setattr(Path, "replace", MagicMock(side_effect=PermissionError("denied")))
    with pytest.raises(StorageError) as failure:
        atomic_write(path, b"new")
    assert isinstance(failure.value.__cause__, PermissionError)
    assert path.read_text() == "original"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["result.json"]


def test_database_failure_is_translated_with_original_cause(tmp_path):
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    try:
        with pytest.raises(StorageError) as failure:
            with session_scope(database.session_factory, "read experiments") as session:
                session.execute(text("SELECT * FROM missing_table"))
        assert isinstance(failure.value.__cause__, SQLAlchemyError)
        assert "read experiments" in str(failure.value)
    finally:
        database.dispose()


def test_llamea_cannot_turn_provider_failure_into_candidate_fitness(tmp_path, monkeypatch):
    monkeypatch.setenv("UPB_API_KEY", "fake-key")
    monkeypatch.setenv("UPB_MODEL", "gwdg.test")
    monkeypatch.setenv("UPB_REQUESTS_PER_MINUTE", "60000")
    monkeypatch.setenv("UPB_RATE_LIMIT_STATE", str(tmp_path / "limiter.sqlite3"))
    monkeypatch.setattr(
        httpx.HTTPTransport,
        "handle_request",
        lambda self, request: httpx.Response(401, json={"error": {"message": "denied"}}),
    )
    client = LLMClient("upb", validate_on_init=False)
    evaluator = MagicMock()
    engine = FailureAwareLLaMEA(
        f=evaluator,
        llm=client,
        budget=2,
        n_parents=1,
        n_offspring=1,
        log=False,
        max_workers=1,
        parallel_backend="sequential",
    )
    try:
        with pytest.raises(ProviderError) as failure:
            engine.initialize_single()
        assert failure.value.reason == "authentication"
        assert isinstance(failure.value.__cause__, Exception)
        evaluator.assert_not_called()
        assert engine.population == []
    finally:
        client.close()


def test_systemic_task_failure_stops_admission_and_keeps_successes(monkeypatch):
    import evolution.infra.concurrency.process_worker_pool as module

    submitted = []

    class Pool:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def submit(self, fn, item):
            submitted.append(item)
            future = Future()
            if item == 1:
                future.set_exception(ProviderError("timeout", "model", "request timed out"))
            else:
                future.set_result(item)
            return future

    monkeypatch.setattr(module, "ProcessPoolExecutor", Pool)
    with pytest.raises(OrchestrationError) as failure:
        ProcessWorkerPool(max_workers=2).execute(int, list(range(10)), str)
    assert submitted == [0, 1]
    assert failure.value.results == {"0": 0}
    assert isinstance(failure.value.__cause__, ProviderError)
    restored = pickle.loads(pickle.dumps(failure.value))
    assert restored.results == {"0": 0}
    assert restored.errors["1"].reason == "timeout"


def emit_worker_failure(value):
    logger = logging.getLogger("evolution.worker")
    try:
        raise ValueError("worker diagnostic cause")
    except ValueError:
        logger.warning("worker warning", exc_info=True)
    return value


def test_pool_logs_reach_parent_with_traceback(tmp_path):
    runtime = LoggingRuntime("synthesis", tmp_path, io.StringIO())
    try:
        with runtime.operation("pool"):
            assert ProcessWorkerPool(max_workers=1).execute(emit_worker_failure, [1], str) == {
                "1": 1
            }
    finally:
        runtime.close()
    assert "worker diagnostic cause" in runtime.path.read_text()
    assert "worker warning" in runtime.path.read_text()


def test_domain_never_configures_or_emits_operational_logs():
    root = Path(__file__).resolve().parents[1] / "src"
    violations = []
    for context in ("shared", "evolution", "benchmark"):
        for path in (root / context / "domain").rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Import) and any(
                    alias.name == "logging" for alias in node.names
                ):
                    violations.append(str(path))
                elif isinstance(node, ast.ImportFrom) and node.module == "logging":
                    violations.append(str(path))
                elif (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    violations.append(str(path))
    assert not violations


def test_backend_scoring_bug_is_not_an_optimizer_failure(monkeypatch):
    import numpy as np

    problem = MagicMock(spec=BaseProblem)
    problem.dim = 2
    problem.evaluations = 1
    problem.true_optimum = 0.0
    problem.eval_clean.return_value = 0.0
    problem.is_in_bounds.return_value = True
    executor = MagicMock()
    executor.execute_algorithm.return_value = np.zeros(2), 0.0
    executor.last_captured_warnings = []
    use_case = CandidateEvaluator(
        problem=problem, budget=100, timeout_seconds=30.0, executor=executor
    )
    monkeypatch.setattr(
        AlgorithmScoringService, "success", MagicMock(side_effect=RuntimeError("scoring defect"))
    )
    with pytest.raises(RuntimeError, match="scoring defect"):
        use_case.evaluate("generated source", "Optimizer")


def test_resource_cleanup_does_not_mask_construction_failure(monkeypatch):
    from contextlib import contextmanager

    import shared.infra.di as composition
    from shared.infra.lifecycle import WorkflowScope

    @contextmanager
    def failing_scope(*args, **kwargs):
        try:
            yield MagicMock(get=MagicMock(side_effect=ValueError("construction failure")))
        finally:
            raise RuntimeError("cleanup failure")

    monkeypatch.setattr(composition, "container_scope", failing_scope)
    scope = WorkflowScope(context={}, request_context={})
    with pytest.raises(ValueError, match="construction failure"):
        scope.get(str)
    scope.close()


def test_analysis_service_reports_without_a_notebook_wrapper(tmp_path):
    from benchmark.application.analysis.analyze_ecdf_and_convergence import (
        AnalyzeEcdfAndConvergence,
    )
    from benchmark.infra.logging import BenchmarkLogger

    console = io.StringIO()
    runtime = LoggingRuntime("analysis", tmp_path, console)
    try:
        with runtime.operation("setup"):
            logger = BenchmarkLogger()
        loader = MagicMock(load=MagicMock(side_effect=ArtifactError("unreadable provenance")))
        analysis = AnalyzeEcdfAndConvergence(loader, MagicMock(), logger)
        with pytest.raises(ArtifactError, match="unreadable provenance"):
            analysis.execute(mode="explicit", dims=None, problems=None, noise_stds=None)
    finally:
        runtime.close()
    assert runtime.path.read_text().count("Operation failed:") == 1
    assert "unreadable provenance" in runtime.path.read_text()
    assert "ECDF and convergence analysis" in console.getvalue()


def test_campaign_call_retains_worker_logging_without_a_notebook_wrapper(tmp_path, monkeypatch):
    from study_fixtures import run_parameters, synthesis_config

    from evolution.application.campaign.service import SynthesisCampaign
    from shared.infra.logging.runtime import current_runtime

    runtime = LoggingRuntime("synthesis", tmp_path, io.StringIO())
    try:
        with runtime.operation("setup"):
            logger = SynthesisLogger()
        worker_pool = MagicMock()

        def dispatch(**kwargs):
            assert current_runtime() is runtime
            return {}

        worker_pool.execute.side_effect = dispatch
        campaign = SynthesisCampaign(
            sqlite_repo=MagicMock(),
            logger=logger,
            engine=MagicMock(),
            model_name="test-model",
            problem_factory=MagicMock(),
            worker_pool=worker_pool,
            worker_fn=int,
            worker_count=1,
        )
        planner = MagicMock()
        planner.build_tasks.return_value = [{"key": "test"}]
        monkeypatch.setattr(campaign, "_build_planner", lambda config: planner)
        campaign.run(**run_parameters(synthesis_config()))
        worker_pool.execute.assert_called_once()
        assert current_runtime() is None
    finally:
        runtime.close()


def test_notebooks_do_not_expose_logging_operation_contexts():
    import json

    notebooks = Path(__file__).resolve().parents[1] / "notebooks"
    for path in notebooks.rglob("*.ipynb"):
        for cell in json.loads(path.read_text())["cells"]:
            if cell["cell_type"] == "code":
                assert "services.operation(" not in "".join(cell["source"]), str(path)
