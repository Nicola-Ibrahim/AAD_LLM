"""The cleanup workflow can operate without SQLite or filesystem access."""

from collections.abc import Callable

from evolution.application.interfaces.duplicate_storage import DuplicateStorage
from evolution.application.maintenance.cleanup_types import (
    CleanupPlan,
    CleanupResult,
    Condition,
    DuplicateRow,
)
from evolution.application.maintenance.duplicate_cleanup import SynthesisDuplicateMaintenance


class SnapshotStorage(DuplicateStorage):
    def read_snapshot(self) -> tuple[list[DuplicateRow], str]:
        condition = Condition("model", 1, 2, 1, "explicit", 0.0, "none", "baseline", 100, 10)
        return [
            DuplicateRow(1, condition, "completed", 10, 0.1, 10, True, True, "keep", ""),
            DuplicateRow(2, condition, "failed", 10, None, None, False, False, "keep", ""),
        ], "snapshot"

    def apply(
        self,
        plan: CleanupPlan,
        *,
        validate: Callable[[list[DuplicateRow], str], None],
        quarantine_files: bool,
    ) -> CleanupResult:
        validate(*self.read_snapshot())
        raise RuntimeError("Storage reached only after valid authorization")


def test_preview_and_authorization_without_database() -> None:
    workflow = SynthesisDuplicateMaintenance(SnapshotStorage())
    plan = workflow.preview().value
    assert plan.delete_ids == (2,)
    refused = workflow.apply(plan, confirmation=plan.confirmation, jobs_stopped=False)
    assert not refused.is_success
    assert isinstance(refused.error._original_exception, ValueError)
    assert "Stop synthesis" in refused.error.message
    failed = workflow.apply(plan, confirmation=plan.confirmation, jobs_stopped=True)
    assert not failed.is_success
    assert isinstance(failed.error._original_exception, RuntimeError)
    assert "valid authorization" in failed.error.message


def test_model_validation_without_database() -> None:
    result = SynthesisDuplicateMaintenance(SnapshotStorage()).preview(models=["unknown"])
    assert not result.is_success
    assert isinstance(result.error._original_exception, ValueError)
    assert "not present" in result.error.message
