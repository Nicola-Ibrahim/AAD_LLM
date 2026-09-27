"""The cleanup workflow can operate without SQLite or filesystem access."""

from collections.abc import Callable

import pytest

from evolution.application.interfaces.duplicate_storage import DuplicateStorage
from evolution.application.maintenance.duplicates import SynthesisDuplicateMaintenance
from evolution.application.maintenance.models import (
    CleanupPlan,
    CleanupResult,
    Condition,
    DuplicateRow,
)


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
    plan = workflow.preview()
    assert plan.delete_ids == (2,)
    with pytest.raises(ValueError, match="Stop synthesis"):
        workflow.apply(plan, confirmation=plan.confirmation, jobs_stopped=False)
    with pytest.raises(RuntimeError, match="valid authorization"):
        workflow.apply(plan, confirmation=plan.confirmation, jobs_stopped=True)


def test_model_validation_without_database() -> None:
    with pytest.raises(ValueError, match="not present"):
        SynthesisDuplicateMaintenance(SnapshotStorage()).preview(models=["unknown"])
