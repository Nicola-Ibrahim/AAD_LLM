"""Replacement campaigns retain exact IDs and never create rows for recovery."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pandas as pd
import pytest
from study_fixtures import run_parameters

from evolution.application.campaign.audit import CampaignAudit
from evolution.application.campaign.conditions import condition_from_experiment
from evolution.application.campaign.planner import CampaignPlanner
from evolution.application.campaign.settings import CampaignSettings
from evolution.application.model_selection import ModelSelection
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.noise_model import NoiseModelEnum

MODEL = ModelSelection(provider="local", model_id="model")


def experiment(
    identifier: int,
    model: str = MODEL.model_id,
    *,
    status: str = "completed",
    error: float | None = 0.0,
    problem_id: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=identifier,
        llm_name=model,
        mode=SynthesisMode.IMPLICIT,
        prompt_strategy=PromptStrategy.BASELINE,
        status=status,
        best_final_error=error,
        problem=SimpleNamespace(
            problem_id=problem_id, dim=2, noise_std=0.2, noise_model=NoiseModelEnum.HETEROSCEDASTIC
        ),
    )


def planner(config: CampaignSettings, selected: list[SimpleNamespace]) -> CampaignPlanner:
    repository = MagicMock()
    repository.load_by_ids.return_value = selected
    repository.load.return_value = [experiment(1), experiment(2)]
    result = CampaignPlanner(repository, config, MagicMock())
    result._build_fresh_task = MagicMock(return_value="fresh")
    result._build_task_from_experiment = MagicMock(return_value="existing")
    return result


def plan(campaign: CampaignPlanner, **kwargs: object) -> list[object]:
    return campaign.build_tasks(model=MODEL, **kwargs)


def inspect_coverage(planned: CampaignPlanner) -> tuple[pd.DataFrame, dict[str, object]]:
    # These fixtures define one condition directly instead of a public matrix.
    (condition,) = planned.config.matrix_conditions
    parameters = run_parameters(planned.config)
    parameters.update(
        problem_targets=[{"id": condition.problem_id, "dimensions": [condition.dim]}],
        noise_conditions=[{"std": condition.noise_std, "noise_model": condition.noise_model}],
        synthesis_modes=[{"mode": condition.mode, "strategies": [condition.strategy]}],
    )
    return CampaignAudit(planned.sqlite_repo, MagicMock()).inspect(model=MODEL, **parameters).value


def test_reruns_replace_exact_ids_without_using_matrix_quota() -> None:
    config = CampaignSettings(runs_per_config=5)
    campaign = planner(config, [experiment(1), experiment(2)])
    assert plan(campaign, rerun_experiment_ids=[1, 2]) == ["existing", "existing"]
    assert [call.args[0].id for call in campaign._build_task_from_experiment.call_args_list] == [
        1,
        2,
    ]
    assert all(
        call.kwargs["restart"] for call in campaign._build_task_from_experiment.call_args_list
    )
    campaign._build_fresh_task.assert_not_called()
    campaign.sqlite_repo.reset_experiment.assert_not_called()


def test_unknown_ids_fail_before_creating_records() -> None:
    campaign = planner(CampaignSettings(), [experiment(1)])
    with pytest.raises(ValueError, match="Unknown rerun"):
        plan(campaign, rerun_experiment_ids=[1, 99])
    campaign._build_fresh_task.assert_not_called()


def test_other_models_are_not_dispatched() -> None:
    campaign = planner(
        CampaignSettings(),
        [experiment(1, "local--another-model")],
    )
    with pytest.raises(ValueError, match="do not belong to selected model"):
        plan(campaign, rerun_experiment_ids=[1])
    campaign._build_fresh_task.assert_not_called()


def test_empty_rerun_list_uses_normal_campaign_planning() -> None:
    campaign = planner(CampaignSettings(), [])
    assert plan(campaign) == []
    campaign.sqlite_repo.load_by_ids.assert_not_called()
    campaign.sqlite_repo.load.assert_called_once_with(llm_name=MODEL.model_id)


def test_manual_reruns_include_unresolved_failures_and_running_conditions() -> None:
    selected = experiment(1)
    invalid = experiment(3, error=None, problem_id=8)
    running = experiment(6, status="running", error=None, problem_id=11)
    resolved_failure = experiment(7, status="failed", error=None, problem_id=15)
    resolved_success = experiment(8, problem_id=15)
    conditions = [
        condition_from_experiment(exp) for exp in [selected, invalid, running, resolved_failure]
    ]
    campaign = planner(CampaignSettings(matrix_conditions=conditions), [selected])
    campaign.sqlite_repo.load.return_value = [
        selected,
        invalid,
        experiment(5, status="failed", error=None, problem_id=11),
        running,
        resolved_failure,
        resolved_success,
        experiment(9, status="failed", error=None, problem_id=99),
    ]
    campaign._build_task_from_experiment = MagicMock(return_value="resume")
    assert plan(campaign, rerun_experiment_ids=[1]) == ["resume", "resume", "resume"]
    assert [call.args[0].id for call in campaign._build_task_from_experiment.call_args_list] == [
        1,
        6,
        3,
    ]
    campaign._build_fresh_task.assert_not_called()


def test_manual_replacement_keeps_requested_id_not_other_pending_record() -> None:
    campaign = planner(CampaignSettings(), [experiment(1)])
    running = experiment(3, status="running", error=None)
    campaign.sqlite_repo.load.return_value = [experiment(1), running]
    campaign._build_task_from_experiment = MagicMock(return_value="resume")
    assert plan(campaign, rerun_experiment_ids=[1]) == ["resume"]
    campaign._build_fresh_task.assert_not_called()


def test_duplicate_requested_ids_restart_once() -> None:
    campaign = planner(CampaignSettings(), [experiment(1)])
    campaign.sqlite_repo.load.return_value = [
        experiment(1),
        experiment(3, status="running", error=None),
    ]
    campaign._build_task_from_experiment = MagicMock(return_value="resume")
    assert plan(campaign, rerun_experiment_ids=[1, 1]) == ["resume"]
    campaign._build_task_from_experiment.assert_called_once_with(
        campaign.sqlite_repo.load_by_ids.return_value[0],
        model=MODEL,
        tag="replace",
        restart=True,
    )
    campaign._build_fresh_task.assert_not_called()


def test_manual_and_automatic_failure_share_one_repair_slot() -> None:
    failed = experiment(1, status="failed", error=None)
    campaign = planner(CampaignSettings(), [failed])
    campaign.sqlite_repo.load.return_value = [failed]
    assert plan(campaign, rerun_experiment_ids=[1]) == ["existing"]
    campaign._build_fresh_task.assert_not_called()


def test_retry_disabled_keeps_only_manual_repairs() -> None:
    selected = experiment(1)
    failed = experiment(3, status="failed", error=None, problem_id=8)
    campaign = planner(
        CampaignSettings(
            retry_failed_synthesis=False,
            matrix_conditions=[condition_from_experiment(failed)],
        ),
        [selected],
    )
    campaign.sqlite_repo.load.return_value = [selected, failed]
    assert plan(campaign, rerun_experiment_ids=[1]) == ["existing"]
    assert campaign._build_task_from_experiment.call_args.args[0].problem.problem_id == 1


def test_fresh_repeat_keys_are_unique() -> None:
    selected = experiment(1)
    campaign = planner(CampaignSettings(), [selected])
    campaign.problem_factory.create.return_value = SimpleNamespace(
        problem_id=1,
        dim=2,
        noise_std=0.2,
        noise_model=NoiseModelEnum.HETEROSCEDASTIC,
        instance_id=1,
        true_optimum=0.0,
    )
    campaign.sqlite_repo.create_experiment.side_effect = [10, 11]
    condition = condition_from_experiment(selected)
    first = CampaignPlanner._build_fresh_task(campaign, condition, 3, MODEL, key_prefix="rerun_")
    second = CampaignPlanner._build_fresh_task(campaign, condition, 4, MODEL, key_prefix="rerun_")
    assert first["key"] != second["key"]
    assert first["experiment_id"] == 10
    assert second["experiment_id"] == 11


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rerun_experiment_ids": [1], "resume_experiment_ids": [2]},
        {"rerun_experiment_ids": [-1]},
        {"rerun_experiment_ids": [True]},
    ],
)
def test_invalid_selections_are_rejected(kwargs: dict[str, object]) -> None:
    campaign = planner(CampaignSettings(), [])
    with pytest.raises(ValueError):
        plan(campaign, **kwargs)
    campaign.sqlite_repo.create_experiment.assert_not_called()


def test_recovery_without_manual_ids_discovers_failures() -> None:
    failed = experiment(3, status="failed", error=None)
    config = CampaignSettings(matrix_conditions=[condition_from_experiment(failed)])
    campaign = planner(config, [])
    campaign.sqlite_repo.load.return_value = [failed]
    assert plan(campaign, recover=True) == ["existing"]
    campaign.sqlite_repo.load_by_ids.assert_not_called()
    assert config.model_dump() == campaign.config.model_dump()


def test_selection_is_not_retained_between_calls() -> None:
    campaign = planner(CampaignSettings(), [experiment(1)])
    assert plan(campaign, rerun_experiment_ids=[1]) == ["existing"]
    campaign._build_fresh_task.reset_mock()
    assert plan(campaign) == []
    campaign._build_fresh_task.assert_not_called()


def test_explicit_resume_selects_running_records_for_selected_model() -> None:
    pending = experiment(1, status="running", error=None)
    campaign = planner(CampaignSettings(), [pending, experiment(2)])
    campaign._build_task_from_experiment = MagicMock(return_value="resume")
    assert plan(campaign, resume_experiment_ids=[1, 1, 2]) == ["resume"]
    campaign._build_task_from_experiment.assert_called_once_with(pending, model=MODEL, tag="target")
    campaign._build_fresh_task.assert_not_called()


def test_explicit_resume_rejects_a_different_model_id() -> None:
    campaign = planner(CampaignSettings(), [experiment(3, "other-model", status="running")])
    with pytest.raises(ValueError, match="do not belong to selected model"):
        plan(campaign, resume_experiment_ids=[3])


def test_campaign_forwards_runtime_request_without_changing_protocol() -> None:
    from evolution.application.campaign.service import SynthesisCampaign

    config = CampaignSettings()
    original = config.model_dump()
    service = SynthesisCampaign(
        sqlite_repo=MagicMock(),
        worker_count=1,
        logger=MagicMock(),
        problem_factory=MagicMock(),
        worker_pool=MagicMock(),
        worker_fn=MagicMock(),
    )
    service._build_planner = MagicMock()
    service._build_planner.return_value.build_tasks.return_value = []
    service.run(model=MODEL, **run_parameters(config), recover=True, rerun_experiment_ids=[1]).value
    service._build_planner.return_value.build_tasks.assert_called_once_with(
        model=MODEL,
        recover=True,
        rerun_experiment_ids=[1],
        resume_experiment_ids=(),
    )
    assert config.model_dump() == original
    service.worker_pool.execute.assert_not_called()


def test_champion_prevents_automatic_retry_of_newer_failures_and_queued_runs() -> None:
    champion = experiment(1)
    champion.iterations = [SimpleNamespace(timed_out=True)] * 9
    condition = condition_from_experiment(champion)
    campaign = planner(CampaignSettings(matrix_conditions=[condition]), [])
    campaign.sqlite_repo.load.return_value = [
        champion,
        experiment(2, status="failed", error=None),
        experiment(3, status="running", error=None),
    ]
    campaign._build_task_from_experiment = MagicMock(return_value="resume")
    assert plan(campaign, recover=True) == []
    assert plan(campaign) == []
    campaign._build_task_from_experiment.assert_not_called()
    campaign._build_fresh_task.assert_not_called()
    matrix, summary = inspect_coverage(campaign)
    assert summary["completed_conditions"] == 1
    assert summary["retry_conditions"] == 0
    assert matrix.iloc[0]["Status"] == "✅ Complete"
    assert matrix.iloc[0]["Running Records"] == 1
    assert matrix.iloc[0]["Failed Records"] == 1


def test_coverage_is_champion_availability_not_replicate_quota() -> None:
    champion = experiment(1)
    condition = condition_from_experiment(champion)
    campaign = planner(CampaignSettings(matrix_conditions=[condition], runs_per_config=5), [])
    campaign.sqlite_repo.load.return_value = [champion]
    _, summary = inspect_coverage(campaign)
    assert summary["progress_pct"] == 100.0
    assert plan(campaign, recover=True) == []


def test_failed_session_is_not_coverage_when_retry_is_disabled() -> None:
    failed = experiment(1, status="failed", error=None)
    condition = condition_from_experiment(failed)
    campaign = planner(
        CampaignSettings(matrix_conditions=[condition], retry_failed_synthesis=False), []
    )
    campaign.sqlite_repo.load.return_value = [failed]
    _, summary = inspect_coverage(campaign)
    assert summary["completed_conditions"] == 0
    assert plan(campaign, recover=True) == []


def test_normal_scheduling_replaces_failed_record_without_creating_new_row() -> None:
    failed = experiment(1, status="failed", error=None)
    config = CampaignSettings(matrix_conditions=[condition_from_experiment(failed)])
    campaign = planner(config, [])
    campaign.sqlite_repo.load.return_value = [failed]
    assert plan(campaign) == ["existing"]
    campaign._build_task_from_experiment.assert_called_once_with(
        failed, model=MODEL, tag="replace", restart=True
    )
    campaign._build_fresh_task.assert_not_called()


def test_replacement_payload_keeps_id_and_starts_at_generation_one() -> None:
    selected = experiment(1401)
    selected.iterations = [object()] * 10
    selected.max_iterations = 10
    selected.synthesis_seed = 43
    selected.problem.instance_id = 1
    campaign = planner(CampaignSettings(), [selected])
    task = CampaignPlanner._build_task_from_experiment(
        campaign, selected, model=MODEL, tag="replace", restart=True
    )
    assert task["experiment_id"] == 1401
    assert task["initial_iteration"] == 0
    assert task["restart"] is True
    assert campaign.problem_factory.create.call_args.kwargs["seed"] == 43
    campaign.sqlite_repo.reset_experiment.assert_not_called()
    campaign.sqlite_repo.create_experiment.assert_not_called()


def test_resume_preserves_seed_and_budget() -> None:
    selected = experiment(1401, status="running")
    selected.iterations = [object()]
    selected.budget = 100000
    selected.max_iterations = 10
    selected.synthesis_seed = 43
    selected.problem.instance_id = 1
    campaign = planner(CampaignSettings(budget=100000), [selected])
    task = CampaignPlanner._build_task_from_experiment(campaign, selected, model=MODEL)
    assert task["initial_iteration"] == 1
    assert task["config"].budget == selected.budget
    assert campaign.problem_factory.create.call_args.kwargs["seed"] == 43


@pytest.mark.parametrize(("budget", "seed"), [(1000, 43), (None, 43), (100000, None)])
def test_unsafe_resume_fails_before_problem_creation(budget: int | None, seed: int | None) -> None:
    selected = experiment(1401, status="running")
    selected.iterations = [object()]
    selected.budget = budget
    selected.synthesis_seed = seed
    campaign = planner(CampaignSettings(budget=100000), [selected])
    with pytest.raises(ValueError, match="Cannot resume"):
        CampaignPlanner._build_task_from_experiment(campaign, selected, model=MODEL)
    campaign.problem_factory.create.assert_not_called()
    campaign.sqlite_repo.reset_experiment.assert_not_called()
