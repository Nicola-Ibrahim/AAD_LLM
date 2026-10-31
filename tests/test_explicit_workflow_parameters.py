"""The same flat parameters work for notebooks and a future validated HTTP body."""

import ast
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from study_fixtures import run_parameters, synthesis_config

from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.trials.coordinator import BenchmarkCoordinator
from evolution.application.campaign.service import SynthesisCampaign
from evolution.application.campaign.settings import CampaignSettings
from shared.infra.cpu import available_cpu_count


def synthesis_service() -> SynthesisCampaign:
    return SynthesisCampaign(
        sqlite_repo=MagicMock(),
        logger=MagicMock(),
        engine=MagicMock(),
        model_name="connected-model",
        problem_factory=MagicMock(),
        worker_pool=MagicMock(),
        worker_fn=MagicMock(),
        worker_count=4,
    )


def test_synthesis_json_parameters_preserve_matrix_and_session_settings() -> None:
    original = synthesis_config()
    payload = json.loads(json.dumps(run_parameters(original)))
    resolved = CampaignSettings(**payload)
    assert resolved.matrix_conditions == original.matrix_conditions
    assert len(resolved.matrix_conditions) == 480
    assert resolved.synthesis_settings(iterations=10) == original.synthesis_settings(iterations=10)
    assert set(payload) == {
        "problem_targets",
        "noise_conditions",
        "synthesis_modes",
        "iterations",
        "budget",
        "timeout_seconds",
        "runs_per_config",
        "auto_resume",
        "skip_completed",
        "retry_failed_synthesis",
    }


def test_synthesis_parameters_are_local_to_each_call() -> None:
    service = synthesis_service()
    payload = run_parameters(synthesis_config())
    plans = []

    def planner(config: CampaignSettings) -> SimpleNamespace:
        plans.append(config)
        return SimpleNamespace(build_tasks=lambda **selection: [])

    service._build_planner = planner
    service.run(**payload).value
    service.run(**(payload | {"budget": 200_000})).value
    assert [config.budget for config in plans] == [100_000, 200_000]
    assert plans[0] is not plans[1]
    assert payload["budget"] == 100_000
    assert service.worker_count == 4
    assert service.model_name == "connected-model"
    service.worker_pool.execute.assert_not_called()
    service.sqlite_repo.create_experiment.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"budget": 0},
        {"budget": "100000"},
        {"budget": True},
        {"timeout_seconds": float("inf")},
        {"iterations": 0},
        {"problem_targets": [{"id": 15, "dimensions": ["10"]}]},
        {"noise_conditions": [{"std": -0.1, "noise_model": "heteroscedastic"}]},
        {"max_workers": 16},
        {"model_name": "untrusted-model"},
        {"recover": True, "resume_experiment_ids": [1]},
        {"rerun_experiment_ids": [True]},
    ],
)
def test_invalid_synthesis_inputs_never_dispatch_or_write(changes: dict[str, object]) -> None:
    service = synthesis_service()
    payload = run_parameters(synthesis_config()) | changes
    try:
        result = service.run(**payload)
    except ValidationError:
        # Wrong call shapes/types are rejected by the existing method signature validator.
        pass
    else:
        assert not result.is_success
        assert isinstance(result.error._original_exception, (ValueError, ValidationError))
    service.worker_pool.execute.assert_not_called()
    service.sqlite_repo.create_experiment.assert_not_called()


def test_benchmark_json_parameters_are_validated_and_not_retained() -> None:
    workload = MagicMock()
    workload.discover.return_value = []
    trials = MagicMock()
    service = BenchmarkCoordinator(
        workload, trials, {"pso": "Particle Swarm Optimization"}, MagicMock()
    )
    original = BenchmarkConfig()
    payload = json.loads(json.dumps(run_parameters(original)))
    service.run_benchmarks(**payload, solver_type="champions").value
    service.run_benchmarks(**(payload | {"first_instance_id": 11}), solver_type="baselines").value
    configs = [call.kwargs["config"] for call in workload.discover.call_args_list]
    assert configs[0].trial_schedule == original.trial_schedule
    assert configs[0].budget == original.budget
    assert configs[0].trial_timeout_seconds == original.trial_timeout_seconds
    assert configs[0].classical_baselines == original.classical_baselines
    assert [instance for instance, _ in configs[1].trial_schedule] == list(range(11, 31))
    assert configs[0] is not configs[1]
    assert "reliability" not in payload
    assert "model_name" not in payload
    trials.run_champion_trials.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"budget": 0},
        {"budget": "100000"},
        {"budget": True},
        {"trials_per_condition": 0},
        {"first_instance_id": 0},
        {"trial_timeout_seconds": float("inf")},
        {"classical_baselines": ["unknown"]},
        {"cross_function_problem_ids": [99]},
        {"solver_type": "unknown"},
    ],
)
def test_invalid_benchmark_inputs_fail_before_discovery(changes: dict[str, object]) -> None:
    workload = MagicMock()
    trials = MagicMock()
    service = BenchmarkCoordinator(workload, trials, {}, MagicMock())
    try:
        result = service.run_benchmarks(**(run_parameters(BenchmarkConfig()) | changes))
    except ValidationError:
        pass
    else:
        assert not result.is_success
        assert isinstance(result.error._original_exception, ValidationError)
    workload.discover.assert_not_called()
    trials.run_champion_trials.assert_not_called()


