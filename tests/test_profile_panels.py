"""Performance figures contain function panels, never cross-function averages."""

from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest
from notebooks.analysis.plotting.profiles import ProfileCurve, build_profile


@pytest.mark.parametrize("kind", ["convergence", "ecdf"])
def test_profiles_only_plot_individual_functions(kind):
    dataset = SimpleNamespace(problem_ids=[1, 8, 11, 15, 21])
    curve = ProfileCurve("solver", "Solver", "#0284C7", "dash", 0.0)
    values = np.ones(300)
    with patch("notebooks.analysis.plotting.profiles.EcdfConvergenceEngine") as factory:
        engine = factory.return_value
        engine.get_convergence_trajectory.return_value = {
            "median": values,
            "q25": values,
            "q75": values,
        }
        engine.get_target_ecdf_curve.return_value = values
        figure = build_profile(
            SimpleNamespace(),
            dataset,
            [curve],
            {0.0: np.array([1e-8])},
            dim=2,
            kind=kind,
            title="Profile",
        )
        method = (
            engine.get_convergence_trajectory
            if kind == "convergence"
            else engine.get_target_ecdf_curve
        )
        assert [call.kwargs["problem_id"] for call in method.call_args_list] == dataset.problem_ids
        engine.get_aggregate_convergence.assert_not_called()
        engine.get_aggregate_target_ecdf_curve.assert_not_called()
    assert len(figure.layout.annotations) == 5
    assert all("Overall" not in annotation.text for annotation in figure.layout.annotations)
    assert {trace.xaxis for trace in figure.data} == {"x", "x2", "x3", "x4", "x5"}
    assert "xaxis6" not in figure.layout
