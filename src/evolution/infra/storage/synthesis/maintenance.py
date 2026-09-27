"""Explicit, backed-up maintenance of duplicate SQLite synthesis records.

This adapter is not part of campaign scheduling. Preview never modifies records;
application requires confirmation, a stable snapshot and a database backup.
"""

import hashlib
import json
import math
import shutil
import sqlite3
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.engine import Connection

from evolution.application.interfaces.duplicate_storage import DuplicateStorage
from evolution.application.maintenance.models import (
    CleanupPlan,
    CleanupResult,
    Condition,
    DuplicateRow,
)
from shared.config import DATA_DIR, PROJECT_ROOT
from shared.infra.database import Database


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _optional_int(value: object) -> int | None:
    return int(str(value)) if value is not None else None


class SQLiteDuplicateStorage(DuplicateStorage):
    """Inspect duplicate conditions and explicitly remove reviewed redundant records."""

    def __init__(
        self,
        database: Database,
        *,
        data_directory: Path = DATA_DIR,
        project_root: Path = PROJECT_ROOT,
    ) -> None:
        if not database.engine.url.drivername.startswith("sqlite"):
            raise ValueError("Duplicate maintenance requires SQLite")
        if not database.engine.url.database or database.engine.url.database == ":memory:":
            raise ValueError("Use an existing on-disk database so a recoverable backup can be made")
        self.database = database
        self.data_directory = data_directory.resolve()
        self.project_root = project_root.resolve()

    def _snapshot(self, connection: Connection) -> tuple[list[DuplicateRow], str]:
        tables = {
            name: [
                dict(row)
                for row in connection.exec_driver_sql(
                    f"SELECT * FROM {name} ORDER BY id"
                ).mappings()
            ]
            for name in ("experiments", "iterations", "error_logs")
        }
        by_experiment: defaultdict[int, list[dict[str, object]]] = defaultdict(list)
        for row in tables["iterations"]:
            by_experiment[int(row["experiment_id"])].append(row)
        records: list[DuplicateRow] = []
        file_state: list[tuple[str, bool]] = []
        for row in tables["experiments"]:
            identifier = int(row["id"])
            iterations = by_experiment[identifier]
            candidates = [item for item in iterations if _finite(item["final_error"])]
            # The existing champion keys: error ascending, NULL evaluations first,
            # stable input order for exact ties (iterations were read in ID order).
            best = (
                min(
                    candidates,
                    key=lambda item: (
                        float(item["final_error"]),
                        (0, 0)
                        if item["evaluations_used"] is None
                        else (1, int(item["evaluations_used"])),
                    ),
                )
                if candidates
                else None
            )
            code_path = str(best["code_path"] or "") if best else ""
            path = Path(code_path)
            available = (
                bool(code_path)
                and (path if path.is_absolute() else self.project_root / path).is_file()
            )
            file_state.append((code_path, available))
            condition = Condition(
                model=str(row["llm_name"]),
                problem_id=int(row["problem_id"]),
                dimension=int(row["dim"]),
                instance=int(row["instance_id"]),
                mode=str(row["mode"]),
                noise=float(row["noise_std"] or 0.0),
                noise_model=str(row["noise_model"]),
                strategy=str(row["prompt_strategy"]),
                budget=_optional_int(row["budget"]),
                max_iterations=_optional_int(row["max_iterations"]),
            )
            records.append(
                DuplicateRow(
                    experiment_id=identifier,
                    condition=condition,
                    status=str(row["status"]),
                    iterations=len(iterations),
                    champion_error=float(best["final_error"])
                    if best
                    else (
                        float(row["best_final_error"]) if _finite(row["best_final_error"]) else None
                    ),
                    evaluations=_optional_int(best["evaluations_used"]) if best else None,
                    code_available=available,
                    valid_completed=row["status"] == "completed"
                    and (_finite(row["best_final_error"]) or best is not None),
                    action="keep",
                    reason="Not a duplicate",
                )
            )
        fingerprint = hashlib.sha256(
            json.dumps((tables, file_state), sort_keys=True, default=str).encode()
        ).hexdigest()
        return records, fingerprint

    def read_snapshot(self) -> tuple[list[DuplicateRow], str]:
        """Read a consistent snapshot without changing records."""
        with self.database.engine.connect() as connection:
            connection.exec_driver_sql("BEGIN")
            return self._snapshot(connection)

    def _artifact_directories(self, ids: tuple[int, ...]) -> list[Path]:
        paths: list[Path] = []
        state_root = self.data_directory / "evolution_state"
        for identifier in ids:
            code = self.data_directory / "code" / f"experiment_{identifier}"
            candidates = [code] + (
                list(state_root.rglob(f"experiment_{identifier}")) if state_root.exists() else []
            )
            for path in candidates:
                if not path.exists() and not path.is_symlink():
                    continue
                if path.is_symlink() or not path.resolve().is_relative_to(self.data_directory):
                    raise ValueError(f"Unsafe artifact directory: {path}")
                if any(
                    parent.is_symlink() for parent in path.parents if parent != self.data_directory
                ):
                    raise ValueError(f"Symbolic-link parent in artifact path: {path}")
                if not path.is_dir():
                    raise ValueError(f"Expected per-experiment directory: {path}")
                paths.append(path)
        return paths

    def apply(
        self,
        plan: CleanupPlan,
        *,
        validate: Callable[[list[DuplicateRow], str], None],
        quarantine_files: bool = False,
    ) -> CleanupResult:
        """Back up, verify the preview is current, then delete only approved records.

        Optional file cleanup moves exact experiment directories into the backup;
        benchmark traces and champion exports are never deleted here.
        """
        backup = (
            self.data_directory
            / "maintenance_backups"
            / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
        )
        moved: list[tuple[Path, Path]] = []
        with self.database.engine.connect() as connection:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
            try:
                records, fingerprint = self._snapshot(connection)
                validate(records, fingerprint)
                artifacts = self._artifact_directories(plan.delete_ids) if quarantine_files else []
                if artifacts:
                    placeholders = ",".join("?" for _ in plan.delete_ids)
                    retained_paths = connection.exec_driver_sql(
                        f"SELECT code_path FROM iterations WHERE experiment_id NOT IN ({placeholders}) AND code_path IS NOT NULL",
                        plan.delete_ids,
                    ).scalars()
                    for value in retained_paths:
                        path = Path(str(value))
                        resolved = (
                            path if path.is_absolute() else self.project_root / path
                        ).resolve()
                        if any(
                            resolved.is_relative_to(directory.resolve()) for directory in artifacts
                        ):
                            raise ValueError(
                                f"A retained experiment references code inside proposed quarantine: {path}"
                            )
                backup.mkdir(parents=True, exist_ok=False)
                # A second reader backs up the committed snapshot while this
                # connection holds the writer lock. No deletion has happened yet.
                with self.database.engine.connect() as reader:
                    source = reader.connection.driver_connection
                    if not isinstance(source, sqlite3.Connection):
                        raise TypeError("Expected a SQLite DBAPI connection")
                    with sqlite3.connect(backup / "database.sqlite3") as destination:
                        source.backup(destination)
                manifest = {
                    "database": str(self.database.engine.url),
                    "plan": asdict(plan),
                    "quarantined_artifacts": [
                        str(path.relative_to(self.data_directory)) for path in artifacts
                    ],
                }
                (backup / "manifest.json").write_text(
                    json.dumps(manifest, indent=2), encoding="utf-8"
                )
                for source in artifacts:
                    destination = backup / "files" / source.relative_to(self.data_directory)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(destination))
                    moved.append((source, destination))
                placeholders = ",".join("?" for _ in plan.delete_ids)
                connection.exec_driver_sql(
                    f"DELETE FROM error_logs WHERE iteration_id IN (SELECT id FROM iterations WHERE experiment_id IN ({placeholders}))",
                    plan.delete_ids,
                )
                connection.exec_driver_sql(
                    f"DELETE FROM iterations WHERE experiment_id IN ({placeholders})",
                    plan.delete_ids,
                )
                connection.exec_driver_sql(
                    f"DELETE FROM experiments WHERE id IN ({placeholders})", plan.delete_ids
                )
                after, _ = self._snapshot(connection)
                coverage = {row.condition for row in records if row.valid_completed}
                if {row.condition for row in after if row.valid_completed} != coverage:
                    raise RuntimeError("Champion coverage changed unexpectedly; rolling back")
                if any(row.experiment_id in plan.delete_ids for row in after):
                    raise RuntimeError("Some approved records remain; rolling back")
                connection.commit()
            except BaseException:
                connection.rollback()
                for original, quarantined in reversed(moved):
                    original.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(quarantined), str(original))
                raise
        return CleanupResult(
            plan.delete_ids, backup, tuple(destination for _, destination in moved)
        )
