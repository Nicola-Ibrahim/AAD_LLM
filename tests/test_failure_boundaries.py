"""Fault injection at operational/scientific and cleanup boundaries; no live studies."""

import io
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from evolution.application.synthesis.candidate_evaluation import CandidateEvaluator
from evolution.infra.di import EvolutionProvider
from evolution.infra.storage.code.repository import FileCodeRepository
from shared.application.errors import StorageError
from shared.domain.problem import BaseProblem


def test_clean_backend_failure_is_not_candidate_failure():
    problem = MagicMock(spec=BaseProblem)
    problem.dim = 2
    problem.evaluations = 1
    problem.is_in_bounds.return_value = True
    problem.eval_clean.side_effect = RuntimeError("clean backend defect")
    executor = MagicMock()
    executor.execute_algorithm.return_value = np.zeros(2), 0.0
    executor.last_captured_warnings = []
    evaluation = CandidateEvaluator(problem=problem, executor=executor, budget=10)
    with pytest.raises(RuntimeError, match="clean backend defect"):
        evaluation.evaluate("generated source", "Optimizer")


def test_startup_error_survives_client_close_failure(monkeypatch):
    import evolution.infra.di as module

    client = MagicMock()
    primary = ValueError("probe failed")
    client.ping.side_effect = primary
    client.close.side_effect = RuntimeError("close failed")
    monkeypatch.setattr(module, "LLMClient", lambda *args: client)
    generator = EvolutionProvider(test_generation_on_startup=True).llm()
    with pytest.raises(ValueError, match="probe failed") as caught:
        next(generator)
    assert caught.value is primary
    assert any("close" in note.lower() for note in caught.value.__notes__)


def test_code_directory_failure_has_storage_context(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "mkdir", MagicMock(side_effect=PermissionError("denied")))
    with pytest.raises(StorageError) as caught:
        FileCodeRepository(tmp_path).save_code("source", 1, 7)
    assert isinstance(caught.value.__cause__, PermissionError)
    assert "experiment_7" in str(caught.value)


def test_optional_diagnostic_is_reported_by_outer_application(tmp_path):
    from shared.application.diagnostics import record_diagnostic
    from shared.infra.logging.runtime import LoggingRuntime

    runtime = LoggingRuntime("analysis", tmp_path, io.StringIO())
    try:
        with runtime.operation("outer"):
            with runtime.operation("inner"):
                record_diagnostic("Optional maintenance failed", RuntimeError("Bearer fake-secret"))
    finally:
        runtime.close()
    text = runtime.path.read_text()
    assert text.count("Optional maintenance failed") == 1
    assert "fake-secret" not in text
    assert "Operation failed:" not in text


def test_optional_diagnostic_stays_nonfatal_under_warnings_as_errors(caplog):
    import warnings

    from shared.application.diagnostics import record_diagnostic

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record_diagnostic("Optional WAL maintenance failed")
    assert "Optional WAL" in caplog.text


def test_successful_atomic_write_keeps_optional_cleanup_nonfatal(tmp_path, monkeypatch, caplog):
    from shared.infra.artifacts import atomic_write

    target = tmp_path / "result.json"
    monkeypatch.setattr(Path, "unlink", MagicMock(side_effect=PermissionError("unlink denied")))
    atomic_write(target, b"committed")
    assert target.read_bytes() == b"committed"
    assert "Cannot remove temporary artifact" in caplog.text


def test_clean_failure_and_invalid_return_remain_distinct():
    from shared.domain.solution import InvalidReturnedPoint, validate_returned_point

    problem = MagicMock(spec=BaseProblem)
    problem.dim = 2
    problem.is_in_bounds.side_effect = RuntimeError("bounds backend defect")
    with pytest.raises(RuntimeError, match="bounds backend defect"):
        validate_returned_point(problem, np.zeros(2))
    problem.is_in_bounds.side_effect = None
    problem.is_in_bounds.return_value = False
    with pytest.raises(InvalidReturnedPoint, match="outside search space bounds"):
        validate_returned_point(problem, np.zeros(2))


