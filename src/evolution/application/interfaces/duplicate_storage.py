"""Storage boundary for backed-up synthesis maintenance."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from evolution.application.maintenance.models import CleanupPlan, CleanupResult, DuplicateRow


class DuplicateStorage(ABC):
    @abstractmethod
    def read_snapshot(self) -> tuple[list[DuplicateRow], str]:
        """Read records and their database/artifact fingerprint without mutation."""

    @abstractmethod
    def apply(
        self,
        plan: CleanupPlan,
        *,
        validate: Callable[[list[DuplicateRow], str], None],
        quarantine_files: bool,
    ) -> CleanupResult:
        """Lock, validate, back up and atomically clean reviewed records."""
