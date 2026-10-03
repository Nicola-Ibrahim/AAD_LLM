"""Independent notebooks, numerical persistence and uncached PNG exports."""

import hashlib
import json
from contextlib import nullcontext
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from notebooks.analysis.plotting.exporter import AnalysisFigureExporter

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
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace
from benchmarking.infra.storage.analysis_results_store import AnalysisResultsStore
from benchmarking.infra.storage.model_registry import configured_model_names
from bootstrap.analysis import AnalysisUseCases

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    "analysis/05_reliability_summary.ipynb",
    "analysis/06_convergence_ecdf_and_ablations.ipynb",
    "analysis/07_noise_robustness.ipynb",
]


def notebook_cells(name: str) -> list[dict[str, object]]:
    return json.loads((ROOT / "notebooks" / name).read_text())["cells"]


@pytest.fixture
def inputs(tmp_path: Path) -> AnalysisSnapshot:
    model = "qwen2.5-coder-14b-instruct-q4_k_m.gguf"
    names = configured_model_names()
    label = names.get_clean_model_label(model) + " / baseline"
    dataset = EvaluationDataset()
    for noise in [0.0, 0.05]:
        for solver in [label, "PSO"]:
            for _ in range(20):
                dataset.add_run(
                    EvaluationCondition(dim=2, noise_std=noise, problem_id=1),
                    solver,
                    RunTrace(evaluations=np.array([1, 100]), raw_objectives=np.array([1.0, 0.0])),
                )
    code = "frozen optimizer"
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    native = dict(
        evaluation_schema_version=EVALUATION_SCHEMA_VERSION,
        return_validation_version=CHAMPION_RETURN_VALIDATION_VERSION,
        error_definition=ERROR_DEFINITION,
        model=model,
        strategy="baseline",
        source_problem_id=1,
        problem_id=1,
        dim=2,
        noise_std=0.0,
        code_hash=code_hash,
        clean_errors=[0.0] * 20,
        n_runs=20,
        solver_folder="qwen_14b_baseline",
        evaluation_kind="native",
    )
    noise_record = dict(native, noise_std=0.05, evaluation_kind="noise_robustness")
    baseline = dict(
        evaluation_schema_version=EVALUATION_SCHEMA_VERSION,
        error_definition=ERROR_DEFINITION,
        baseline="pso",
        problem_id=1,
        dim=2,
        noise_std=0.0,
        clean_errors=[0.0] * 20,
        n_runs=20,
        solver_folder="pso",
    )
    baseline_noise = dict(baseline, noise_std=0.05)
    reader = MagicMock()
    reader.load_evaluation_traces.return_value = dataset
    reader.load_provenance_records.return_value = [native, noise_record, baseline, baseline_noise]
    repository = MagicMock()
    repository.get_synthesis_dataframes.return_value = (
        pd.DataFrame([dict(status="completed", llm_name=model)]),
        pd.DataFrame(),
    )
    champion = dict(
        llm_name=model,
        problem_id=1,
        dim=2,
        mode="explicit",
        noise_std=0.0,
        prompt_strategy="baseline",
        code_path=str(tmp_path / "champion.py"),
    )
    code_reader = MagicMock()
    code_reader.exists.return_value = True
    code_reader.read.return_value = code
    transfer_reader = MagicMock()
    transfer_reader.load_provenance_records.return_value = [
        dict(
            native, problem_id=8, clean_errors=[0.0] * 2, n_runs=2, evaluation_kind="cross_function"
        ),
        dict(native, source_problem_id=8, code_hash="obsolete", evaluation_kind="cross_function"),
    ]
    champions = MagicMock()
    champions.get_champions.return_value = {model: {"f1": champion}}
    loader = AnalysisDataLoader(
        repository,
        reader,
        transfer_reader,
        code_reader,
        champions,
        names,
        EvaluationConfig(cross_function_problem_ids=[1, 8]),
        TransferAnalysisEngine(),
    )
    return loader.load(dims=None, problems=None, noise_stds=None, include_transfer=True)


