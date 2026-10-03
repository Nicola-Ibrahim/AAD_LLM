"""Application orchestration preserves domain mathematics without IO or Plotly."""

import hashlib
import inspect
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from benchmarking.application.analysis.analyze_ecdf_and_convergence import AnalyzeEcdfAndConvergence
from benchmarking.application.analysis.analyze_noise_robustness import AnalyzeNoiseRobustness
from benchmarking.application.analysis.analyze_performance import AnalyzePerformance
from benchmarking.application.analysis.analyze_reliability import AnalyzeReliability
from benchmarking.application.analysis.data_loader import AnalysisDataLoader, AnalysisSnapshot
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.domain.evaluation import (
    CHAMPION_RETURN_VALIDATION_VERSION,
    ERROR_DEFINITION,
    EVALUATION_SCHEMA_VERSION,
)
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.resolvers import ModelNames
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace


@pytest.fixture
def snapshot() -> AnalysisSnapshot:
    dataset = EvaluationDataset()
    for dim in [2, 5]:
        for noise in [0.0, 0.05, 0.1]:
            for problem in [1, 8]:
                for solver in [
                    "Model / baseline",
                    "Model / baseline (noise-adapted)",
                    "Model / baseline (noise-implicit)",
                    "PSO",
                ]:
                    for terminal in [0.0, 0.02]:
                        dataset.add_run(
                            EvaluationCondition(dim=dim, noise_std=noise, problem_id=problem),
                            solver,
                            RunTrace(
                                evaluations=np.array([1, 5, 10]),
                                raw_objectives=np.array([10.0, 2.0, terminal]),
                            ),
                        )
    records = []
    for noise in [0.0, 0.05, 0.1]:
        records.append(
            dict(
                model="raw-model",
                strategy="baseline",
                problem_id=1,
                source_problem_id=1,
                dim=2,
                noise_std=noise,
                clean_errors=[0.0, 0.02],
                n_runs=2,
                code_hash="same",
                solver_folder="model_baseline",
                evaluation_kind="native" if noise == 0 else "noise_robustness",
            )
        )
    return AnalysisSnapshot(
        {"raw-model": "Model"},
        {"model_baseline": "Model / baseline"},
        EvaluationConfig(target_eval_runs=2),
        dataset,
        {"Model": [s for s in dataset.solvers if " / " in s]},
        {"Model": "model"},
        dataset.solvers,
        ["PSO"],
        [records[0]],
        records,
        [],
        [],
        records,
        {"dims": None, "problems": None, "noise_stds": None},
    )


def loader_for(snapshot: AnalysisSnapshot) -> MagicMock:
    loader = MagicMock()
    loader.load.return_value = snapshot
    return loader


@pytest.mark.parametrize("mode", ["explicit", "implicit", "comparison"])
def test_profiles_match_existing_calculations_and_load_once(snapshot, mode):
    loader = loader_for(snapshot)
    engine = EcdfConvergenceEngine()
    spy = MagicMock(wraps=engine)
    result = AnalyzeEcdfAndConvergence(loader, spy).execute(
        mode=mode, dims=None, problems=None, noise_stds=None
    )
    loader.load.assert_called_once()
    assert spy.compute_trajectory_and_ecdf.call_count == sum(
        len(c.series) for c in result.conditions
    )
    for condition in result.conditions:
        for series in condition.series:
            runs = snapshot.dataset.get_runs(
                condition.dim, condition.noise_std, series.problem_id, series.solver
            )
            # Independent stepwise interpolation oracle, not retired access wrappers.
            values = []
            for run in runs:
                incumbent = np.minimum.accumulate(run.raw_objectives)
                values.append(
                    [
                        incumbent[run.evaluations <= checkpoint][-1]
                        if np.any(run.evaluations <= checkpoint)
                        else np.inf
                        for checkpoint in condition.evaluations
                    ]
                )
            values = np.asarray(values)
            for name, expected in [
                ("median", np.median(values, axis=0)),
                ("q25", np.percentile(values, 25, axis=0)),
                ("q75", np.percentile(values, 75, axis=0)),
            ]:
                np.testing.assert_array_equal(getattr(series, name), expected)
            expected_ecdf = np.mean(
                values[:, :, None] <= condition.targets[None, None, :], axis=(0, 2)
            )
            np.testing.assert_array_equal(series.ecdf, expected_ecdf)


