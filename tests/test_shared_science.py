"""Characterization of unchanged scientific and runtime rules across ownership moves."""

import pickle

import numpy as np
import pytest

from evolution.domain.services.algorithm_scoring import AlgorithmScoringService, FailureKind
from shared.domain.noise import NoiseStrategyFactory
from shared.domain.noise_model import NoiseModelEnum
from shared.domain.scoring import objective_gap
from shared.infra.problems.bbob import BBOBProblem


@pytest.mark.parametrize(
    "model,expected",
    [
        (
            "heteroscedastic",
            [80.08065585818638, 80.00227402211785, 80.10663743593646, 80.11771904050414],
        ),
        (
            "homoscedastic_additive",
            [80.85141577646749, 81.00306485155396, 80.55841283706614, 77.52899099679057],
        ),
        ("awgn", [80.09336578797544, 79.95889566937596, 80.13793919958066, 80.15695055163913]),
        ("none", [80.06289408] * 4),
    ],
)
def test_seeded_noise_and_clean_scoring_are_unchanged(model: str, expected: list[float]) -> None:
    problem = BBOBProblem(1, 2, NoiseStrategyFactory.create(NoiseModelEnum(model), 0.1), seed=42)
    x = np.array([1.0, -1.0])
    np.testing.assert_allclose([problem(x) for _ in range(4)], expected, rtol=0, atol=1e-12)
    assert problem.true_optimum == 79.48
    assert problem.eval_clean(x) == 80.06289408
    assert problem.evaluations == 4
    assert not hasattr(problem, "mode")
    assert not hasattr(problem, "profile")


def test_scoring_policies_and_budget_accounting_are_unchanged() -> None:
    assert objective_gap(81.0, 79.48) == AlgorithmScoringService.objective_gap(81.0, 79.48)
    assert objective_gap(79.479999999, 79.48) == 0.0
    assert AlgorithmScoringService.success(81.0, 79.48).fitness == -(81.0 - 79.48)
    assert [AlgorithmScoringService.failure_score(k) for k in FailureKind] == [-5e8, -4.5e8, -4e8]
    problem = BBOBProblem(1, 2, NoiseStrategyFactory.create(NoiseModelEnum.NONE))
    problem.set_budget(2)
    point = np.array([1.0, -1.0])
    value = problem(point)
    assert problem(point) == value
    assert problem.evaluations == 2
    with pytest.warns(UserWarning, match="BUDGET OVERRUN"):
        assert problem(point) == value
    assert problem.eval_clean(point) == value
    assert problem.evaluations == 2
    restored = pickle.loads(pickle.dumps(problem))
    assert restored.eval_clean(point) == value
