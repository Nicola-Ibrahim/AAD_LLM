"""Transfer workflows tested without databases, IOH, generated subprocesses or LLMs."""

from contextlib import nullcontext
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
import json

from benchmarking.application.evaluation.run import EvaluationService
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.infra.storage.model_registry import configured_model_names
from benchmarking.infra.io.trace_repository import IOHTraceReader
from benchmarking.domain.evaluation import (
    EVALUATION_SCHEMA_VERSION,
    ERROR_DEFINITION,
)
from benchmarking.application.evaluation.audit import EvaluationAuditService, SynthesisConditionSpec


def audit_for(service: EvaluationService) -> EvaluationAuditService:
    service.workload.sqlite_repo.get_synthesis_dataframes.return_value = (
        pd.DataFrame(
            [
                {"status": "completed", "llm_name": "new-model"},
                {"status": "running", "llm_name": "not-completed"},
            ]
        ),
        pd.DataFrame(),
    )
    return EvaluationAuditService(
        service.workload,
        service.workload.sqlite_repo,
        (
            SynthesisConditionSpec(1, 2, 0.0, "explicit", "baseline"),
            SynthesisConditionSpec(1, 2, 0.0, "implicit", "baseline"),
        ),
    )


def test_audit_does_not_substitute_implicit_counts_or_count_synthesis_gaps(
    transfer_service: EvaluationService,
) -> None:
    service = transfer_service
    row = service.workload.audit_champions_workload().iloc[0]
    path = Path(row["target_dir"])
    service.trials.state_repo.records[path] = {
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "error_definition": ERROR_DEFINITION,
        "code_hash": "obsolete",
        "clean_errors": [0.0] * 20,
    }
    service.trials.state_repo.records[path.with_name(path.name + "_implicit")] = {
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "error_definition": ERROR_DEFINITION,
        "code_hash": row["code_hash"],
        "clean_errors": [0.0] * 20,
    }
    original = dict(service.trials.state_repo.records)
    snapshot = audit_for(service).get_audit_data()
    stale = snapshot.evaluations.loc[snapshot.evaluations["key"] == row["key"]].iloc[0]
    assert stale["status"] == "NEEDS_RERUN"
    assert stale["runs_found"] == 0
    assert stale["recorded_trials"] == 20
    assert snapshot.coverage_summary.completed_cells == 0
    assert snapshot.coverage_summary.synthesis_gap_cells == 1
    assert snapshot.coverage_summary.total_cells == len(snapshot.evaluations)
    assert snapshot.completed_models == ("new-model",)
    assert service.trials.state_repo.records == original


def test_audit_excludes_missing_code_and_keeps_baselines_without_models(
    transfer_service: EvaluationService,
) -> None:
    service = transfer_service
    audit = audit_for(service)
    service.workload.code_reader.exists.return_value = False
    snapshot = audit.get_audit_data()
    assert snapshot.coverage_summary.missing_code_cells > 0
    assert snapshot.coverage_summary.total_cells == int(snapshot.evaluations["eligible"].sum())
    service.workload.sqlite_repo.get_synthesis_dataframes.return_value = (
        pd.DataFrame(),
        pd.DataFrame(),
    )
    service.workload.sqlite_repo.get_target_conditions.return_value = []
    repo = service.workload.champion_selection.champions_repo
    repo.query_candidates.return_value = repo.query_candidates.return_value.iloc[:0]
    service.workload.planned_target_conditions = ((2, 0.0, 1),)
    snapshot = audit.get_audit_data()
    assert snapshot.completed_models == ()
    assert not snapshot.evaluations.empty
    assert set(snapshot.evaluations["solver_type"]) == {"baseline"}


def test_audit_notebook_runs_without_campaign(
    transfer_service: EvaluationService,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import bootstrap.audit
    import shared.config
    import plotly.graph_objects as go

    monkeypatch.setattr(bootstrap.audit, "build_audit_service", lambda: audit_for(transfer_service))
    monkeypatch.setattr(shared.config, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(go.Figure, "show", lambda self: None)
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "notebooks/04_audit.ipynb").read_text()
    )
    namespace = {"display": lambda value: None}
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            code = "".join(cell["source"])
            exec(compile(code, "04_audit.ipynb", "exec"), namespace)
    assert (tmp_path / "reports/evaluation_coverage_v2.csv").is_file()
    assert (tmp_path / "reports/synthesis_gaps_v1.csv").is_file()
    assert transfer_service.trials.state_repo.records == {}


class MemoryState:
    def __init__(self, root: Path) -> None:
        self.eval_dir = root / "ioh_traces"
        self.records: dict[Path, dict[str, object]] = {}

    def solver_directory_exists(self, path: Path) -> bool:
        return path in self.records

    def read_provenance(self, path: Path) -> dict[str, object] | None:
        return self.records.get(path)

    def write_provenance(self, path: Path, data: dict[str, object]) -> None:
        self.records[path] = data

    def open_run_logger(self, path: Path, algorithm: str, incremental: bool) -> nullcontext:
        return nullcontext(object())

    def remove_solver_traces(self, path: Path) -> None:
        self.records.pop(path, None)