def test_reliability_matches_bootstrap_and_preserves_raw_csv_identifiers(snapshot):
    result = AnalyzeReliability(
        loader_for(snapshot), TransferAnalysisEngine(), ReliabilityEngine()
    ).execute(dims=None, problems=None, noise_stds=None)
    assert result.native.iloc[0]["Model"] == "raw-model"
    assert result.primary.iloc[0]["Model"] == "Model"
    runs = snapshot.dataset.get_runs(2, 0.0, 1, "Model / baseline")
    rel = snapshot.config.reliability
    expected = ReliabilityEngine().compute_attainment_band(
        runs, result.evaluations, rel.primary_target, rel.bootstrap_samples, rel.bootstrap_seed
    )
    series = next(s for s in result.attainment if not s.baseline)
    for actual, expected_values in zip([series.probability, series.lower, series.upper], expected):
        np.testing.assert_array_equal(actual, expected_values)


def test_noise_and_performance_match_domain_services(snapshot):
    filters = dict(dims=None, problems=None, noise_stds=None)
    transfer = TransferAnalysisEngine()
    noise = AnalyzeNoiseRobustness(loader_for(snapshot), transfer).execute(**filters)
    rel = snapshot.config.reliability
    expected = transfer.condition_table(
        transfer.frozen_noise_records(snapshot.noise_records),
        rel.primary_target,
        rel.secondary_target,
        snapshot.config.target_eval_runs,
    )
    pd.testing.assert_frame_equal(noise.conditions, expected)
    pd.testing.assert_frame_equal(
        noise.aggregate,
        transfer.aggregate_noise(
            expected, rel.primary_prompt_strategy, rel.bootstrap_samples, rel.bootstrap_seed
        ),
    )
    performance = AnalyzePerformance(
        loader_for(snapshot), EcdfConvergenceEngine(), PerformanceMetricsEngine()
    ).execute(**filters)
    engine = EcdfConvergenceEngine()
    expected = engine.compute_auc_ecdf_matrix(
        snapshot.dataset, snapshot.solver_order, targets=performance.targets, group_by="condition"
    )
    pd.testing.assert_frame_equal(performance.table.drop(columns="Canonical Solver"), expected)
    for summary in performance.hardness:
        for noise, table in summary.tables.items():
            pd.testing.assert_frame_equal(
                table,
                PerformanceMetricsEngine().compute_hardness_success_rates(
                    snapshot.dataset, summary.dim, summary.solvers, noise_level=noise
                ),
            )


def test_missing_trace_is_not_a_zero_profile(snapshot):
    result = AnalyzeEcdfAndConvergence(loader_for(snapshot), EcdfConvergenceEngine()).execute(
        mode="explicit", dims=None, problems=None, noise_stds=None
    )
    assert all(s.solver != "CMA-ES" for c in result.conditions for s in c.series)
    assert any("CMA-ES" in message for message in result.diagnostics)


def test_empty_inputs_return_explicit_empty_results(snapshot):
    empty = replace(
        snapshot,
        dataset=EvaluationDataset(),
        native_records=[],
        noise_records=[],
        models_to_solvers={},
    )
    filters = dict(dims=None, problems=None, noise_stds=None)
    assert (
        not AnalyzeEcdfAndConvergence(loader_for(empty), EcdfConvergenceEngine())
        .execute(mode="explicit", **filters)
        .conditions
    )
    reliability = AnalyzeReliability(
        loader_for(empty), TransferAnalysisEngine(), ReliabilityEngine()
    ).execute(**filters)
    assert not reliability.attainment and reliability.diagnostics
    noise = AnalyzeNoiseRobustness(loader_for(empty), TransferAnalysisEngine()).execute(**filters)
    assert noise.aggregate.empty and noise.diagnostics
    performance = AnalyzePerformance(
        loader_for(empty), EcdfConvergenceEngine(), PerformanceMetricsEngine()
    ).execute(**filters)
    assert performance.table.empty and performance.diagnostics


def test_dependencies_are_required_and_mode_validated_before_loading():
    for cls in [
        AnalyzeEcdfAndConvergence,
        AnalyzeReliability,
        AnalyzeNoiseRobustness,
        AnalyzePerformance,
    ]:
        for name, param in inspect.signature(cls.__init__).parameters.items():
            if name != "self":
                assert param.default is inspect.Parameter.empty
    with pytest.raises(ValueError):
        AnalyzeEcdfAndConvergence(MagicMock(), EcdfConvergenceEngine()).execute(
            mode="invalid", dims=None, problems=None, noise_stds=None
        )


def test_bootstrap_disposes_on_use_case_failure(monkeypatch):
    import bootstrap.analysis

    database = MagicMock()
    monkeypatch.setattr(bootstrap.analysis, "Database", lambda: database)
    with pytest.raises(RuntimeError):
        with bootstrap.analysis.build_analysis_use_cases():
            raise RuntimeError("interrupted")
    database.dispose.assert_called_once()


