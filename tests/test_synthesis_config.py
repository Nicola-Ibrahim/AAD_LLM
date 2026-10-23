"""Configuration validation happens once before typed campaign/session transfer."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from evolution.application.synthesis.models import SessionConfig
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.domain.noise_model import NoiseModelEnum


@pytest.mark.parametrize(
    ("content", "location"),
    [
        ('[evolution]\nbudget = "100000"', ("evolution", "budget")),
        ("[evolution]\nbudget = 100000.0", ("evolution", "budget")),
        ("[evolution]\nbudget = true", ("evolution", "budget")),
        ('[evolution]\ntimeout_seconds = "30"', ("evolution", "timeout_seconds")),
        ("[evolution]\ntimeout_seconds = true", ("evolution", "timeout_seconds")),
        ('[evolution]\niterations = "10"', ("evolution", "iterations")),
        ("[evolution]\nname = 123", ("evolution", "name")),
        ('[execution]\nskip_completed = "false"', ("execution", "skip_completed")),
        ("[execution]\nauto_resume = 1", ("execution", "auto_resume")),
        ('[execution]\nmax_workers = "4"', ("execution", "max_workers")),
        ('[matrix]\nnoise_stds = ["0.1"]', ("matrix", "noise_stds")),
        ("[matrix]\nnoise_stds = [true]", ("matrix", "noise_stds")),
        ('[matrix]\nnoise_conditions = [{std = "0.1"}]', ("matrix", "noise_conditions")),
        ("[matrix]\nnoise_conditions = [42]", ("matrix", "noise_conditions")),
        ('[matrix]\ndimensions = ["10"]', ("matrix", "dimensions")),
        ("[matrix]\nproblem_targets = [{id = true}]", ("matrix", "problem_targets")),
        ("[matrix]\nprompt_strategies = [42]", ("matrix", "prompt_strategies")),
        ("[matrix]\nsynthesis_modes = [42]", ("matrix", "synthesis_modes")),
        ("matrix = []", ("matrix",)),
        ('[evolution]\ninstance_policy = "per_iteration"', ("evolution", "instance_policy")),
    ],
)
def test_malformed_types_are_not_coerced_or_replaced_with_defaults(
    tmp_path: Path, content: str, location: tuple[str, ...]
) -> None:
    path = tmp_path / "synthesis.toml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValidationError) as error:
        SynthesisConfigRepository(path).load_config()
    assert any(item["loc"][: len(location)] == location for item in error.value.errors())


def test_config_and_session_transfer_keep_concrete_types(tmp_path: Path) -> None:
    path = tmp_path / "synthesis.toml"
    path.write_text(
        "[matrix]\nproblem_targets = [{id = 15, dimensions = [10]}]\n"
        'noise_conditions = [{std = 0, mode = "IMPLICIT"}]\n'
        'prompt_strategies = "GUIDED"\n'
        "[evolution]\nbudget = 100000\ntimeout_seconds = 30\niterations = 10\n"
        "[execution]\nmax_workers = 2\nskip_completed = false\n",
        encoding="utf-8",
    )
    config = SynthesisConfigRepository(path).load_config()
    (condition,) = config.matrix_conditions
    assert type(config.budget) is int
    assert type(config.timeout_seconds) is float
    assert type(config.skip_completed) is bool
    assert config.skip_completed is False
    assert type(condition.dim) is int
    assert type(condition.noise_std) is float
    assert condition.noise_std == 0.0
    assert condition.mode is SynthesisMode.IMPLICIT
    assert condition.noise_model is NoiseModelEnum.NONE
    assert condition.strategy is PromptStrategy.GUIDED
    assert config.noise_conditions[0].mode is SynthesisMode.IMPLICIT

    session = config.to_session_config(iterations=7)
    assert isinstance(session, SessionConfig)
    assert session.iterations == 7
    assert config.iterations == 10
    assert session.budget == config.budget
    assert type(session.budget) is int
    assert type(session.timeout_seconds) is float


@pytest.mark.parametrize(
    ("settings", "expected"),
    [
        ("eval_timeout_seconds = 12", 12.0),
        ("eval_timeout_seconds = 12\ntimeout_seconds = 30", 30.0),
    ],
)
def test_supported_timeout_alias_keeps_precedence(
    tmp_path: Path, settings: str, expected: float
) -> None:
    path = tmp_path / "synthesis.toml"
    path.write_text(f"[evolution]\n{settings}\n", encoding="utf-8")
    assert SynthesisConfigRepository(path).load_config().timeout_seconds == expected


def test_missing_configuration_keeps_historical_defaults(tmp_path: Path) -> None:
    config = SynthesisConfigRepository(tmp_path / "absent.toml").load_config()
    assert config.budget == 1_000_000
    assert config.timeout_seconds == 30.0
    assert config.iterations == 10
    assert config.dimensions == [2, 3, 5]
    assert config.noise_stds == [0.0, 0.05]
    assert len(config.matrix_conditions) == 240
