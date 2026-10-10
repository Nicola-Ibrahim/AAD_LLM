"""Performance figures consume calculated arrays, never cross-function averages."""

import numpy as np
import pytest
from notebooks.analysis.plotting.profiles import build_profile

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