class Problem:
    def __init__(self, problem_id: int) -> None:
        self.problem_id = problem_id
        self.true_optimum = 10.0 * problem_id
        self.evaluations = 0

    def attach_logger(self, logger: object) -> None:
        pass

    def set_budget(self, budget: int) -> None:
        self.budget = budget

    def eval_clean(self, x: np.ndarray) -> float:
        return self.true_optimum + float(x[0])

    def reset(self) -> None:
        pass


@pytest.fixture
def transfer_service(tmp_path: Path) -> EvaluationService:
    candidates = pd.DataFrame(
        [
            dict(
                llm_name="new-model",
                problem_id=source,
                dim=2,
                mode="explicit",
                noise_std=0.0,
                prompt_strategy="baseline",
                experiment_id=source,
                iteration_id=source,
                algorithm_name="Optimizer",
                final_error=0.1,
                evaluations_used=10,
                code_path=f"source_{source}.py",
            )
            for source in [1, 8]
        ]
    )
    champion_repo = MagicMock()
    champion_repo.query_candidates.return_value = candidates
    synthesis_repo = MagicMock()
    synthesis_repo.get_target_conditions.return_value = [(2, 0.0, 1), (2, 0.05, 1)]
    code_reader = MagicMock()
    code_reader.exists.return_value = True
    code_reader.read.side_effect = lambda path: f"frozen code {path.name}"
    problem_factory = MagicMock()
    problem_factory.create.side_effect = lambda **kwargs: Problem(kwargs["problem_id"])
    executor = MagicMock()

    def execute(**kwargs: object) -> tuple[np.ndarray, float]:
        kwargs["problem"].evaluations += 1
        return np.array([0.001, 0.0]), -999.0

    executor.execute_algorithm.side_effect = execute
    baseline = MagicMock(side_effect=lambda problem, budget: (problem.true_optimum + 0.01, 0.1, 1))
    return EvaluationService(
        sqlite_repo=synthesis_repo,
        champions_repo=champion_repo,
        state_repo=MemoryState(tmp_path),
        config=EvaluationConfig(
            target_eval_runs=3,
            cross_function_enabled=True,
            cross_function_problem_ids=[1, 8],
            classical_baselines=["pso"],
        ),
        logger=MagicMock(),
        problem_factory=problem_factory,
        executor_factory=lambda timeout: executor,
        baseline_resolver=lambda slug: baseline,
        code_reader=code_reader,
        model_names=configured_model_names(),
    )


def test_frozen_target_execution_pairing_and_baseline_reuse(
    transfer_service: EvaluationService,
) -> None:
    service = transfer_service
    rows = service.run_cross_function_evaluations(verbose=False)
    assert len(rows) == 6  # Four source-target pairs; two shared baselines.
    records = service.trials.state_repo.records
    transfer = [r for r in records.values() if "code_hash" in r]
    assert len(transfer) == 4
    for record in transfer:
        assert record["clean_errors"] == pytest.approx([0.001] * 3)
        assert record["true_optima"] == [record["target_problem_id"] * 10.0] * 3
        assert record["instance_ids"] == [1, 2, 3]
        assert record["trial_seeds"] == [43, 44, 45]
        assert record["source_noise_std"] == record["target_noise_std"] == 0.0
    assert len([r for r in records.values() if "baseline" in r]) == 2
    assert all(
        "cross_function_traces" in str(p)
        for p, r in records.items()
        if r.get("evaluation_kind") == "cross_function"
    )
    assert len([r for r in records.values() if r.get("evaluation_kind") == "native"]) == 2
    executor = service.trials.executor_factory(1)
    assert {c.kwargs["code"] for c in executor.execute_algorithm.call_args_list} == {
        "frozen code source_1.py",
        "frozen code source_8.py",
    }
    count = executor.execute_algorithm.call_count
    cached = service.run_cross_function_evaluations(verbose=False)
    assert set(cached["status"]) == {"CACHED"}
    assert executor.execute_algorithm.call_count == count


def test_failure_does_not_skip_later_instances(transfer_service: EvaluationService) -> None:
    service = transfer_service
    executor = service.trials.executor_factory(1)
    executor.execute_algorithm.side_effect = [
        RuntimeError("first"),
        RuntimeError("second"),
        (np.array([0.0, 0.0]), 123.0),
    ]
    champion = next(iter(service.champion_selection.flatten_champions().values()))
    result = service.trials.run_champion_trials(champion, target_problem_id=8, verbose=False)
    assert executor.execute_algorithm.call_count == 3
    assert result["clean_errors"] == [float("inf"), float("inf"), 0.0]