@pytest.mark.parametrize(
    "state,expected_native",
    [
        ("complete", 1),
        ("partial", 1),
        ("failure", 1),
        ("stale_schema", 0),
        ("stale_hash", 0),
        ("missing_code", 0),
        ("stale_validation", 0),
        ("skipped_tail", 1),
    ],
)
def test_loader_eligibility_and_dynamic_models(state, expected_native):
    names = ModelNames([])
    raw = "NewModel-7B-Instruct"
    label = names.get_clean_model_label(raw)
    solver = names.resolve_folder_solver_name("NewModel-7B-Instruct_baseline")
    code = "candidate"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    dataset = EvaluationDataset()
    condition = EvaluationCondition(dim=2, noise_std=0.0, problem_id=1)
    dataset.add_run(
        condition, solver, RunTrace(evaluations=np.array([1]), raw_objectives=np.array([0.0]))
    )
    dataset.add_run(
        condition, "PSO", RunTrace(evaluations=np.array([1]), raw_objectives=np.array([0.0]))
    )
    record = dict(
        evaluation_schema_version=EVALUATION_SCHEMA_VERSION,
        return_validation_version=CHAMPION_RETURN_VALIDATION_VERSION,
        error_definition=ERROR_DEFINITION,
        evaluation_kind="native",
        model=raw,
        strategy="baseline",
        problem_id=1,
        dim=2,
        noise_std=0.0,
        code_hash=code_hash,
        solver_folder="NewModel-7B-Instruct_baseline",
        clean_errors=[0.0] * 20,
        n_runs=20,
    )
    if state == "partial":
        record["clean_errors"] = [0.0] * 2
    if state == "failure":
        record["clean_errors"] = [float("inf")] * 20
    if state == "skipped_tail":
        record.update(
            clean_errors=[float("inf")] * 20,
            runtimes=[0.1, 0.1] + [0.0] * 18,
            evaluations_used=[10, 10] + [0] * 18,
        )
    if state == "stale_schema":
        record["evaluation_schema_version"] = -1
    if state == "stale_hash":
        record["code_hash"] = "old"
    if state == "stale_validation":
        record["return_validation_version"] = -1
    baseline = dict(
        record,
        baseline="pso",
        solver_folder="pso",
        evaluation_schema_version=EVALUATION_SCHEMA_VERSION,
    )
    baseline.pop("model")
    baseline.pop("code_hash")
    reader = MagicMock()
    reader.load_evaluation_traces.return_value = dataset
    reader.load_provenance_records.return_value = [record, baseline]
    repository = MagicMock()
    repository.get_synthesis_dataframes.return_value = (
        pd.DataFrame([{"status": "completed", "llm_name": raw}]),
        pd.DataFrame(),
    )
    candidates = MagicMock()
    candidates.get_champions.return_value = {
        raw: {
            "condition": dict(
                llm_name=raw,
                problem_id=1,
                dim=2,
                mode="explicit",
                noise_std=0.0,
                prompt_strategy="baseline",
                code_path="candidate.py",
            )
        }
    }
    code_reader = MagicMock()
    code_reader.exists.return_value = state != "missing_code"
    code_reader.read.return_value = code
    loader = AnalysisDataLoader(
        repository,
        reader,
        MagicMock(),
        code_reader,
        candidates,
        names,
        EvaluationConfig(),
        TransferAnalysisEngine(),
    )
    result = loader.load(dims=None, problems=None, noise_stds=None)
    assert len(result.native_records) == expected_native
    assert result.model_slugs[label] == names.get_model_slug(raw)
    assert result.dataset.get_runs(2, 0.0, 1, "PSO")
    assert bool(result.dataset.get_runs(2, 0.0, 1, solver)) == bool(expected_native)


def test_calculation_never_exports_or_creates_directories(snapshot, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Calculation attempted presentation IO")

    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(pd.DataFrame, "to_csv", forbidden)
    filters = dict(dims=None, problems=None, noise_stds=None)
    AnalyzeEcdfAndConvergence(loader_for(snapshot), EcdfConvergenceEngine()).execute(
        mode="explicit", **filters
    )
    AnalyzeReliability(loader_for(snapshot), TransferAnalysisEngine(), ReliabilityEngine()).execute(
        **filters
    )
    AnalyzeNoiseRobustness(loader_for(snapshot), TransferAnalysisEngine()).execute(**filters)
    AnalyzePerformance(
        loader_for(snapshot), EcdfConvergenceEngine(), PerformanceMetricsEngine()
    ).execute(**filters)
