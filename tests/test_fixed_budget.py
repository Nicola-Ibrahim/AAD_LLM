"""Fixed objective-call allowances stay aligned across execution and analysis."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmarking.application.benchmark.trials import BenchmarkTrialRunner
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.infra.io.code_reader import FilesystemCodeReader
from benchmarking.infra.io.trace_repository import BenchmarkStateRepository
from benchmarking.infra.logging import BenchmarkLogger
from benchmarking.infra.solvers.baselines import get_baseline_runner
from benchmarking.infra.storage.benchmark_config_repository import BenchmarkConfigRepository
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.config import CONFIGS_DIR
from shared.infra.execution.candidate_executor import create_candidate_executor
from shared.infra.problems.factory import BBOBProblemFactory


def test_default_budget_is_fixed_and_non_optional() -> None:
    assert BenchmarkConfig().budget == 100_000
    with pytest.raises(ValidationError):
        BenchmarkConfig(budget=None)


@pytest.mark.parametrize("budget", [0, -1])
def test_invalid_fixed_budget_is_rejected(budget: int) -> None:
    with pytest.raises(ValidationError):
        BenchmarkConfig(budget=budget)


def test_nonempty_config_requires_an_explicit_fixed_budget(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.toml"
    path.write_text("[benchmarking]\ntrials_per_condition = 20\n", encoding="utf-8")
    with pytest.raises(ValueError, match="benchmarking.budget"):
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