def use_cases(snapshot: AnalysisSnapshot) -> AnalysisUseCases:
    loader = MagicMock()
    loader.load.return_value = snapshot
    return AnalysisUseCases(
        AnalyzeEcdfAndConvergence(loader, EcdfConvergenceEngine()),
        AnalyzeReliability(loader, TransferAnalysisEngine(), ReliabilityEngine()),
        AnalyzeNoiseRobustness(loader, TransferAnalysisEngine()),
        AnalyzePerformance(loader, EcdfConvergenceEngine(), PerformanceMetricsEngine()),
    )


@pytest.fixture
def png_exports(tmp_path: Path, monkeypatch) -> list[tuple[go.Figure, str]]:
    import bootstrap.analysis
    import shared.config

    monkeypatch.setattr(shared.config, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        bootstrap.analysis,
        "build_analysis_results_store",
        lambda: AnalysisResultsStore(tmp_path / "analysis"),
    )
    exports = []

    def write_image(figure: go.Figure, path: str, **kwargs: object) -> None:
        Path(path).touch()
        exports.append((figure, path))

    monkeypatch.setattr(go.Figure, "write_image", write_image)
    return exports


def test_modified_notebook_cells_compile() -> None:
    for name in ["03_evaluation.ipynb"] + NOTEBOOKS:
        for index, cell in enumerate(notebook_cells(name)):
            if cell["cell_type"] == "code":
                source = "".join(
                    line for line in cell["source"] if not line.lstrip().startswith("%")
                )
                compile(source, f"{name}:cell{index}", "exec")


def test_cross_function_figure_export_removed() -> None:
    from notebooks.analysis.plotting import generalization

    assert not hasattr(generalization, "export_cross_function")


def test_summary_exports_only_attainment_png_and_rebuilds_each_time(
    inputs: AnalysisSnapshot, png_exports, monkeypatch
) -> None:
    from notebooks.analysis.plotting import summary

    from shared.config import RESULTS_DIR

    result = use_cases(inputs).reliability.execute(dims=None, problems=None, noise_stds=None)
    builder = MagicMock(wraps=summary.build_attainment_figure)
    monkeypatch.setattr(summary, "build_attainment_figure", builder)
    exporter = AnalysisFigureExporter(RESULTS_DIR)
    exporter.export_reliability(result)
    exporter.export_reliability(result)
    assert len(png_exports) == 2
    assert builder.call_count == 2
    figure, path = png_exports[0]
    assert path.endswith("fig_10b_fixed_target_attainment.png")
    assert max(figure.data[0].x) == pytest.approx(2 * inputs.config.budget_multiplier)
    assert png_exports[0][1] == png_exports[1][1]
    assert not list(RESULTS_DIR.rglob(".analysis_cache"))


def test_transfer_changes_do_not_affect_other_workflow_provenance(inputs: AnalysisSnapshot) -> None:
    changed = replace(
        inputs, transfer_records=[dict(r, clean_errors=[1.0] * 20) for r in inputs.transfer_records]
    )
    for workflow in ["summary", "profiles", "noise"]:
        assert inputs.provenance(workflow) == changed.provenance(workflow)
    assert inputs.provenance("transfer") != changed.provenance("transfer")
    changed_config = inputs.config.model_copy(update={"cross_function_problem_ids": [1, 8, 11]})
    assert inputs.provenance("profiles") == replace(inputs, config=changed_config).provenance(
        "profiles"
    )


def test_failed_export_propagates_and_can_be_retried(tmp_path: Path, monkeypatch) -> None:
    exporter = AnalysisFigureExporter(tmp_path)
    target = tmp_path / "figure.png"
    writer = MagicMock(side_effect=RuntimeError("Export failed"))
    monkeypatch.setattr(go.Figure, "write_image", writer)
    with pytest.raises(RuntimeError, match="Export failed"):
        exporter.export_figure(go.Figure(), target)
    writer.side_effect = None
    exporter.export_figure(go.Figure(), target)
    assert writer.call_count == 2
    assert not list(tmp_path.rglob("*.json"))