@pytest.mark.parametrize("incremental", [False, True])
def test_ioh_cleanup_preserves_body_error_and_surfaces_sole_close_failure(
    tmp_path, monkeypatch, incremental
):
    import benchmark.infra.io.trace_repository as module

    logger = MagicMock(close=MagicMock(side_effect=OSError("flush denied")))
    monkeypatch.setattr(module.ioh.logger, "Analyzer", lambda **kwargs: logger)
    store = module.BenchmarkStateRepository(tmp_path)
    target = tmp_path / "condition"
    primary = RuntimeError("trial backend failed")
    with pytest.raises(RuntimeError, match="trial backend failed") as failure:
        with store.open_run_logger(target, "optimizer", incremental):
            raise primary
    assert failure.value is primary
    assert any("IOH" in note for note in primary.__notes__)
    with pytest.raises(StorageError) as close_failure:
        with store.open_run_logger(target, "optimizer", incremental):
            pass
    assert isinstance(close_failure.value.__cause__, OSError)


def test_request_and_root_cleanup_do_not_mask_body_failure(monkeypatch):
    import shared.infra.di as module

    request = MagicMock(close=MagicMock(side_effect=RuntimeError("request teardown")))
    root = MagicMock(
        return_value=request, close=MagicMock(side_effect=RuntimeError("root teardown"))
    )
    monkeypatch.setattr(module, "make_container", lambda *args, **kwargs: root)
    primary = ValueError("workflow failed")
    with pytest.raises(ValueError) as failure:
        with module.container_scope(context={}, request_context={}):
            raise primary
    assert failure.value is primary
    assert len(primary.__notes__) == 2
    request.close.assert_called_once()
    root.close.assert_called_once()


def test_resolution_diagnostic_contains_secondary_cleanup_error(monkeypatch):
    from contextlib import contextmanager

    import shared.infra.di as composition
    from shared.infra.lifecycle import WorkflowScope

    @contextmanager
    def failing_scope(*args, **kwargs):
        try:
            yield MagicMock(get=MagicMock(side_effect=ValueError("construction failed")))
        finally:
            raise RuntimeError("secondary teardown defect")

    monkeypatch.setattr(composition, "container_scope", failing_scope)
    scope = WorkflowScope(context={}, request_context={})
    with pytest.raises(ValueError):
        scope.get(str)
    diagnostic = scope.logging.path.read_text()
    assert diagnostic.count("Operation failed:") == 1
    assert "secondary teardown defect" in diagnostic


def test_provider_diagnostic_hides_response_body_but_keeps_cause(tmp_path):
    import httpx
    import openai

    from evolution.infra.llm.gateway import provider_error
    from shared.infra.logging.runtime import LoggingRuntime

    request = httpx.Request("POST", "https://example.invalid/v1/chat/completions")
    original = openai.AuthenticationError(
        "private-response-marker",
        response=httpx.Response(401, request=request),
        body={"error": {"message": "private-response-marker"}},
    )
    translated = provider_error(original, "test-model")
    runtime = LoggingRuntime("evolution", tmp_path, io.StringIO())
    try:
        with pytest.raises(type(translated)) as caught:
            with runtime.operation("request"):
                raise translated from original
        assert caught.value.__cause__ is original
    finally:
        runtime.close()
    diagnostic = runtime.path.read_text()
    assert "private-response-marker" not in diagnostic
    assert "AuthenticationError" in diagnostic
    assert "check gateway credentials" in diagnostic


def test_tolerated_trace_rows_preserve_values_and_report_exclusions(tmp_path, caplog):
    from benchmark.infra.io.trace_repository import IOHTraceReader

    path = tmp_path / "IOHprofiler_f1.dat"
    path.write_text("evaluations raw_y\n1 3\n2 nan\nwrong value\nshort\n3 1\n")
    runs = IOHTraceReader.parse_dat_file(path)
    assert len(runs) == 1
    np.testing.assert_array_equal(runs[0].evaluations, [1, 2, 3])
    np.testing.assert_array_equal(runs[0].raw_objectives, [3, 3, 1])
    assert "Excluded 2 unusable trace rows" in caplog.text


def test_nonfinite_clean_return_keeps_runtime_penalty_and_traceback():
    problem = MagicMock(spec=BaseProblem)
    problem.dim = 2
    problem.evaluations = 1
    problem.is_in_bounds.return_value = True
    problem.eval_clean.return_value = float("nan")
    executor = MagicMock()
    executor.execute_algorithm.return_value = np.zeros(2), 0.0
    executor.last_captured_warnings = []
    result = CandidateEvaluator(problem=problem, executor=executor, budget=10).evaluate(
        "source", "Opt"
    )
    assert result.is_failure
    assert result.fitness_score == CandidateEvaluator.RUNTIME_FAILURE_FITNESS
    assert result.metadata.error.error_type == "ValueError"
    assert "Traceback" in result.metadata.error.error_traceback


