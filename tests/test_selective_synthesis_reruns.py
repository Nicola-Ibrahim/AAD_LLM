"""Replacement campaigns retain exact IDs and never create rows for recovery."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from evolution.application.campaign.audit import CampaignAuditor
from evolution.application.campaign.plan import CampaignPlanner
from evolution.application.synthesis_config import SynthesisConfig
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.domain.noise_model import NoiseModelEnum


def experiment(
    identifier: int,
    model: str = "model",
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


def planner(config: SynthesisConfig, selected: list[SimpleNamespace]) -> CampaignPlanner:
    repository = MagicMock()
    repository.load_by_ids.return_value = selected
    repository.load.return_value = [experiment(1), experiment(2)]
    auditor = CampaignAuditor(repository, config, MagicMock(), "model")
    result = CampaignPlanner(repository, config, MagicMock(), "model", MagicMock(), auditor)
    result._build_fresh_task = MagicMock(return_value="fresh")
    result._build_task_from_summary = MagicMock(return_value="existing")
    return result


def test_reruns_replace_exact_ids_without_using_matrix_quota() -> None:
    config = SynthesisConfig(runs_per_config=5)
    campaign = planner(config, [experiment(1), experiment(2)])
    assert campaign.build_tasks(rerun_experiment_ids=[1, 2]) == ["existing", "existing"]
    assert [call.args[0].id for call in campaign._build_task_from_summary.call_args_list] == [1, 2]
    assert all(call.kwargs["restart"] for call in campaign._build_task_from_summary.call_args_list)
    campaign._build_fresh_task.assert_not_called()
    campaign.sqlite_repo.reset_experiment.assert_not_called()


def test_unknown_ids_fail_before_creating_records() -> None:
    campaign = planner(SynthesisConfig(), [experiment(1)])
    with pytest.raises(ValueError, match="Unknown rerun"):
        campaign.build_tasks(rerun_experiment_ids=[1, 99])
    campaign._build_fresh_task.assert_not_called()


def test_other_models_are_not_dispatched() -> None:
    campaign = planner(
        SynthesisConfig(),
        [experiment(1, "another-model")],
    )
    assert campaign.build_tasks(rerun_experiment_ids=[1]) == []
    campaign._build_fresh_task.assert_not_called()


def test_empty_rerun_list_uses_normal_campaign_planning() -> None:
    campaign = planner(SynthesisConfig(), [])
    campaign.auditor = MagicMock()
    campaign.auditor.group_experiments_by_condition.return_value = ({}, {}, {})
    assert campaign.build_tasks() == []
    campaign.sqlite_repo.load_by_ids.assert_not_called()
    campaign.auditor.group_experiments_by_condition.assert_called_once()


def test_manual_reruns_include_unresolved_failures_and_running_conditions() -> None:
    selected = experiment(1)
    invalid = experiment(3, error=None, problem_id=8)
    running = experiment(6, status="running", error=None, problem_id=11)
    resolved_failure = experiment(7, status="failed", error=None, problem_id=15)
    resolved_success = experiment(8, problem_id=15)
    conditions = [
        CampaignAuditor._condition_from_summary(exp)
        for exp in [selected, invalid, running, resolved_failure]
    ]
    campaign = planner(SynthesisConfig(matrix_conditions=conditions), [selected])
    campaign.sqlite_repo.load.return_value = [
        selected,
        invalid,
        experiment(5, status="failed", error=None, problem_id=11),
        running,
        resolved_failure,
        resolved_success,
        experiment(9, status="failed", error=None, problem_id=99),
    ]
    campaign._build_task_from_summary = MagicMock(return_value="resume")
    assert campaign.build_tasks(rerun_experiment_ids=[1]) == ["resume", "resume", "resume"]
    assert [call.args[0].id for call in campaign._build_task_from_summary.call_args_list] == [
        1,
        6,
        3,
    ]
    campaign._build_fresh_task.assert_not_called()


def test_manual_replacement_keeps_requested_id_not_other_pending_record() -> None:
    campaign = planner(SynthesisConfig(), [experiment(1)])
    running = experiment(3, status="running", error=None)
    campaign.sqlite_repo.load.return_value = [experiment(1), running]
    campaign._build_task_from_summary = MagicMock(return_value="resume")
    assert campaign.build_tasks(rerun_experiment_ids=[1]) == ["resume"]
    campaign._build_fresh_task.assert_not_called()


def test_duplicate_requested_ids_restart_once() -> None:
    campaign = planner(SynthesisConfig(), [experiment(1)])
    campaign.sqlite_repo.load.return_value = [
        experiment(1),
        experiment(3, status="running", error=None),
    ]
    campaign._build_task_from_summary = MagicMock(return_value="resume")
    assert campaign.build_tasks(rerun_experiment_ids=[1, 1]) == ["resume"]
    campaign._build_task_from_summary.assert_called_once_with(
        campaign.sqlite_repo.load_by_ids.return_value[0], tag="replace", restart=True
    )
    campaign._build_fresh_task.assert_not_called()


def test_manual_and_automatic_failure_share_one_repair_slot() -> None:
    failed = experiment(1, status="failed", error=None)
    campaign = planner(SynthesisConfig(), [failed])
    campaign.sqlite_repo.load.return_value = [failed]
    assert campaign.build_tasks(rerun_experiment_ids=[1]) == ["existing"]
    campaign._build_fresh_task.assert_not_called()


def test_retry_disabled_keeps_only_manual_repairs() -> None:
    selected = experiment(1)
    failed = experiment(3, status="failed", error=None, problem_id=8)
    campaign = planner(
        SynthesisConfig(
            retry_failed_synthesis=False,
            matrix_conditions=[CampaignAuditor._condition_from_summary(failed)],
        ),
        [selected],
    )
    campaign.sqlite_repo.load.return_value = [selected, failed]
    assert campaign.build_tasks(rerun_experiment_ids=[1]) == ["existing"]
    assert campaign._build_task_from_summary.call_args.args[0].problem.problem_id == 1


def test_fresh_repeat_keys_are_unique() -> None:
    selected = experiment(1)
    campaign = planner(SynthesisConfig(), [selected])
    campaign.problem_factory.create.return_value = SimpleNamespace(
        problem_id=1,
        dim=2,
        noise_std=0.2,
        noise_model=NoiseModelEnum.HETEROSCEDASTIC,
        instance_id=1,
        true_optimum=0.0,
    )
    campaign.sqlite_repo.create_experiment.side_effect = [10, 11]
    condition = CampaignAuditor._condition_from_summary(selected)
    first = CampaignPlanner._build_fresh_task(campaign, condition, 3, key_prefix="rerun_")
    second = CampaignPlanner._build_fresh_task(campaign, condition, 4, key_prefix="rerun_")
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
    campaign = planner(SynthesisConfig(), [])
    with pytest.raises(ValueError):
        campaign.build_tasks(**kwargs)
    campaign.sqlite_repo.create_experiment.assert_not_called()


def test_toml_rejects_dynamic_campaign_options(tmp_path) -> None:
    path = tmp_path / "synthesis.toml"
    path.write_text("[execution]\nrerun_experiment_ids=[1]\nrerun_repeats=2\n")
    with pytest.raises(ValueError, match="into run_campaign"):
        SynthesisConfigRepository(path).load_config()


def test_recovery_without_manual_ids_discovers_failures() -> None:
    failed = experiment(3, status="failed", error=None)
    config = SynthesisConfig(matrix_conditions=[CampaignAuditor._condition_from_summary(failed)])
    campaign = planner(config, [])
    campaign.sqlite_repo.load.return_value = [failed]
    assert campaign.build_tasks(recover=True) == ["existing"]
    campaign.sqlite_repo.load_by_ids.assert_not_called()
    assert config.model_dump() == campaign.config.model_dump()


def test_selection_is_not_retained_between_calls() -> None:
    campaign = planner(SynthesisConfig(), [experiment(1)])
    assert campaign.build_tasks(rerun_experiment_ids=[1]) == ["existing"]
    campaign._build_fresh_task.reset_mock()
    assert campaign.build_tasks() == []
    campaign._build_fresh_task.assert_not_called()


def test_explicit_resume_filters_model_and_completed_records() -> None:
    pending = experiment(1, status="running", error=None)
    campaign = planner(
        SynthesisConfig(), [pending, experiment(2), experiment(3, "other", status="running")]
    )
    campaign._build_task_from_summary = MagicMock(return_value="resume")
    assert campaign.build_tasks(resume_experiment_ids=[1, 1, 2, 3]) == ["resume"]
    campaign._build_task_from_summary.assert_called_once_with(pending, tag="target")
    campaign._build_fresh_task.assert_not_called()


def test_campaign_forwards_runtime_request_without_changing_protocol() -> None:
    from evolution.application.campaign.run import SynthesisCampaignCoordinator

    config = SynthesisConfig()
    original = config.model_dump()
    service = SynthesisCampaignCoordinator(
        sqlite_repo=MagicMock(),
        config=config,
        logger=MagicMock(),
        engine=MagicMock(),
        model_name="model",
        problem_factory=MagicMock(),
        dispatcher=MagicMock(),
        worker_fn=MagicMock(),
    )
    service.planner = MagicMock()
    service.planner.build_tasks.return_value = []
    service.run_campaign(recover=True, rerun_experiment_ids=[1])
    service.planner.build_tasks.assert_called_once_with(
        recover=True,
        rerun_experiment_ids=[1],
        resume_experiment_ids=(),
    )
    assert config.model_dump() == original
    service.dispatcher.run.assert_not_called()


def test_champion_prevents_automatic_retry_of_newer_failures_and_queued_runs() -> None:
    champion = experiment(1)
    champion.iterations = [SimpleNamespace(timed_out=True)] * 9
    condition = CampaignAuditor._condition_from_summary(champion)
    campaign = planner(SynthesisConfig(matrix_conditions=[condition]), [])
    campaign.sqlite_repo.load.return_value = [
        champion,
        experiment(2, status="failed", error=None),
        experiment(3, status="running", error=None),
    ]
    campaign._build_task_from_summary = MagicMock(return_value="resume")
    assert campaign.build_tasks(recover=True) == []
    assert campaign.build_tasks() == []
    campaign._build_task_from_summary.assert_not_called()
    campaign._build_fresh_task.assert_not_called()
    matrix, summary = campaign.auditor.audit_matrix()
    assert summary["completed_conditions"] == 1
    assert summary["retry_conditions"] == 0
    assert matrix.iloc[0]["Status"] == "✅ Complete"
    assert matrix.iloc[0]["Running Records"] == 1
    assert matrix.iloc[0]["Failed Records"] == 1


def test_coverage_is_champion_availability_not_replicate_quota() -> None:
    champion = experiment(1)
    condition = CampaignAuditor._condition_from_summary(champion)
    campaign = planner(SynthesisConfig(matrix_conditions=[condition], runs_per_config=5), [])
    campaign.sqlite_repo.load.return_value = [champion]
    _, summary = campaign.auditor.audit_matrix()
    assert summary["progress_pct"] == 100.0
    assert campaign.build_tasks(recover=True) == []


def test_failed_session_is_not_coverage_when_retry_is_disabled() -> None:
    failed = experiment(1, status="failed", error=None)
    condition = CampaignAuditor._condition_from_summary(failed)
    campaign = planner(
        SynthesisConfig(matrix_conditions=[condition], retry_failed_synthesis=False), []
    )
    campaign.sqlite_repo.load.return_value = [failed]
    _, summary = campaign.auditor.audit_matrix()
    assert summary["completed_conditions"] == 0
    assert campaign.build_tasks(recover=True) == []


def test_normal_scheduling_replaces_failed_record_without_creating_new_row() -> None:
    failed = experiment(1, status="failed", error=None)
    config = SynthesisConfig(matrix_conditions=[CampaignAuditor._condition_from_summary(failed)])
    campaign = planner(config, [])
    campaign.sqlite_repo.load.return_value = [failed]
    assert campaign.build_tasks() == ["existing"]
    campaign._build_task_from_summary.assert_called_once_with(failed, tag="replace", restart=True)
    campaign._build_fresh_task.assert_not_called()


def test_replacement_payload_keeps_id_and_starts_at_generation_one() -> None:
    selected = experiment(1401)
    selected.iterations = [object()] * 10
    selected.max_iterations = 10
    selected.synthesis_seed = 43
    selected.problem.instance_id = 1
    campaign = planner(SynthesisConfig(), [selected])
    task = CampaignPlanner._build_task_from_summary(campaign, selected, tag="replace", restart=True)
    assert task["experiment_id"] == 1401
    assert task["initial_iteration"] == 0
    assert task["restart"] is True
    assert campaign.problem_factory.create.call_args.kwargs["seed"] == 43
    campaign.sqlite_repo.reset_experiment.assert_not_called()
    campaign.sqlite_repo.create_experiment.assert_not_called()