def test_exporter_rejects_non_png_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="PNG-only"):
        AnalysisFigureExporter(tmp_path).export_figure(go.Figure(), tmp_path / "figure.html")


def test_profile_provenance_detects_trace_changes(inputs: AnalysisSnapshot) -> None:
    dataset = inputs.dataset.model_copy(deep=True)
    condition = next(iter(dataset))
    solver = next(iter(dataset[condition]))
    dataset[condition][solver].pop()
    changed = replace(inputs, dataset=dataset)
    assert (
        inputs.provenance("profiles").trace_signature
        != changed.provenance("profiles").trace_signature
    )
    before = changed.provenance("profiles").trace_signature
    dataset[condition][solver][0].raw_objectives[-1] = 0.5
    changed_values = replace(inputs, dataset=dataset)
    assert before != changed_values.provenance("profiles").trace_signature


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebooks_run_independently(
    name: str, inputs: AnalysisSnapshot, png_exports, monkeypatch
) -> None:
    import bootstrap.analysis

    monkeypatch.setattr(
        bootstrap.analysis, "build_analysis_use_cases", lambda: nullcontext(use_cases(inputs))
    )
    scope = {"display": lambda table: None}
    for cell in notebook_cells(name):
        if cell["cell_type"] == "code":
            source = "".join(line for line in cell["source"] if not line.lstrip().startswith("%"))
            exec(compile(source, name, "exec"), scope)
    assert png_exports
    assert all(path.endswith(".png") for _, path in png_exports)


def test_noise_success_rates_export(inputs: AnalysisSnapshot, png_exports) -> None:
    from shared.config import RESULTS_DIR

    result = use_cases(inputs).noise_robustness.execute(dims=None, problems=None, noise_stds=None)
    AnalysisFigureExporter(RESULTS_DIR).export_noise_robustness(result)
    table = result.aggregate
    assert len(png_exports) == 1
    figure, path = png_exports[0]
    assert path.endswith("success_rate_vs_noise.png")
    assert {trace.line.dash for trace in figure.data} == {"dash", "solid"}
    assert set(table["Noise Std"]) == {0.0, 0.05}
    assert all(trace.error_y.symmetric is False for trace in figure.data)


def test_noise_success_rates_do_not_plot_clean_only(inputs: AnalysisSnapshot, png_exports) -> None:
    from shared.config import RESULTS_DIR

    clean = replace(
        inputs, noise_records=[r for r in inputs.noise_records if r["noise_std"] == 0.0]
    )
    result = use_cases(clean).noise_robustness.execute(dims=None, problems=None, noise_stds=None)
    AnalysisFigureExporter(RESULTS_DIR).export_noise_robustness(result)
    assert not png_exports


def assert_saved_equal(expected: object, actual: object) -> None:
    """Verify all arrays, tables, identities and scientific metadata recursively."""
    if isinstance(expected, pd.DataFrame):
        pd.testing.assert_frame_equal(expected, actual)
    elif isinstance(expected, pd.Series):
        pd.testing.assert_series_equal(expected, actual)
    elif isinstance(expected, np.ndarray):
        np.testing.assert_array_equal(expected, actual)
    elif is_dataclass(expected):
        assert type(expected) is type(actual)
        for field in fields(expected):
            assert_saved_equal(getattr(expected, field.name), getattr(actual, field.name))
    elif isinstance(expected, dict):
        assert expected.keys() == actual.keys()
        for key in expected:
            assert_saved_equal(expected[key], actual[key])
    elif isinstance(expected, (list, tuple)):
        assert type(expected) is type(actual)
        assert len(expected) == len(actual)
        for before, after in zip(expected, actual, strict=True):
            assert_saved_equal(before, after)
    else:
        assert expected == actual


