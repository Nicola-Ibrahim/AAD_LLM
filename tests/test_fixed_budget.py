"""Fixed objective-call allowances stay aligned across execution and analysis."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmarking.application.benchmark.models import RecordedTrial
from benchmarking.application.benchmark.trials import BenchmarkTrialRunner
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import BenchmarkStateRepository
from benchmarking.infra.logging import BenchmarkLogger
from benchmarking.infra.solvers.baselines import get_baseline_runner
from benchmarking.infra.storage.benchmark_config_repository import BenchmarkConfigRepository
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.application.interfaces.candidate_executor import (
    CANDIDATE_EXECUTION_VERSION,
    CandidateTimeout,
)
from shared.config import CONFIGS_DIR
from shared.domain.problem import BaseProblem
from shared.infra.execution.candidate_executor import create_candidate_executor
from shared.infra.problems.factory import BBOBProblemFactory


def test_default_budget_is_fixed_and_non_optional() -> None:
    assert BenchmarkConfig().budget == 100_000
    with pytest.raises(ValidationError):
        BenchmarkConfig(budget=None)


@pytest.mark.parametrize(
    "setting",
    [
        'force_rerun = "false"',
        'budget = "100000"',
        "trials_per_condition = 20.0",
        "fill_missing_only = 1",
        'target_noise_stds = ["0.1"]',
    ],
)
def test_benchmark_loader_rejects_wrong_types(tmp_path: Path, setting: str) -> None:
    path = tmp_path / "benchmark.toml"
    budget = "" if setting.startswith("budget") else "budget = 100000\n"
    path.write_text(f"[benchmarking]\n{budget}{setting}\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        BenchmarkConfigRepository(path).load_config()


def test_reliability_settings_are_also_strict(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.toml"
    path.write_text(
        '[benchmarking]\nbudget=100000\n[benchmarking.reliability]\nbootstrap_samples="1000"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="bootstrap_samples"):
        BenchmarkConfigRepository(path).load_config()


def test_failure_diagnostics_survive_trial_resumption(tmp_path: Path) -> None:
    state = BenchmarkStateRepository(tmp_path / "traces")
    config = BenchmarkConfig(budget=10, trials_per_condition=2)
    runner = BenchmarkTrialRunner(
        state_repo=state,
        logger=BenchmarkLogger(verbose=False),
        problem_factory=BBOBProblemFactory(),
        executor_factory=create_candidate_executor,
        baseline_resolver=get_baseline_runner,
        code_reader=FilesystemCodeReader(tmp_path),
        model_names=ModelNames([]),
        config=config,
    )
    errors = iter([ValueError("invalid coordinates"), CandidateTimeout("time limit")])

    def fail(problem: BaseProblem, budget: int) -> tuple[float, float, int]:
        raise next(errors)

    directory = state.benchmark_dir / "2D/std_0.0/f1/test"
    metadata = {"baseline": "test", "candidate_execution_contract": CANDIDATE_EXECUTION_VERSION}
    runner._execute_trial_runs(directory, 2, 0.0, 1, "test", fail, metadata, verbose=False)
    original = state.read_provenance(directory)
    assert original["clean_errors"] == [float("inf")] * 2
    assert [r["error_type"] for r in original["trial_records"]] == [
        "ValueError",
        "CandidateTimeout",
    ]
    assert "invalid coordinates" in original["trial_records"][0]["error_traceback"]
    assert original["trial_records"][1]["error_traceback"] is None
    config.trials_per_condition = 3

    def succeed(problem: BaseProblem, budget: int) -> tuple[float, float, int]:
        return problem.true_optimum, 0.01, 0

    runner._execute_trial_runs(directory, 2, 0.0, 1, "test", succeed, metadata, verbose=False)
    resumed = state.read_provenance(directory)
    assert resumed["trial_records"][:2] == original["trial_records"]
    assert resumed["trial_records"][2]["error_type"] is None
    assert resumed["clean_errors"] == [float("inf"), float("inf"), 0.0]
    resumed.pop("candidate_execution_contract")
    state.write_provenance(directory, resumed)
    config.trials_per_condition = 4
    with pytest.raises(ValueError, match="unknown execution contract"):
        runner._execute_trial_runs(directory, 2, 0.0, 1, "test", succeed, metadata, verbose=False)
    assert state.read_provenance(directory) == resumed


def test_legacy_trial_records_keep_sidecar_alignment_and_serialized_fields() -> None:
    trials = RecordedTrial.from_provenance(
        {
            "all_trials_executed": True,
            "clean_errors": [0.125, float("inf")],
            "instance_ids": [11, 12],
            "trial_seeds": [53, 54],
            "true_optima": [79.48, -24.0],
            "best_objectives": [79.605, float("inf")],
            "runtimes": [0.3, 0.1],
            "evaluations_used": [4, 0],
            "observed_objectives": [[{"evaluations": 4, "observed_y": 79.7}]],
            "trial_records": [{"trace_run_index": 0}],
        }
    )
    assert [trial.identity for trial in trials] == [(11, 53), (12, 54)]
    assert trials[0].observations == [{"evaluations": 4, "observed_y": 79.7}]
    assert trials[1].observations == []
    assert trials[0].provenance_row(1) == {
        "trial": 1,
        "instance_id": 11,
        "seed": 53,
        "true_optimum": 79.48,
        "best_objective": 79.605,
        "error": 0.125,
        "evaluations_used": 4,
        "trace_run_index": 0,
        "error_type": None,
        "error_message": None,
        "error_traceback": None,
    }
    assert trials[1].provenance_row(2) == {
        "trial": 2,
        "instance_id": 12,
        "seed": 54,
        "true_optimum": -24.0,
        "best_objective": float("inf"),
        "error": float("inf"),
        "evaluations_used": 0,
        "trace_run_index": None,
        "error_type": None,
        "error_message": None,
        "error_traceback": None,
    }


@pytest.mark.parametrize("budget", [0, -1])
def test_invalid_fixed_budget_is_rejected(budget: int) -> None:
    with pytest.raises(ValidationError):
        BenchmarkConfig(budget=budget)


def test_nonempty_config_requires_an_explicit_fixed_budget(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.toml"
    path.write_text("[benchmarking]\ntrials_per_condition = 20\n", encoding="utf-8")
    with pytest.raises(ValueError, match="benchmarking.budget"):
        BenchmarkConfigRepository(path).load_config()


def test_benchmark_section_must_be_a_table(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.toml"
    path.write_text("benchmarking = []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a TOML table"):
        BenchmarkConfigRepository(path).load_config()


def test_unknown_settings_are_rejected_by_the_model(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.toml"
    path.write_text("[benchmarking]\nbudget = 100000\nunknown_setting = 1\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="unknown_setting"):
        BenchmarkConfigRepository(path).load_config()


def test_config_loader_reads_fixed_budget_and_keeps_the_schedule(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.toml"
    path.write_text("[benchmarking]\nbudget = 100000\n", encoding="utf-8")
    config = BenchmarkConfigRepository(path).load_config()
    assert config.budget == 100_000
    assert config.trial_schedule == tuple((instance, 42 + instance) for instance in range(2, 22))
    assert config.trial_timeout_seconds == 30.0


def test_project_configs_share_fixed_allowance_and_supported_dimensions() -> None:
    synthesis = SynthesisConfigRepository(CONFIGS_DIR / "synthesis.toml").load_config()
    benchmark = BenchmarkConfigRepository(CONFIGS_DIR / "benchmark.toml").load_config()
    assert synthesis.budget == benchmark.budget == 100_000
    selected_dimensions = {condition.dim for condition in synthesis.matrix_conditions}
    assert selected_dimensions
    assert selected_dimensions <= {2, 10, 50}


@pytest.mark.parametrize(
    ("condition", "expected_model", "expected_modes"),
    [
        ("{std = 0.0}", "none", {"explicit", "implicit"}),
        ("{std = 0.1}", "heteroscedastic", {"explicit", "implicit"}),
        ('{std = 0.1, model = "awgn"}', "awgn", {"explicit", "implicit"}),
        (
            '{std = 0.1, noise_model = "homoscedastic_additive", model = "awgn"}',
            "homoscedastic_additive",
            {"explicit", "implicit"},
        ),
        ('{std = 0.1, mode = "IMPLICIT"}', "heteroscedastic", {"implicit"}),
    ],
)
def test_synthesis_noise_configuration_preserves_resolution(
    tmp_path: Path, condition: str, expected_model: str, expected_modes: set[str]
) -> None:
    path = tmp_path / "synthesis.toml"
    path.write_text(
        "[matrix]\nproblem_targets = [{id = 15, dimensions = [10]}]\n"
        f'noise_conditions = [{condition}]\nprompt_strategies = "baseline"\n',
        encoding="utf-8",
    )
    config = SynthesisConfigRepository(path).load_config()
    assert len(config.noise_conditions) == 1
    assert config.noise_conditions[0].noise_model.value == expected_model
    assert {item.mode.value for item in config.matrix_conditions} == expected_modes
    assert {item.strategy.value for item in config.matrix_conditions} == {"baseline"}


@pytest.mark.parametrize("dim", [2, 10, 50])
def test_fixed_trial_budget_is_recorded_cached_and_invalidated(tmp_path: Path, dim: int) -> None:
    """Use tiny isolated PSO runs, never historical artifacts or LLM requests."""
    config = BenchmarkConfig(budget=120, trials_per_condition=2)
    runner = BenchmarkTrialRunner(
        state_repo=BenchmarkStateRepository(benchmark_dir=tmp_path / "traces"),
        logger=BenchmarkLogger(verbose=False),
        problem_factory=BBOBProblemFactory(),
        executor_factory=create_candidate_executor,
        baseline_resolver=get_baseline_runner,
        code_reader=FilesystemCodeReader(tmp_path),
        model_names=ModelNames([]),
        config=config,
    )
    result = runner.run_baseline_trials(dim=dim, noise_std=0.0, p_id=1, baseline_slug="pso")
    path = tmp_path / "traces" / f"{dim}D" / "std_0.0/f1/pso/provenance.json"
    provenance = json.loads(path.read_text())
    assert result["status"] == "SUCCESS"
    assert provenance["budget"] == 120
    assert provenance["evaluations_used"] == [120, 120]
    assert provenance["instance_ids"] == [2, 3]
    assert (
        runner.run_baseline_trials(dim=dim, noise_std=0.0, p_id=1, baseline_slug="pso")["status"]
        == "CACHED"
    )

    config.budget = 150
    assert (
        runner.run_baseline_trials(dim=dim, noise_std=0.0, p_id=1, baseline_slug="pso")["status"]
        == "SUCCESS"
    )
    assert json.loads(path.read_text())["budget"] == 150