def test_passive_wal_failure_is_nonfatal_after_commit(db_session_factory, monkeypatch, caplog):
    from contextlib import contextmanager

    import evolution.infra.storage.synthesis.repository as module

    @contextmanager
    def failed_checkpoint(*args, **kwargs):
        raise StorageError("passive checkpoint unavailable")
        yield

    repository = module.SQLiteSynthesisRepository(db_session_factory)
    monkeypatch.setattr(module, "session_scope", failed_checkpoint)
    repository.checkpoint_wal()
    assert "committed data remains stored" in caplog.text


@pytest.mark.parametrize("solver", ["run_cmaes", "run_de", "run_pso"])
def test_baseline_clean_backend_failure_remains_operational(solver):
    from test_candidate_evaluation import DummyProblem

    from benchmark.infra.solvers import baselines
    from shared.application.errors import ProblemEvaluationError

    problem = DummyProblem()
    problem.eval_clean = MagicMock(side_effect=RuntimeError("clean scoring defect"))
    with pytest.raises(ProblemEvaluationError) as caught:
        getattr(baselines, solver)(problem, 50)
    assert isinstance(caught.value.__cause__, RuntimeError)


def test_provider_worker_transport_retains_safe_cause_only(monkeypatch):
    from contextlib import contextmanager

    import httpx
    import openai

    import evolution.infra.di as composition
    from evolution.infra.concurrency.worker import run_synthesis_worker
    from evolution.infra.llm.gateway import provider_error
    from shared.infra.logging.exceptions import format_diagnostic_exception

    vendor = openai.AuthenticationError(
        "private-body-marker",
        response=httpx.Response(401, request=httpx.Request("POST", "https://example.invalid")),
        body={"message": "private-body-marker"},
    )

    def fail(**kwargs):
        raise provider_error(vendor, "test-model") from vendor

    @contextmanager
    def scope(engine):
        yield MagicMock(execute=fail)

    monkeypatch.setattr(composition, "synthesis_worker_scope", scope)
    item = dict(
        experiment_id=1,
        key="task",
        engine=object(),
        problem=object(),
        config=object(),
        prompt_strategy="baseline",
        synthesis_mode="explicit",
        initial_iteration=0,
    )
    from evolution.application.exceptions import ProviderError

    with pytest.raises(ProviderError) as caught:
        run_synthesis_worker(item)
    assert caught.value.reason == "authentication"
    assert caught.value.__cause__ is not vendor
    # Executor's transport uses ordinary traceback rendering, not our log formatter.
    import traceback

    transported = "".join(traceback.format_exception(caught.value))
    assert "private-body-marker" not in transported
    assert "AuthenticationError" in transported
    assert "AuthenticationError" in format_diagnostic_exception(caught.value)


def test_library_exception_events_do_not_duplicate_private_tracebacks(tmp_path):
    import logging

    from evolution.infra.engines.llamea.runtime import FailureAwareLLaMEA
    from shared.infra.logging.runtime import LoggingRuntime

    runtime = LoggingRuntime("evolution", tmp_path, io.StringIO())
    try:
        with runtime.operation("library"):
            try:
                raise RuntimeError("provider-private-message")
            except RuntimeError:
                FailureAwareLLaMEA.logevent(None, "rendered provider-private-message")
            logging.getLogger("evolution.test").info("safe progress")
    finally:
        runtime.close()
    assert "provider-private-message" not in runtime.path.read_text()
    assert "safe progress" in runtime.path.read_text()


def test_worker_initialization_drops_inherited_operation_buffer():
    import contextvars
    import logging

    from shared.application.diagnostics import (
        diagnostic_context,
        diagnostic_fields,
        record_diagnostic,
        report_operation,
        reset_process_diagnostics,
    )

    parent = MagicMock(spec=logging.Logger)
    child = MagicMock(spec=logging.Logger)
    with report_operation(parent, "parent"):
        with diagnostic_context(experiment_id=7):
            inherited = contextvars.copy_context()

            def initialize_child():
                reset_process_diagnostics()
                assert diagnostic_fields() == {}
                with report_operation(child, "child"):
                    record_diagnostic("child maintenance")

            inherited.run(initialize_child)
            assert diagnostic_fields() == {"operation": "parent", "experiment_id": 7}
    child.warning.assert_called_once_with("%s", "child maintenance")
    parent.warning.assert_not_called()


