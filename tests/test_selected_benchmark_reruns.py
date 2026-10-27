"""Explicit benchmark reruns preserve other trials, provenance and trace identities."""

import json
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from study_fixtures import run_parameters

from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.trials.coordinator import BenchmarkCoordinator
from benchmark.application.trials.runner import BenchmarkTrialRunner
from benchmark.domain.benchmark_results import (
    BENCHMARK_SCHEMA_VERSION,
    CHAMPION_RETURN_VALIDATION_VERSION,
    ERROR_DEFINITION,
)
from benchmark.infra.io.trace_repository import BenchmarkStateRepository, IOHTraceReader
from shared.application.interfaces.candidate_executor import (
    CANDIDATE_EXECUTION_VERSION,
    CandidateTimeout,
)


def condition_record() -> dict[str, object]:
    errors = [float("inf"), 0.1, float("inf"), float("inf"), float("inf")]
    kinds = ["CandidateTimeout", None, "CandidateTimeout", "ValueError", "CandidateTimeout"]
    return {
        "model": "test-model",
        "candidate_execution_contract": CANDIDATE_EXECUTION_VERSION,
        "return_validation_version": CHAMPION_RETURN_VALIDATION_VERSION,
        "evaluation_schema_version": BENCHMARK_SCHEMA_VERSION,
        "error_definition": ERROR_DEFINITION,
        "code_hash": "current",
        "budget": 100_000,
        "n_runs": 5,
        "all_trials_executed": True,
        "instance_ids": list(range(2, 7)),
        "trial_seeds": list(range(44, 49)),
        "clean_errors": errors,
        "best_objectives": errors.copy(),
        "true_optima": [0.0] * 5,
        "runtimes": [30.0, 1.0, 30.0, 0.1, 120.0],
        "evaluations_used": [100_000, 100_000, 500, 100_000, 100_000],
        "observed_objectives": [[] for _ in range(5)],
        "trial_records": [
            {
                "trial": i + 1,
                "instance_id": i + 2,
                "seed": i + 44,
                "true_optimum": 0.0,
                "best_objective": errors[i],
                "error": errors[i],
                "evaluations_used": 500 if i == 2 else 100_000,
                "trace_run_index": i,
                "error_type": kind,
                "error_message": "old diagnostic" if kind else None,
                "error_traceback": None,
                **({"execution_timeout_seconds": 120.0} if i == 4 else {}),
            }
            for i, kind in enumerate(kinds)
        ],
    }


@pytest.mark.parametrize("times_out_again", [False, True])
def test_explicit_rerun_replaces_all_scheduled_trials_and_preserves_history(times_out_again):
    original = condition_record()
    original["previous_trial_attempts"] = [original["trial_records"][0].copy()]
    state = MagicMock()
    state.solver_directory_exists.return_value = True
    state.read_provenance.return_value = deepcopy(original)
    state.get_trace_run_count.side_effect = [5, 10]
    state.open_run_logger.side_effect = lambda *a: nullcontext(object())
    state.write_provenance.side_effect = lambda path, data: setattr(
        state.read_provenance, "return_value", deepcopy(data)
    )
    problem = MagicMock(true_optimum=0.0, evaluations=100_000)
    problem.observation_samples.return_value = []
    factory = MagicMock()
    factory.create.return_value = problem
    execute = MagicMock(return_value=(0.001, 31.0, 100_000))
    if times_out_again:
        execute.side_effect = CandidateTimeout("Execution exceeded 120 seconds")
    runner = BenchmarkTrialRunner(
        state, MagicMock(), factory, MagicMock(), MagicMock(), MagicMock()
    )
    config = BenchmarkConfig(trials_per_condition=5, trial_timeout_seconds=120.0)

    def run(rerun=True):
        return runner._execute_trial_runs(
            Path("condition"),
            10,
            0.0,
            15,
            "test",
            execute,
            {"model": "test-model", "candidate_execution_contract": CANDIDATE_EXECUTION_VERSION},
            expected_code_hash="current",
            config=config,
            rerun=rerun,
        )

    assert run()["n_runs"] == 5
    assert [call.kwargs["instance_id"] for call in factory.create.call_args_list] == [2, 3, 4, 5, 6]
    assert [call.kwargs["seed"] for call in factory.create.call_args_list] == [44, 45, 46, 47, 48]
    saved = state.read_provenance.return_value
    assert saved["before_selected_rerun"] == original
    assert saved["previous_trial_attempts"] == original["previous_trial_attempts"]
    for index in range(5):
        assert (
            saved["before_selected_rerun"]["trial_records"][index]["error_type"]
            == original["trial_records"][index]["error_type"]
        )
        assert saved["before_selected_rerun"]["trial_records"][index]["trace_run_index"] == index
        assert saved["trial_records"][index]["trace_run_index"] == 5 + index
        assert saved["trial_records"][index]["execution_timeout_seconds"] == 120.0
    assert run()["status"] == "SUCCESS"
    assert execute.call_count == 10
    assert state.read_provenance.return_value["before_selected_rerun"] == saved
    assert (
        state.read_provenance.return_value["before_selected_rerun"]["before_selected_rerun"]
        == original
    )
    assert run(rerun=False)["status"] == "CACHED"
    assert execute.call_count == 10
    state.remove_solver_traces.assert_not_called()


