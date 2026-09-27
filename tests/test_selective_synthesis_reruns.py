"""Selective repair campaigns create fresh records without a full-matrix rerun."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.plan import CampaignPlanner
from evolution.application.synthesis_config import SynthesisConfig
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.domain.noise_model import NoiseModelEnum


def experiment(identifier: int, model: str = "model") -> SimpleNamespace:
    return SimpleNamespace(
        id=identifier,
        llm_name=model,
        mode=SynthesisMode.IMPLICIT,
        prompt_strategy=PromptStrategy.BASELINE,
        problem=SimpleNamespace(
            problem_id=1, dim=2, noise_std=0.2, noise_model=NoiseModelEnum.HETEROSCEDASTIC
        ),
    )


def planner(config: SynthesisConfig, selected: list[SimpleNamespace]) -> CampaignPlanner:
    repository = MagicMock()
    repository.load_by_ids.return_value = selected
    repository.load.return_value = [experiment(1), experiment(2)]
    result = CampaignPlanner(repository, config, MagicMock(), "model", MagicMock(), CampaignAuditor)
    result._build_fresh_task = MagicMock(return_value="fresh")
    return result


def test_reruns_are_fresh_deduplicated_and_do_not_use_matrix_count() -> None:
    config = SynthesisConfig(rerun_experiment_ids=[1, 2], rerun_repeats=2, runs_per_config=5)
    campaign = planner(config, [experiment(1), experiment(2)])
    assert campaign.build_tasks() == ["fresh", "fresh"]
    assert [call.args[1] for call in campaign._build_fresh_task.call_args_list] == [3, 4]
    assert all(
        call.kwargs["key_prefix"] == "rerun_" for call in campaign._build_fresh_task.call_args_list
    )


def test_unknown_ids_fail_before_creating_records() -> None:
    campaign = planner(SynthesisConfig(rerun_experiment_ids=[1, 99]), [experiment(1)])
    with pytest.raises(ValueError, match="Unknown rerun"):
        campaign.build_tasks()
    campaign._build_fresh_task.assert_not_called()


def test_other_models_are_not_dispatched() -> None:
    campaign = planner(
        SynthesisConfig(rerun_experiment_ids=[1]),
        [experiment(1, "another-model")],
    )
    assert campaign.build_tasks() == []
    campaign._build_fresh_task.assert_not_called()


def test_empty_rerun_list_uses_normal_campaign_planning() -> None:
    campaign = planner(SynthesisConfig(), [])
    campaign.auditor = MagicMock()
    campaign.auditor.group_experiments_by_condition.return_value = ({}, {}, {})
    assert campaign.build_tasks() == []
    campaign.sqlite_repo.load_by_ids.assert_not_called()
    campaign.auditor.group_experiments_by_condition.assert_called_once()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rerun_experiment_ids": [1], "target_exp_ids": [2]},
        {"rerun_experiment_ids": [-1]},
        {"rerun_repeats": 0},
    ],
)
def test_invalid_selections_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SynthesisConfig(**kwargs)


def test_toml_selective_settings_are_loaded(tmp_path) -> None:
    path = tmp_path / "synthesis.toml"
    path.write_text("[execution]\nrerun_experiment_ids=[1]\nrerun_repeats=2\n")
    config = SynthesisConfigRepository(path).load_config()
    assert config.rerun_experiment_ids == [1]
    assert config.rerun_repeats == 2