def test_native_diagonals_are_reused_without_reexecution(
    transfer_service: EvaluationService,
) -> None:
    service = transfer_service
    service.run_champions(verbose=False)
    executor = service.trials.executor_factory(1)
    before = executor.execute_algorithm.call_count
    rows = service.run_cross_function_evaluations(verbose=False)
    assert (
        executor.execute_algorithm.call_count == before + 6
    )  # Two off-diagonal pairs × three trials.
    assert len(rows[rows["status"] == "CACHED"]) == 2


def test_historical_skipped_tail_resumes(transfer_service: EvaluationService) -> None:
    service = transfer_service
    champion = next(iter(service.champion_selection.flatten_champions().values()))
    service.trials.run_champion_trials(champion, target_problem_id=8, verbose=False)
    record = next(iter(service.trials.state_repo.records.values()))
    record["clean_errors"][2] = float("inf")
    record["runtimes"][2] = 0.0
    record["evaluations_used"][2] = 0
    executor = service.trials.executor_factory(1)
    count = executor.execute_algorithm.call_count
    service.trials.run_champion_trials(champion, target_problem_id=8, verbose=False)
    assert executor.execute_algorithm.call_count == count + 1
    assert executor.execute_algorithm.call_args.kwargs["problem"].problem_id == 8
    assert record["instance_ids"] == [1, 2, 3]


def test_workflow_flags_and_baseline_targets(transfer_service: EvaluationService) -> None:
    service = transfer_service
    service.config.cross_eval_clean_champions = False
    assert service.workload.audit_noise_robustness_workload().empty
    service.config.cross_function_enabled = False
    assert service.workload.audit_cross_function_workload().empty
    assert service.run_cross_function_evaluations().empty
    service.config.cross_function_enabled = True
    assert set(service.workload.audit_workload("cross_function")["problem_id"]) == {1, 8}
    service.config.cross_function_problem_ids = [8]
    # Restricting transfer targets must not remove each champion's native reference.
    assert set(service.workload.audit_cross_function_workload()["problem_id"]) == {1, 8}


def test_transfer_aggregation_missing_and_reproducibility() -> None:
    records = [
        dict(
            model="new-model",
            strategy="baseline",
            dim=2,
            noise_std=0.0,
            source_problem_id=source,
            problem_id=target,
            clean_errors=errors,
        )
        for source, target, errors in [
            (1, 1, [0.0] * 3),
            (1, 8, [0.0] * 3),
            (8, 1, [1.0] * 3),
            (8, 8, [1.0]),
        ]
    ]
    engine = TransferAnalysisEngine()
    table = engine.condition_table(records, expected_trials=3)
    aggregate = engine.aggregate_transfer(table)
    assert aggregate.iloc[0]["Conditions"] == 2
    assert aggregate.iloc[0]["Success Rate"] == 0.5
    pd.testing.assert_frame_equal(aggregate, engine.aggregate_transfer(table))
    assert not table.iloc[3]["Complete"]


def test_noise_records_require_identical_champion_code() -> None:
    common = dict(
        model="new-model",
        strategy="baseline",
        dim=2,
        problem_id=1,
        solver_folder="new_model_baseline",
        code_hash="same",
    )
    clean = dict(common, noise_std=0.0)
    matched = dict(common, noise_std=0.05)
    changed = dict(common, noise_std=0.1, code_hash="different")
    adapted = dict(common, noise_std=0.2, solver_folder="new_model_baseline_noisy")
    assert TransferAnalysisEngine.frozen_noise_records([clean, matched, changed, adapted]) == [
        clean,
        matched,
    ]


def test_invalid_transfer_targets_rejected() -> None:
    with pytest.raises(ValueError):
        EvaluationConfig(cross_function_problem_ids=[0, 25])


def test_reader_excludes_skipped_tail_but_retains_actual_prequery_failure(tmp_path: Path) -> None:
    folder = tmp_path / "2D" / "std_0.0" / "f1" / "pso"
    folder.mkdir(parents=True)
    provenance = dict(
        evaluation_schema_version=EVALUATION_SCHEMA_VERSION,
        error_definition=ERROR_DEFINITION,
        dim=2,
        problem_id=1,
        noise_std=0.0,
        baseline="pso",
        clean_errors=[float("inf"), 0.0, float("inf")],
        runtimes=[0.01, 0.02, 0.0],
        evaluations_used=[0, 10, 0],
    )
    (folder / "provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
    reader = IOHTraceReader(tmp_path)
    assert reader.get_run_count(folder) == 2
    assert reader.load_provenance_records()[0]["n_runs"] == 2
    runs = reader.load_evaluation_traces().get_runs(2, 0.0, 1, "pso")
    assert len(runs) == 1  # Actual zero-query failure, not the absent finite-result trace.
    assert not runs[0].is_success()