@pytest.mark.parametrize(
    "workflow", ["ecdf_and_convergence", "reliability", "noise_robustness", "performance"]
)
def test_analysis_snapshots_round_trip(inputs, tmp_path, workflow):
    options = dict(dims=None, problems=None, noise_stds=None)
    if workflow == "ecdf_and_convergence":
        options["mode"] = "explicit"
    result = getattr(use_cases(inputs), workflow).execute(**options)
    store = AnalysisResultsStore(tmp_path / "analysis")
    directory = store.save(result)
    assert directory.is_relative_to(tmp_path / "analysis")
    restored = store.load(directory)
    assert_saved_equal(result, restored)
    assert store.save(result) == directory
    assert not list(tmp_path.rglob("*.png"))
    if workflow == "ecdf_and_convergence":
        from notebooks.analysis.plotting.profiles import build_profile

        figure = build_profile(restored.conditions[0], restored.mode, kind="ecdf", title="Reloaded")
        assert figure.data


def test_snapshot_rejects_corruption_and_outside_paths(inputs, tmp_path):
    result = use_cases(inputs).ecdf_and_convergence.execute(
        mode="explicit", dims=None, problems=None, noise_stds=None
    )
    store = AnalysisResultsStore(tmp_path / "analysis")
    directory = store.save(result)
    with (directory / "arrays.npz").open("ab") as stream:
        stream.write(b"corruption")
    with pytest.raises(ValueError, match="checksum"):
        store.load(directory)
    with pytest.raises(ValueError, match="inside"):
        store.load(tmp_path / "elsewhere")


def test_snapshot_preserves_empty_profiles_and_nonfinite_arrays(inputs, tmp_path):
    result = use_cases(inputs).ecdf_and_convergence.execute(
        mode="explicit", dims=None, problems=None, noise_stds=None
    )
    store = AnalysisResultsStore(tmp_path / "analysis")
    empty = replace(result, conditions=[], diagnostics=("No traces available.",))
    assert_saved_equal(empty, store.load(store.save(empty)))
    curve = result.conditions[0].series[0]
    curve.median[:3] = [np.inf, np.nan, -np.inf]
    assert_saved_equal(result, store.load(store.save(result)))


def test_snapshot_preserves_missing_values_empty_strings_and_table_index(inputs, tmp_path):
    result = use_cases(inputs).reliability.execute(dims=None, problems=None, noise_stds=None)
    table = pd.DataFrame(
        {
            "label": pd.array(["", "NA", pd.NA], dtype="string"),
            "error": np.array([np.inf, np.nan, 0.12345678901234567]),
            "complete": [True, False, True],
        },
        index=pd.Index([2, 7, 11], name="condition"),
    )
    result = replace(result, native=table)
    store = AnalysisResultsStore(tmp_path / "analysis")
    assert_saved_equal(result, store.load(store.save(result)))


@pytest.mark.parametrize("workflow", ["reliability", "noise_robustness", "performance"])
def test_snapshot_preserves_empty_workflow_results(inputs, tmp_path, workflow):
    empty = replace(inputs, dataset=EvaluationDataset(), native_records=[], noise_records=[])
    result = getattr(use_cases(empty), workflow).execute(dims=None, problems=None, noise_stds=None)
    store = AnalysisResultsStore(tmp_path / "analysis")
    assert_saved_equal(result, store.load(store.save(result)))


def test_snapshot_failed_write_does_not_publish_manifest(inputs, tmp_path, monkeypatch):
    result = use_cases(inputs).ecdf_and_convergence.execute(
        mode="explicit", dims=None, problems=None, noise_stds=None
    )
    store = AnalysisResultsStore(tmp_path / "analysis")
    monkeypatch.setattr(store, "_write", MagicMock(side_effect=OSError("Disk unavailable")))
    with pytest.raises(OSError, match="Disk unavailable"):
        store.save(result)
    assert not list(store.root.rglob("manifest.json"))
