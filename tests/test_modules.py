"""Module-owned roots/scopes, with substitute use cases and no external campaigns."""

import os
import pickle
from collections.abc import Iterator
from unittest.mock import MagicMock

import pandas as pd
import pytest
from dishka import Provider, Scope, make_container
from study_fixtures import run_parameters, synthesis_config

import benchmark.infra.module as benchmark_module
import evolution.infra.module as evolution_module
import shared.infra.di as shared_di
from benchmark.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmark.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
from benchmark.application.analysis.analyze_performance import AnalyzePerformance
from benchmark.application.analysis.analyze_reliability import AnalyzeReliability
from benchmark.application.analysis.results import AnalysisProvenance, ProfileAnalysisResult
from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.trials.coordinator import BenchmarkCoordinator
from benchmark.infra.module import BenchmarkModule
from evolution.application.campaign.models import CampaignResults
from evolution.application.campaign.run import SynthesisCampaignCoordinator
from evolution.infra.module import EvolutionModule
from shared.infra.database import Database


@pytest.mark.parametrize("kind", ["evolution", "benchmark"])
def test_module_reuses_lazy_root_and_closes_operation_scopes_on_success_and_failure(
    monkeypatch, kind
):
    database = MagicMock()
    create_database = MagicMock(return_value=database)
    monkeypatch.setattr(shared_di, "Database", create_database)
    opened, closed = [], []
    fail_next = [False]
    result = CampaignResults() if kind == "evolution" else pd.DataFrame()
    dependency = SynthesisCampaignCoordinator if kind == "evolution" else BenchmarkCoordinator
    method_name = "run_campaign" if kind == "evolution" else "run_benchmarks"

    def service(database: Database):
        use_case = MagicMock(spec=dependency)

        def execute(**params):
            if fail_next[0]:
                raise ValueError("operation failed")
            return result

        getattr(use_case, method_name).side_effect = execute
        opened.append(use_case)
        try:
            yield use_case
        finally:
            closed.append(use_case)

    service.__annotations__["return"] = Iterator[dependency]
    replacements = Provider(scope=Scope.REQUEST)
    replacements.provide(service, override=True)
    target = evolution_module if kind == "evolution" else benchmark_module
    monkeypatch.setattr(
        target,
        "make_container",
        lambda *args, **kwargs: make_container(*args, replacements, **kwargs),
    )
    module = EvolutionModule(MagicMock()) if kind == "evolution" else BenchmarkModule()
    create_database.assert_not_called()
    payload = run_parameters(synthesis_config() if kind == "evolution" else BenchmarkConfig())
    method = getattr(module, method_name)
    try:
        assert method(**payload) is result
        assert method(**payload) is result
        assert closed == opened
        assert opened[0] is not opened[1]
        create_database.assert_called_once()
        for use_case in opened:
            supplied = getattr(use_case, method_name).call_args.kwargs
            assert all(supplied[key] == value for key, value in payload.items())
        fail_next[0] = True
        with pytest.raises(ValueError, match="operation failed"):
            method(**payload)
        assert closed == opened
        fail_next[0] = False
        assert method(**payload) is result
        database.dispose.assert_not_called()
    finally:
        module.close()
    module.close()
    database.dispose.assert_called_once()
    with pytest.raises(RuntimeError, match="closed"):
        method(**payload)


def test_analysis_settings_are_per_call_and_unrelated_workflows_do_not_run(monkeypatch):
    configurations, calls, finalized = [], [], []
    marker = object()
    replacements = Provider(scope=Scope.REQUEST)

    def make_factory(dependency):
        def build(config: BenchmarkConfig):
            configurations.append(config)
            use_case = MagicMock(spec=dependency)
            use_case.execute.side_effect = lambda **kwargs: (
                calls.append((dependency, kwargs)) or marker
            )
            try:
                yield use_case
            finally:
                finalized.append(dependency)

        build.__annotations__["return"] = Iterator[dependency]
        return build

    for dependency in (
        AnalyzeEcdfAndConvergence,
        AnalyzeReliability,
        AnalyzeNoiseRobustness,
        AnalyzePerformance,
    ):
        replacements.provide(make_factory(dependency), override=True)
    monkeypatch.setattr(
        benchmark_module,
        "make_container",
        lambda *args, **kwargs: make_container(*args, replacements, **kwargs),
    )
    module = BenchmarkModule()
    filters = dict(dims=[2], problems=[15], noise_stds=[0.1])
    try:
        assert (
            module.analyze_ecdf_and_convergence(mode="explicit", **filters, budget=1234) is marker
        )
        assert (
            module.analyze_reliability(
                **filters, budget=2345, primary_target=1e-6, bootstrap_samples=123
            )
            is marker
        )
        assert module.analyze_noise_robustness(**filters) is marker
        assert module.analyze_performance(**filters) is marker
    finally:
        module.close()
    assert len(calls) == len(finalized) == len(configurations) == 4
    assert [config.budget for config in configurations] == [1234, 2345, 100_000, 100_000]
    assert configurations[1].reliability.primary_target == 1e-6
    assert configurations[1].reliability.bootstrap_samples == 123
    assert calls[0][1] == {"mode": "explicit", **filters}
    assert all(args == filters for _, args in calls[1:])


def test_numerical_storage_is_separate_from_calculation_and_database(tmp_path, monkeypatch):
    create_database = MagicMock(side_effect=AssertionError("database not needed"))
    monkeypatch.setattr(shared_di, "Database", create_database)
    result = ProfileAnalysisResult("explicit", [], AnalysisProvenance({}, {}, {}, [], "empty"), ())
    module = BenchmarkModule(results_dir=tmp_path)
    try:
        path = module.save_analysis_results(result)
        loaded = module.load_analysis_results(path)
    finally:
        module.close()
    assert path.exists()
    assert loaded == result
    create_database.assert_not_called()


@pytest.mark.parametrize("kind", ["evolution", "benchmark"])
def test_modules_cannot_be_pickled_or_used_from_another_process(monkeypatch, kind):
    module = EvolutionModule(MagicMock()) if kind == "evolution" else BenchmarkModule()
    try:
        with pytest.raises(TypeError, match="worker tasks"):
            pickle.dumps(module)
        owner_pid = os.getpid()
        monkeypatch.setattr(os, "getpid", lambda: owner_pid + 1)
        module.close()
        with pytest.raises(RuntimeError, match="process-local"):
            with module._operation({}):
                pass
        monkeypatch.setattr(os, "getpid", lambda: owner_pid)
        assert not module._closed
    finally:
        module.close()
