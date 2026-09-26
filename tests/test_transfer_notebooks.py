"""Independent analysis notebooks and cached PNG exports on synthetic data."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from benchmarking.application.analysis.data import AnalysisData
from benchmarking.application.analysis.view_data import AnalysisInputs, load_analysis_inputs
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.domain.vos import EvaluationCondition, EvaluationDataset, RunTrace
from notebooks.analysis.plotting.cache import FigureCache, build_figure_cache
from benchmarking.infra.storage.model_registry import configured_model_names

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    "analysis/05_analysis.ipynb",
    "analysis/06_performance_profiles.ipynb",
    "analysis/07_generalization.ipynb",
]


def notebook_cells(name: str) -> list[dict[str, object]]:
    return json.loads((ROOT / "notebooks" / name).read_text())["cells"]


@pytest.fixture
def inputs(tmp_path: Path) -> AnalysisInputs:
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
    service = AnalysisData(repository, reader, names)
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
    return load_analysis_inputs(
        service,
        {model: {"f1": champion}},
        code_reader,
        transfer_reader,
        EvaluationConfig(cross_function_problem_ids=[1, 8]),
        include_transfer=True,
    )


@pytest.fixture
def png_exports(tmp_path: Path, monkeypatch) -> list[tuple[go.Figure, str]]:
    from notebooks.analysis.plotting import cache, generalization, summary, performance, profiles

    for module in [cache, generalization, summary, performance, profiles]:
        monkeypatch.setattr(module, "RESULTS_DIR", tmp_path)
        for attribute, path in [
            ("REPORTS_DIR", tmp_path / "reports"),
            ("THESIS_SUMMARY_DIR", tmp_path / "figures" / "06_thesis_summary"),
            ("EXPLICIT_DIR", tmp_path / "figures" / "02_explicit"),
            ("TRANSFER_FIGURES_DIR", tmp_path / "figures" / "07_cross_function"),
        ]:
            if hasattr(module, attribute):
                monkeypatch.setattr(module, attribute, path)
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


def test_transfer_png_matrix_and_versioned_csvs(
    inputs: AnalysisInputs, png_exports, tmp_path: Path
) -> None:
    from notebooks.analysis.plotting.generalization import export_cross_function

    table = export_cross_function(inputs, build_figure_cache(inputs, "transfer"))
    assert len(png_exports) == 1
    figure, output = png_exports[0]
    assert output.endswith(".png")
    assert figure.data[0].z[0, 0] == 1.0
    assert np.isnan(figure.data[0].z[0, 1])
    assert np.isnan(figure.data[0].z[1, 0])
    assert figure.layout.plot_bgcolor == "#D1D5DB"
    assert table.set_index("Target Problem")["Trials"].to_dict() == {1: 20, 8: 2}
    assert (tmp_path / "reports" / "cross_function_reliability_v1.csv").is_file()
    assert not list(tmp_path.rglob("*.html"))
    export_cross_function(inputs, build_figure_cache(inputs, "transfer"))
    assert len(png_exports) == 1


def test_summary_exports_exactly_three_pngs_and_skips_cached_builders(
    inputs: AnalysisInputs, png_exports, monkeypatch
) -> None:
    from notebooks.analysis.plotting import summary

    summary.export_summary(inputs, build_figure_cache(inputs, "summary"))
    assert len(png_exports) == 3
    for name in ["_reliability_matrix", "_attainment_profile", "_noise_summary"]:
        monkeypatch.setattr(
            summary, name, MagicMock(side_effect=AssertionError("Cached builder executed"))
        )
    summary.export_summary(inputs, build_figure_cache(inputs, "summary"))
    assert len(png_exports) == 3


def test_transfer_changes_do_not_invalidate_other_workflows(
    inputs: AnalysisInputs, png_exports
) -> None:
    changed = replace(
        inputs, transfer_records=[dict(r, clean_errors=[1.0] * 20) for r in inputs.transfer_records]
    )
    for workflow in ["summary", "profiles", "noise"]:
        assert (
            build_figure_cache(inputs, workflow).signature
            == build_figure_cache(changed, workflow).signature
        )
    assert (
        build_figure_cache(inputs, "transfer").signature
        != build_figure_cache(changed, "transfer").signature
    )
    changed_config = inputs.config.model_copy(update={"cross_function_problem_ids": [1, 8, 11]})
    assert (
        build_figure_cache(inputs, "profiles").signature
        == build_figure_cache(replace(inputs, config=changed_config), "profiles").signature
    )


def test_failed_export_is_not_cached(tmp_path: Path, monkeypatch) -> None:
    cache = FigureCache(tmp_path / "cache.json", "signature")
    target = tmp_path / "figure.png"
    monkeypatch.setattr(
        go.Figure, "write_image", MagicMock(side_effect=RuntimeError("Export failed"))
    )
    with pytest.raises(RuntimeError):
        cache.export(go.Figure(), target)
    assert cache.needs_export(target)
    assert not cache.manifest_path.exists()


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebooks_run_independently(
    name: str, inputs: AnalysisInputs, png_exports, monkeypatch
) -> None:
    import bootstrap.analysis

    monkeypatch.setattr(bootstrap.analysis, "build_analysis_inputs", lambda **kwargs: inputs)
    scope = {"display": lambda table: None}
    for cell in notebook_cells(name):
        if cell["cell_type"] == "code":
            source = "".join(line for line in cell["source"] if not line.lstrip().startswith("%"))
            exec(compile(source, name, "exec"), scope)
    assert png_exports
    assert all(path.endswith(".png") for _, path in png_exports)


def test_profile_line_styles(inputs: AnalysisInputs, png_exports) -> None:
    from notebooks.analysis.plotting.generalization import export_noise_robustness

    export_noise_robustness(inputs, build_figure_cache(inputs, "noise"))
    assert len(png_exports) == 4
    for figure, path in png_exports:
        curves = [trace for trace in figure.data if trace.showlegend]
        assert curves
        expected = "solid" if "classical_baselines" in path else "dash"
        assert all(trace.line.dash == expected for trace in curves)