def test_public_application_returns_error_data_and_preserves_original_cause(tmp_path):
    from benchmark.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
    from benchmark.infra.logging import BenchmarkLogger
    from shared.infra.logging.runtime import LoggingRuntime

    cause = PermissionError("read denied")
    primary = StorageError("Cannot load recorded inputs")
    primary.__cause__ = cause
    runtime = LoggingRuntime("benchmark", tmp_path, io.StringIO())
    try:
        with runtime.operation("setup"):
            logger = BenchmarkLogger()
        service = AnalyzeNoiseRobustness(
            MagicMock(load=MagicMock(side_effect=primary)), MagicMock(), logger
        )
        outcome = service.execute(dims=None, problems=None, noise_stds=None)
        assert not outcome.is_success
        assert outcome.value is None
        assert outcome.error.code == "StorageError"
        assert outcome.error.diagnostic_log == str(runtime.path)
        assert outcome.error._original_exception is primary
        assert outcome.error._original_exception.__cause__ is cause
        public = outcome.model_dump(mode="json")
        assert "exception" not in public
        assert public["error"]["code"] == "StorageError"
    finally:
        runtime.close()
    assert runtime.path.read_text().count("Operation failed:") == 1


def test_application_cancellation_is_not_an_error_result():
    from benchmark.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
    from benchmark.infra.logging import BenchmarkLogger

    service = AnalyzeNoiseRobustness(
        MagicMock(load=MagicMock(side_effect=KeyboardInterrupt)), MagicMock(), BenchmarkLogger()
    )
    with pytest.raises(KeyboardInterrupt):
        service.execute(dims=None, problems=None, noise_stds=None)


def test_failed_notebook_calculation_does_not_export_stale_data(capsys):
    import json

    from shared.application.result import Result

    notebook = Path(__file__).resolve().parents[1] / "notebooks/analysis/07_noise_robustness.ipynb"
    cells = json.loads(notebook.read_text())["cells"]
    namespace = {
        "noise_analysis": MagicMock(
            execute=MagicMock(
                return_value=Result.failure("noise analysis", StorageError("unreadable inputs"))
            )
        ),
        "FILTER_DIMS": None,
        "FILTER_PROBLEMS": None,
        "FILTER_NOISE_STDS": None,
        "results_exporter": MagicMock(),
        "figure_exporter": MagicMock(),
        "noise": object(),
        "display": MagicMock(),
    }
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        if (
            "noise_result = noise_analysis.execute(" in source
            or "figure_exporter.export_noise_robustness(" in source
        ):
            exec(compile(source, str(notebook), "exec"), namespace)
    assert namespace["noise"] is None
    namespace["results_exporter"].save.assert_not_called()
    namespace["figure_exporter"].export_noise_robustness.assert_not_called()
    assert "unreadable inputs" in capsys.readouterr().out


def test_nested_result_failure_is_reported_once_with_diagnostic_path(tmp_path):
    from benchmark.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
    from benchmark.infra.logging import BenchmarkLogger
    from shared.infra.logging.runtime import LoggingRuntime

    runtime = LoggingRuntime("benchmark", tmp_path, io.StringIO())
    try:
        with runtime.operation("host request"):
            service = AnalyzeNoiseRobustness(
                MagicMock(load=MagicMock(side_effect=StorageError("unreadable inputs"))),
                MagicMock(),
                BenchmarkLogger(),
            )
            outcome = service.execute(dims=None, problems=None, noise_stds=None)
            assert not outcome.is_success
            assert outcome.error.diagnostic_log == str(runtime.path)
    finally:
        runtime.close()
    assert runtime.path.read_text().count("Operation failed:") == 1


def test_result_success_keeps_detached_data_and_rejects_mixed_outcome():
    from pydantic import ValidationError

    from shared.application.result import Result

    values = np.arange(3)
    outcome = Result.success(values)
    assert outcome.is_success
    assert outcome.value is values
    assert outcome.error is None
    with pytest.raises(ValidationError):
        Result(value=values, error=RuntimeError("mixed"))
