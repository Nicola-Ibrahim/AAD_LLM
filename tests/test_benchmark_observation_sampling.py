"""Benchmark observations are sampled without changing objective results or budget."""

import numpy as np
import pytest

from benchmarking.domain.services.returned_point import validate_returned_point
from shared.domain.noise import HeteroscedasticNoiseStrategy
from shared.infra.problems.bbob import BBOBProblem


def test_noisy_samples_preserve_values_and_eval_count() -> None:
    def problem() -> BBOBProblem:
        return BBOBProblem(
            problem_id=1,
            dim=2,
            instance_id=2,
            noise_strategy=HeteroscedasticNoiseStrategy(0.2),
            seed=43,
        )

    plain = problem()
    sampled = problem()
    plain.set_budget(12)
    sampled.set_budget(12)
    sampled.configure_observation_checkpoints(12, 4)
    points = [np.array([float(i) / 10, 0.0]) for i in range(7)]
    plain_values = [plain(x) for x in points]
    sampled_values = [sampled(x) for x in points]

    assert sampled_values == plain_values
    assert plain.evaluations == sampled.evaluations == len(points)
    observations = sampled.observation_samples()
    assert observations
    assert observations[-1].evaluations == len(points)
    assert all(
        sample.observed_y == sampled_values[sample.evaluations - 1] for sample in observations
    )
    assert all(np.isfinite(sample.observed_y) for sample in observations)
    assert len(observations) <= 5  # Four grid checkpoints plus the final query.


@pytest.mark.parametrize(
    "point",
    [np.array([6.0, 0.0]), np.array([np.nan, 0.0]), np.array([0.0]), np.zeros((2, 1))],
)
def test_returned_point_validation_rejects_invalid_coordinates(point: np.ndarray) -> None:
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.2))
    with pytest.raises(ValueError, match="Returned best_x"):
        validate_returned_point(problem, point)
    assert problem.evaluations == 0


def test_returned_point_validation_accepts_in_domain_point() -> None:
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.2))
    validate_returned_point(problem, np.zeros(2))
    assert problem.evaluations == 0