def coordinator_fixture():
    workload, runner = MagicMock(), MagicMock()
    task = SimpleNamespace(
        champion={"problem_id": 15, "experiment_id": 11},
        inspection=SimpleNamespace(reason="complete", status="COMPLETED"),
        target_dir=Path("condition"),
        solver_type="champion",
        dim=10,
        noise_std=0.0,
        problem_id=15,
        display_name="test",
        mode="explicit",
        strategy="baseline",
        solver="test_solver",
        model="test",
        key="test",
    )
    workload.discover.return_value = [
        task,
        SimpleNamespace(**(vars(task) | {"champion": {"problem_id": 15, "experiment_id": 22}})),
        SimpleNamespace(**(vars(task) | {"champion": None, "solver_type": "baseline"})),
        SimpleNamespace(**(vars(task) | {"solver_type": "noise_robustness"})),
    ]
    workload.state_repo.read_provenance.return_value = condition_record()
    runner.run_champion_trials.return_value = {"status": "SUCCESS", "n_runs": 5}
    return BenchmarkCoordinator(workload, runner, {}, MagicMock()), task


@pytest.mark.parametrize("ids", [[11], [11, 11]])
def test_coordinator_reruns_selected_completed_experiment_only(ids):
    coordinator, task = coordinator_fixture()
    config = BenchmarkConfig(trials_per_condition=5, trial_timeout_seconds=120.0)
    coordinator.run_benchmarks(
        **run_parameters(config),
        rerun_experiment_ids=ids,
    )
    coordinator.trials.run_champion_trials.assert_called_once()
    assert coordinator.trials.run_champion_trials.call_args.args[0] is task.champion
    assert coordinator.trials.run_champion_trials.call_args.kwargs["rerun"] is True
    coordinator.trials.run_baseline_trials.assert_not_called()


@pytest.mark.parametrize(
    "selection",
    [
        {"rerun_experiment_ids": [999]},
        {"rerun_experiment_ids": [-1]},
        {"rerun_experiment_ids": [True]},
        {"rerun_experiment_ids": [11], "force_rerun": True},
    ],
)
def test_invalid_rerun_selection_does_not_start_trials(selection):
    coordinator, _ = coordinator_fixture()
    config = BenchmarkConfig(trials_per_condition=5)
    with pytest.raises(ValueError):
        coordinator.run_benchmarks(**(run_parameters(config) | selection))
    coordinator.trials.run_champion_trials.assert_not_called()
    coordinator.trials.run_baseline_trials.assert_not_called()


@pytest.mark.parametrize("reason", ["partial", "stale_champion", "missing_code"])
def test_explicit_rerun_refuses_incompatible_results(reason):
    coordinator, task = coordinator_fixture()
    task.inspection = SimpleNamespace(reason=reason, status="PENDING")
    with pytest.raises(ValueError, match="compatible"):
        coordinator.run_benchmarks(
            **run_parameters(BenchmarkConfig(trials_per_condition=5)),
            rerun_experiment_ids=[11],
        )
    coordinator.trials.run_champion_trials.assert_not_called()


def test_other_workflows_are_skipped_during_selected_native_reruns():
    coordinator, _ = coordinator_fixture()
    for solver_type in ("baselines", "noise_robustness", "cross_function"):
        result = coordinator.run_benchmarks(
            **run_parameters(BenchmarkConfig()),
            rerun_experiment_ids=[11],
            solver_type=solver_type,
        )
        assert result.empty
    coordinator.workload.discover.assert_not_called()


def test_failed_provenance_write_preserves_previous_results(tmp_path):
    state = BenchmarkStateRepository(tmp_path)
    folder = tmp_path / "condition"
    original = condition_record()
    state.write_provenance(folder, original)
    with pytest.raises(TypeError):
        state.write_provenance(folder, {"unserializable": object()})
    assert state.read_provenance(folder) == original
    assert [p.name for p in folder.iterdir()] == ["provenance.json"]


@pytest.mark.parametrize("replace_all", [False, True])
def test_reader_uses_retry_trace_once_and_ignores_the_preserved_original(tmp_path, replace_all):
    state = BenchmarkStateRepository(tmp_path)
    folder = tmp_path / "2D/std_0.0/f1/test"
    record = condition_record()
    record.update(dim=2, noise_std=0.0, problem_id=1)
    record["trial_records"][0]["trace_run_index"] = 5
    values = [1, 2, 3, 4, 5, 999]
    instances = [2, 3, 4, 5, 6, 2]
    expected = [[2.0], [3.0], [4.0], [5.0], [999.0]]
    if replace_all:
        for index, row in enumerate(record["trial_records"]):
            row["trace_run_index"] = 5 + index
        values = list(range(1, 11))
        instances = [2, 3, 4, 5, 6] * 2
        expected = [[float(value)] for value in range(6, 11)]
    state.write_provenance(folder, record)
    dat = folder / "runs.dat"
    dat.write_text("".join(f"evaluations raw_y\n1 {value}\n" for value in values))
    (folder / "IOHprofiler_f1_Sphere.json").write_text(
        json.dumps(
            {
                "function_id": 1,
                "scenarios": [
                    {
                        "dimension": 2,
                        "path": dat.name,
                        "runs": [{"instance": i, "evals": 1} for i in instances],
                    }
                ],
            }
        )
    )
    dataset = IOHTraceReader(tmp_path).load_benchmark_traces(
        trial_schedule=BenchmarkConfig(trials_per_condition=5).trial_schedule
    )
    runs = dataset.get_runs(2, 0.0, 1, f"{record['model']} / {record.get('strategy', 'baseline')}")
    assert len(runs) == 5
    assert [run.raw_objectives.tolist() for run in runs] == expected
