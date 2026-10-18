"""Held-out instance migration preserves historical data and resumes only missing identities."""

import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from benchmarking.application.evaluation.trials import EvaluationTrialRunner
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.domain.evaluation import ERROR_DEFINITION, EVALUATION_SCHEMA_VERSION
from benchmarking.domain.services.condition_status import inspect_condition
from benchmarking.domain.trial_schedule import matching_trial_indices, select_scheduled_trials
from benchmarking.infra.io.trace_repository import EvaluationStateRepository, IOHTraceReader
from benchmarking.infra.storage.model_registry import configured_model_names
from shared.domain.problem import BaseProblem
from shared.infra.problems.factory import BBOBProblemFactory


def historical_record() -> dict[str, object]:
    return {
        "baseline": "pso",
        "problem_id": 1,
        "dim": 2,
        "noise_std": 0.0,
        "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
        "error_definition": ERROR_DEFINITION,
        "budget": 20_000,
        "instance_ids": list(range(1, 21)),
        "trial_seeds": list(range(43, 63)),
        "clean_errors": [float(i) for i in range(1, 21)],
        "best_objectives": [float(i) for i in range(1, 21)],
        "true_optima": [0.0] * 20,
        "runtimes": [0.01] * 20,
        "evaluations_used": [1] * 20,
        "n_runs": 20,
    }


def test_historical_twenty_runs_are_nineteen_reusable_held_out_trials() -> None:
    config = EvaluationConfig()
    record = historical_record()
    original = deepcopy(record)
    inspection = inspect_condition(
        code_available=True,
        directory_exists=True,
        provenance=record,
        expected_code_hash=None,
        expected_trials=20,
        expected_budget=20_000,
        trial_schedule=config.trial_schedule,
    )
    assert inspection.status == "PENDING"
    assert inspection.recorded_trials == 20
    assert inspection.reusable_trials == 19
    selected = select_scheduled_trials(record, config.trial_schedule)
    assert selected["instance_ids"] == list(range(2, 21))
    assert selected["clean_errors"] == list(range(2, 21))
    assert selected["n_runs"] == 19
    assert record == original
    assert config.trial_schedule[-1] == (21, 63)


def test_identity_selection_handles_gaps_wrong_seeds_duplicates_and_unknown_metadata() -> None:
    schedule = EvaluationConfig(target_eval_runs=3).trial_schedule
    record = {
        "instance_ids": [4, 2, 3, 2],
        "trial_seeds": [46, 44, 999, 44],
        "clean_errors": [0.0] * 4,
    }
    assert matching_trial_indices(record, schedule) == [0, 1]
    assert matching_trial_indices({"clean_errors": [0.0] * 20}, schedule) == []


def test_historical_unexecuted_tail_is_not_reused() -> None:
    record = historical_record()
    record["clean_errors"][19] = float("inf")
    record["runtimes"][19] = 0.0
    record["evaluations_used"][19] = 0
    assert len(matching_trial_indices(record, EvaluationConfig().trial_schedule)) == 18


@pytest.mark.parametrize("orphan", [False, True])
def test_append_only_instance_21_and_filter_ioh_traces(tmp_path: Path, orphan: bool) -> None:
    config = EvaluationConfig()
    state = EvaluationStateRepository(tmp_path / "ioh_traces")
    folder = state.eval_dir / "2D/std_0.0/f1/pso"
    folder.mkdir(parents=True)
    record = historical_record()
    state.write_provenance(folder, record)
    relative_dat = "data_f1_Sphere/IOHprofiler_f1_DIM2.dat"
    dat = folder / relative_dat
    dat.parent.mkdir()
    original_trace = "".join(f"evaluations raw_y\n1 {i}\n" for i in range(1, 21))
    dat.write_text(original_trace + ("evaluations raw_y\n1 999\n" if orphan else ""))
    (folder / "IOHprofiler_f1_Sphere.json").write_text(
        json.dumps(
            {
                "function_id": 1,
                "scenarios": [
                    {
                        "dimension": 2,
                        "path": relative_dat,
                        "runs": [{"instance": i, "evals": 1} for i in range(1, 21)]
                        + ([{"instance": 21, "evals": 1}] if orphan else []),
                    }
                ],
            }
        )
    )
    factory = MagicMock(wraps=BBOBProblemFactory())

    def baseline(problem: BaseProblem, budget: int) -> tuple[float, float, int]:
        point = np.zeros(problem.dim)
        problem(point)
        return problem.eval_clean(point), 0.01, problem.evaluations

    baseline_spy = MagicMock(side_effect=baseline)
    runner = EvaluationTrialRunner(
        state,
        MagicMock(),
        factory,
        MagicMock(),
        lambda _: baseline_spy,
        MagicMock(),
        configured_model_names(),
        config,
    )
    result = runner.run_baseline_trials("pso", 2, 0.0, 1, verbose=False)
    assert result["n_runs"] == 20
    factory.create.assert_called_once()
    assert factory.create.call_args.kwargs["instance_id"] == 21
    assert factory.create.call_args.kwargs["seed"] == 63
    saved = state.read_provenance(folder)
    assert saved["instance_ids"] == list(range(1, 22))
    assert saved["clean_errors"][:20] == record["clean_errors"]
    assert dat.read_text().startswith(original_trace)
    assert saved["trial_records"][-1]["trace_run_index"] == 20 + int(orphan)
    selected = select_scheduled_trials(saved, config.trial_schedule)
    assert selected["instance_ids"] == list(range(2, 22))
    assert result["clean_errors"] == selected["clean_errors"]
    traces = IOHTraceReader(state.eval_dir).load_evaluation_traces(
        trial_schedule=config.trial_schedule
    )
    runs = traces.get_runs(2, 0.0, 1, "pso")
    assert len(runs) == 20
    assert runs[0].raw_objectives.tolist() == [2.0]
    assert all(999 not in run.raw_objectives for run in runs)
    assert runner.run_baseline_trials("pso", 2, 0.0, 1, verbose=False)["status"] == "CACHED"
    assert baseline_spy.call_count == 1
