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
