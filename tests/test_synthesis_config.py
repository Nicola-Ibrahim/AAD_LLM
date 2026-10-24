"""Validate explicit synthesis inputs before typed campaign/session transfer."""

import pytest
from pydantic import ValidationError
from study_fixtures import synthesis_config

from evolution.application.synthesis.models import SessionConfig
from evolution.application.synthesis_config import ProblemTarget, SynthesisConfig
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.noise_model import NoiseModelEnum


@pytest.mark.parametrize(
    "values",
    [
        {"id": True, "dimensions": [10]},
        {"id": 15, "dimensions": ["10"]},
        {"id": 15, "dimensions": [0]},
        {"id": 25, "dimensions": [10]},
        {"id": 15, "dimensions": []},
    ],
)
def test_problem_target_rejects_invalid_inputs(values):
    with pytest.raises(ValidationError):
        ProblemTarget(**values)


def test_config_and_session_transfer_keep_concrete_types():
    config = synthesis_config(
        problem_targets=[{"id": 15, "dimensions": [10]}],
        noise_conditions=[{"std": 0.1, "noise_model": "heteroscedastic"}],
        synthesis_modes=[{"mode": "implicit", "strategies": ["guided"]}],
        skip_completed=False,
    )
    (condition,) = config.matrix_conditions
    assert type(config.budget) is int
    assert type(config.timeout_seconds) is float
    assert config.skip_completed is False
    assert type(condition.dim) is int
    assert type(condition.noise_std) is float
    assert condition.mode is SynthesisMode.IMPLICIT
    assert condition.noise_model is NoiseModelEnum.HETEROSCEDASTIC
    assert condition.strategy is PromptStrategy.GUIDED
    session = config.to_session_config(iterations=7)
    assert isinstance(session, SessionConfig)
    assert session.iterations == 7
    assert config.iterations == 10
    assert session.budget == config.budget == 100_000


def test_explicit_matrix_and_protocol_defaults():
    config = synthesis_config()
    assert config.dimensions == [2, 10, 50]
    assert config.noise_stds == [0.0, 0.05, 0.1, 0.2]
    assert len(config.matrix_conditions) == 480
    assert SynthesisConfig().budget == 100_000
    assert SynthesisConfig().matrix_conditions == []
