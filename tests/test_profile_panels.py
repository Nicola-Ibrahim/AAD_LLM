"""Performance figures consume calculated arrays, never cross-function averages."""

import numpy as np
import pytest
from notebooks.analysis.plotting.profiles import build_profile
from notebooks.analysis.plotting.style import (
    CLASSICAL_SOLVERS_STYLE,
    STRATEGY_COLORS,
    get_solver_line_style,
)

from benchmarking.application.analysis.results import ConditionProfile, ProfileSeries


@pytest.mark.parametrize("kind", ["convergence", "ecdf"])
def test_profiles_only_plot_individual_functions(kind):
    problems = [1, 8, 11, 15, 21]
    values = np.ones(300)
    profile = ConditionProfile(
        "Model",
        "model",
        2,
        0.0,
        problems,
        ["Model / baseline"],
        np.logspace(0, 6, 300),
        np.array([1e-8]),
        [
            ProfileSeries("Model / baseline", p, values, values, values, values, 20)
            for p in problems
        ],
    )
    figure = build_profile(profile, "explicit", kind=kind, title="Profile")
    assert len(figure.layout.annotations) == 5
    assert all("Overall" not in annotation.text for annotation in figure.layout.annotations)
    assert {trace.xaxis for trace in figure.data} == {"x", "x2", "x3", "x4", "x5"}
    assert "xaxis6" not in figure.layout
    np.testing.assert_array_equal(values, np.ones(300))


@pytest.mark.parametrize("kind", ["convergence", "ecdf"])
def test_comparison_legend_separates_strategy_and_mode(kind):
    values = np.array([1.0, 0.5])
    solvers = [
        f"Model / {strategy} ({mode})"
        for strategy in ["baseline", "guided", "thinking", "vectorization"]
        for mode in ["noise-adapted", "noise-implicit"]
    ]
    profile = ConditionProfile(
        "Model",
        "model",
        2,
        0.1,
        [1],
        solvers,
        np.array([1, 10]),
        np.array([1e-8]),
        [ProfileSeries(s, 1, values, values, values, values, 20) for s in solvers],
    )
    figure = build_profile(profile, "comparison", kind=kind, title="Comparison")
    keys = [trace for trace in figure.data if trace.showlegend]
    assert [trace.name for trace in keys] == [
        "Baseline prompt",
        "Guided",
        "Thinking",
        "Vectorization",
        "Explicit (noise-informed)",
        "Implicit (noise-blind)",
    ]
    assert keys[-2].line.dash == "solid"
    assert keys[-1].line.dash == "dash"
    assert figure.layout.legend.y > figure.layout.legend2.y
    assert figure.layout.legend.x == figure.layout.legend2.x == 0.5
    assert figure.layout.legend.title.side == figure.layout.legend2.title.side == "top"
    assert figure.layout.margin.b >= 270
    assert figure.layout.annotations[-1].y < figure.layout.legend2.y
    curves = [trace for trace in figure.data if trace.name and not trace.showlegend]
    assert len(curves) == 8
    for trace in curves:
        assert trace.line.dash == ("solid" if "noise-informed" in trace.name else "dash")
        np.testing.assert_array_equal(trace.y, values)
    np.testing.assert_array_equal(values, [1.0, 0.5])


def test_strategy_and_classical_colors_are_distinct():
    colors = list(STRATEGY_COLORS.values()) + [
        style["color"] for style in CLASSICAL_SOLVERS_STYLE.values()
    ]
    assert len(set(colors)) == 7


@pytest.mark.parametrize("model", ["Qwen 14B", "Qwen 32B", "DeepSeek", "Model 7B"])
@pytest.mark.parametrize("suffix", ["", " (noise-adapted)", " (noise-implicit)"])
def test_strategy_colors_ignore_model_size_and_mode_suffix(model, suffix):
    for strategy, color in STRATEGY_COLORS.items():
        style = get_solver_line_style(f"{model} / {strategy}{suffix}")
        assert style["color"] == color
        assert style["dash"] == "dash"
    for solver, expected in CLASSICAL_SOLVERS_STYLE.items():
        assert get_solver_line_style(solver.upper()) == expected


@pytest.mark.parametrize("mode", ["explicit", "implicit", "comparison"])
def test_ecdf_and_convergence_share_strategy_palette(mode):
    values = np.array([1.0, 0.5])
    suffixes = [" (noise-adapted)", " (noise-implicit)"] if mode == "comparison" else [""]
    solvers = [f"Model / {strategy}{suffix}" for strategy in STRATEGY_COLORS for suffix in suffixes]
    if mode != "comparison":
        solvers += ["CMA-ES", "PSO", "DE"]
    profile = ConditionProfile(
        "Model",
        "model",
        2,
        0.05,
        [1],
        solvers,
        np.array([1, 10]),
        np.array([1e-8]),
        [ProfileSeries(s, 1, values, values, values, values, 20) for s in solvers],
    )
    styles = []
    for kind in ["convergence", "ecdf"]:
        figure = build_profile(profile, mode, kind=kind, title="Profile")
        curves = [
            trace
            for trace in figure.data
            if trace.name and trace.x[0] is not None and trace.mode == "lines"
        ]
        styles.append({t.name: (t.line.color, t.line.dash) for t in curves})
        for trace in curves:
            if " / " in trace.name:
                strategy = trace.name.split(" / ", 1)[1]
            else:
                strategy = trace.name.split(" ", 1)[0].lower()
            if strategy in STRATEGY_COLORS:
                assert trace.line.color == STRATEGY_COLORS[strategy]
            elif mode != "comparison":
                assert trace.line.color == CLASSICAL_SOLVERS_STYLE[trace.name.lower()]["color"]
                assert trace.line.dash == "solid"
    assert styles[0] == styles[1]