def test_worker_capacity_uses_affinity_and_scheduler(monkeypatch: pytest.MonkeyPatch) -> None:
    import shared.infra.cpu as cpu

    monkeypatch.setattr(cpu.os, "process_cpu_count", lambda: 32, raising=False)
    monkeypatch.setattr(cpu.os, "sched_getaffinity", lambda _: set(range(16)), raising=False)
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "8")
    assert available_cpu_count() == 8
    monkeypatch.delenv("SLURM_CPUS_PER_TASK")
    assert available_cpu_count() == 16
    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "invalid")
    assert available_cpu_count() == 16


def test_public_execution_dependencies_are_not_study_configuration() -> None:
    for service in (SynthesisCampaign, BenchmarkCoordinator):
        assert "config" not in inspect.signature(service).parameters
    assert "max_workers" not in inspect.signature(SynthesisCampaign.run).parameters
    assert "model_name" not in inspect.signature(SynthesisCampaign.run).parameters


def test_benchmark_composition_injects_concrete_workflows(monkeypatch: pytest.MonkeyPatch) -> None:
    import benchmark.infra.di as composition
    import shared.infra.di

    database = MagicMock()
    monkeypatch.setattr(shared.infra.di, "Database", lambda: database)
    monkeypatch.setattr(composition, "ChampionsReadRepository", MagicMock())
    with shared.infra.di.container_scope(
        composition.BenchmarkProvider(), context={}, request_context={}
    ) as scope:
        workflow = scope.get(BenchmarkCoordinator)
        assert isinstance(workflow.workload, composition.BenchmarkWorkload)
        assert isinstance(workflow.trials, composition.BenchmarkTrialRunner)
        assert not hasattr(workflow, "workload_factory")
        assert not hasattr(workflow.workload, "config")
        assert not hasattr(workflow.trials, "config")
    database.dispose.assert_called_once()


def test_synthesis_composition_gets_model_from_client_not_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import evolution.infra.di as composition
    import shared.infra.di

    database = MagicMock()
    client = MagicMock()
    client.model.name = "live-server-model"
    monkeypatch.setattr(shared.infra.di, "Database", lambda: database)
    monkeypatch.setattr(composition, "available_cpu_count", lambda: 6)
    with shared.infra.di.container_scope(
        composition.EvolutionProvider(), context={composition.LLMClient: client}, request_context={}
    ) as scope:
        workflow = scope.get(SynthesisCampaign)
        assert workflow.model_name == "live-server-model"
        assert workflow.worker_count == workflow.worker_pool.max_workers == 6
    database.dispose.assert_called_once()


def test_notebook_study_parameters_are_executable_and_preserve_the_protocol() -> None:
    root = Path(__file__).resolve().parents[1]
    synthesis_notebook = json.loads((root / "notebooks/02_synthesis.ipynb").read_text())
    synthesis_calls = [
        node
        for cell in synthesis_notebook["cells"]
        if cell["cell_type"] == "code"
        for node in ast.walk(ast.parse("".join(cell["source"])))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and (node.func.value.id, node.func.attr) in {("campaign", "run"), ("audit", "inspect")}
    ]
    assert len(synthesis_calls) == 2
    synthesis_configurations = []
    for call in synthesis_calls:
        assert all(kw.arg is not None for kw in call.keywords)
        parameters = {
            kw.arg: eval(compile(ast.Expression(kw.value), "02_synthesis.ipynb", "eval"))
            for kw in call.keywords
            if kw.arg in CampaignSettings.model_fields
        }
        synthesis_configurations.append(CampaignSettings(**parameters))
    synthesis = synthesis_configurations[0]
    assert synthesis_configurations[1] == synthesis
    notebook = json.loads((root / "notebooks/03_benchmark.ipynb").read_text())
    code = "\n".join("".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code")
    tree = ast.parse(code)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "benchmark_coordinator"
    ]
    assert calls
    assert not any(
        isinstance(node, ast.Name) and node.id in {"benchmark_parameters", "benchmark_reruns"}
        for node in ast.walk(tree)
    )
    configurations = []
    for call in calls:
        assert all(kw.arg is not None for kw in call.keywords)
        parameters = {
            kw.arg: ast.literal_eval(kw.value)
            for kw in call.keywords
            if kw.arg in BenchmarkConfig.model_fields
        }
        configurations.append(BenchmarkConfig(**parameters))
        if call.func.attr == "run_benchmarks":
            ids = next(
                (
                    ast.literal_eval(kw.value)
                    for kw in call.keywords
                    if kw.arg == "rerun_experiment_ids"
                ),
                [],
            )
            assert all(type(identifier) is int and identifier > 0 for identifier in ids)
    benchmark = configurations[0]
    assert all(c == benchmark for c in configurations)
    assert synthesis.budget == benchmark.budget == 100_000
    assert synthesis.dimensions == [2, 10, 50]
    assert len(synthesis.matrix_conditions) == 480
    assert benchmark.trial_schedule == tuple((instance, 42 + instance) for instance in range(2, 22))
    assert synthesis.timeout_seconds == 30.0
    assert benchmark.trial_timeout_seconds == 60.0
    assert not hasattr(benchmark, "timeout_retry")
    assert not benchmark.force_rerun


def test_study_loaders_and_conversion_helpers_are_removed() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "configs/synthesis.toml").exists()
    assert not (root / "configs/benchmark.toml").exists()
    assert not hasattr(CampaignSettings, "run_parameters")
    assert not hasattr(BenchmarkConfig, "run_parameters")
    for path in (root / "src").rglob("*.py"):
        source = path.read_text()
        assert "SynthesisConfigRepository" not in source
        assert "BenchmarkConfigRepository" not in source
