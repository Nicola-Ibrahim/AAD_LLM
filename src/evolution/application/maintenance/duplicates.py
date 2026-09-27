"""Review duplicate experiments and coordinate explicitly approved cleanup."""

import math
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace

from evolution.application.interfaces.duplicate_storage import DuplicateStorage
from evolution.application.maintenance.models import (
    CleanupPlan,
    CleanupResult,
    Condition,
    DuplicateRow,
)


class SynthesisDuplicateMaintenance:
    """Application workflow; storage operations are delegated to an adapter."""

    def __init__(self, storage: DuplicateStorage) -> None:
        self.storage = storage

    @staticmethod
    def _plan(
        records: list[DuplicateRow], fingerprint: str, models: tuple[str, ...], collapse: bool
    ) -> CleanupPlan:
        groups: defaultdict[Condition, list[DuplicateRow]] = defaultdict(list)
        for row in records:
            if not models or row.condition.model in models:
                groups[row.condition].append(row)
        output: list[DuplicateRow] = []
        for group in groups.values():
            if len(group) < 2:
                continue
            completed = [row for row in group if row.valid_completed]
            pending = [row for row in group if row.status == "running"]

            def rank(row: DuplicateRow) -> tuple[float, tuple[int, int]]:
                return (
                    row.champion_error if row.champion_error is not None else math.inf,
                    (0, 0) if row.evaluations is None else (1, row.evaluations),
                )

            if completed:
                # Preserve the scientific winner, not the newest record. Missing
                # code is reported, not used as a new ranking criterion.
                winner = min(completed, key=rank)
            elif pending:
                winner = max(pending, key=lambda row: (row.iterations, row.experiment_id))
            else:
                winner = max(group, key=lambda row: row.experiment_id)
            for row in group:
                keep = row == winner or (row.valid_completed and not collapse)
                # Safe mode also retains interrupted sessions with real progress.
                if not collapse and row.status == "running" and row.iterations:
                    keep = True
                if not collapse and row.status not in {"completed", "failed", "running"}:
                    keep = True
                reason = (
                    "Retained representative"
                    if row == winner
                    else "Preserve valid completed history"
                    if row.valid_completed and keep
                    else "Preserve interrupted progress"
                    if keep and row.status == "running"
                    else "Unrecognized status; review manually"
                    if keep
                    else f"Redundant record; representative #{winner.experiment_id} retained"
                )
                output.append(replace(row, action="keep" if keep else "delete", reason=reason))
        return CleanupPlan(fingerprint, tuple(output), models, collapse)

    def preview(
        self, *, models: Sequence[str] = (), collapse_valid_runs: bool = False
    ) -> CleanupPlan:
        """Read a consistent snapshot; safe mode retains every valid completed run."""
        records, fingerprint = self.storage.read_snapshot()
        requested = tuple(dict.fromkeys(models))
        unknown = set(requested) - {row.condition.model for row in records}
        if unknown:
            raise ValueError(f"Models not present in this database: {sorted(unknown)}")
        return self._plan(records, fingerprint, requested, collapse_valid_runs)

    def apply(
        self,
        plan: CleanupPlan,
        *,
        confirmation: str,
        jobs_stopped: bool,
        quarantine_files: bool = False,
    ) -> CleanupResult:
        """Authorize cleanup; revalidate the plan inside the storage transaction."""
        if not jobs_stopped or confirmation != plan.confirmation:
            raise ValueError(
                "Stop synthesis/evaluation jobs and provide the exact preview confirmation"
            )
        if not plan.delete_ids:
            raise ValueError("The preview contains no records to remove")

        def validate(records: list[DuplicateRow], fingerprint: str) -> None:
            current = self._plan(records, fingerprint, plan.models, plan.collapse_valid_runs)
            if current != plan:
                raise RuntimeError(
                    "Database or candidate availability changed; generate and review a new preview"
                )

        return self.storage.apply(plan, validate=validate, quarantine_files=quarantine_files)
