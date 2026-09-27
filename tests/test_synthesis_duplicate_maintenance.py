"""Duplicate cleanup is reviewed, backed up, scoped and reversible."""

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from evolution.application.maintenance.duplicates import SynthesisDuplicateMaintenance
from evolution.infra.storage.synthesis.maintenance import SQLiteDuplicateStorage
from shared.infra.database import Base, Database
from shared.infra.database.tables import ErrorLogORM, ExperimentORM, IterationORM


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    db = Database(f"sqlite:///{tmp_path / 'database.sqlite3'}")
    Base.metadata.create_all(db.engine)
    yield db
    db.dispose()


def add(
    db: Database,
    root: Path,
    identifier: int,
    *,
    status: str = "completed",
    error: float | None = 0.1,
    evaluations: int | None = 10,
    iterations: int = 1,
    **condition: object,
) -> None:
    metadata: dict[str, object] = {
        "id": identifier,
        "llm_name": "full-model-name",
        "problem_id": 1,
        "dim": 2,
        "instance_id": 1,
        "mode": "explicit",
        "noise_std": 0.0,
        "noise_model": "none",
        "prompt_strategy": "baseline",
        "budget": 100,
        "max_iterations": 10,
        "status": status,
        "best_final_error": error,
    }
    metadata.update(condition)
    with db.session_factory.begin() as session:
        session.add(ExperimentORM(**metadata))
        session.flush()
        for index in range(iterations):
            path = root / "code" / f"experiment_{identifier}" / f"iter_{index + 1}.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# optimizer {identifier}, candidate {index}")
            row = IterationORM(
                experiment_id=identifier,
                algorithm_name="optimizer",
                final_error=error,
                evaluations_used=evaluations,
                code_path=str(path),
            )
            row.error_log = ErrorLogORM(error_type="diagnostic", error_message="example")
            session.add(row)


def counts(db: Database) -> tuple[int, int, int]:
    with db.engine.connect() as connection:
        return tuple(
            connection.exec_driver_sql(f"SELECT COUNT(*) FROM {table}").scalar_one()
            for table in ("experiments", "iterations", "error_logs")
        )


def test_safe_preview_preserves_valid_runs_and_progress(database: Database, tmp_path: Path) -> None:
    add(database, tmp_path, 1, error=0.2)
    add(database, tmp_path, 2, error=0.1)
    add(database, tmp_path, 3, status="failed", error=None)
    add(database, tmp_path, 4, status="running", error=None, iterations=0)
    add(database, tmp_path, 5, status="running", error=None, iterations=2)
    before = counts(database)
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview()
    assert plan.delete_ids == (3, 4)
    assert counts(database) == before
    assert (tmp_path / "code/experiment_3").is_dir()


def test_collapse_uses_error_then_null_first_evaluation_ranking(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1, error=0.2, evaluations=1)
    add(database, tmp_path, 2, error=0.1, evaluations=10)
    add(database, tmp_path, 3, error=0.1, evaluations=None)
    add(database, tmp_path, 4, error=0.1, evaluations=None)
    plan = SynthesisDuplicateMaintenance(SQLiteDuplicateStorage(database)).preview(
        collapse_valid_runs=True
    )
    assert plan.delete_ids == (1, 2, 4)
    assert [row.experiment_id for row in plan.rows if row.action == "keep"] == [3]


@pytest.mark.parametrize(
    "difference",
    [
        {"llm_name": "different-model"},
        {"problem_id": 8},
        {"dim": 3},
        {"instance_id": 2},
        {"mode": "implicit"},
        {"noise_std": 0.1},
        {"noise_model": "heteroscedastic"},
        {"prompt_strategy": "guided"},
        {"budget": 200},
        {"max_iterations": 20},
    ],
)
def test_distinct_conditions_and_protocols_never_merge(
    database: Database, tmp_path: Path, difference: dict[str, object]
) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, **difference)
    assert (
        SynthesisDuplicateMaintenance(SQLiteDuplicateStorage(database))
        .preview(collapse_valid_runs=True)
        .rows
        == ()
    )


def test_backup_and_quarantine_preserve_recovery_and_unrelated_records(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    add(database, tmp_path, 3, problem_id=8)
    checkpoint = tmp_path / "evolution_state/2D/std_0.0/f1/experiment_2"
    checkpoint.mkdir(parents=True)
    (checkpoint / "llamea_config.pkl").write_bytes(b"old checkpoint")
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview()
    result = maintenance.apply(
        plan, confirmation=plan.confirmation, jobs_stopped=True, quarantine_files=True
    )
    assert result.deleted_ids == (2,)
    assert counts(database) == (2, 2, 2)
    assert (tmp_path / "code/experiment_1/iter_1.py").is_file()
    assert (tmp_path / "code/experiment_3/iter_1.py").is_file()
    assert not (tmp_path / "code/experiment_2").exists()
    assert not checkpoint.exists()
    assert len(result.quarantined_paths) == 2
    with sqlite3.connect(result.backup_directory / "database.sqlite3") as backup:
        assert backup.execute("SELECT COUNT(*) FROM experiments").fetchone()[0] == 3
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    manifest = json.loads((result.backup_directory / "manifest.json").read_text())
    assert manifest["plan"]["collapse_valid_runs"] is False
    assert len(manifest["quarantined_artifacts"]) == 2
    assert maintenance.preview().delete_ids == ()


def test_stale_plan_and_missing_confirmation_cannot_delete(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview()
    with pytest.raises(ValueError, match="exact preview"):
        maintenance.apply(plan, confirmation="", jobs_stopped=True)
    with pytest.raises(ValueError, match="Stop"):
        maintenance.apply(plan, confirmation=plan.confirmation, jobs_stopped=False)
    add(database, tmp_path, 3, problem_id=8)
    with pytest.raises(RuntimeError, match="changed"):
        maintenance.apply(plan, confirmation=plan.confirmation, jobs_stopped=True)
    assert counts(database) == (3, 3, 3)
    assert not (tmp_path / "maintenance_backups").exists()


def test_forged_plan_cannot_delete_protected_winner(database: Database, tmp_path: Path) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview()
    forged = replace(plan, rows=tuple(replace(row, action="delete") for row in plan.rows))
    with pytest.raises(RuntimeError, match="changed"):
        maintenance.apply(forged, confirmation=forged.confirmation, jobs_stopped=True)
    assert counts(database) == (2, 2, 2)


def test_shared_code_cannot_be_quarantined(database: Database, tmp_path: Path) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    with database.engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE iterations SET code_path=? WHERE experiment_id=1",
            (str(tmp_path / "code/experiment_2/iter_1.py"),),
        )
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview()
    with pytest.raises(ValueError, match="retained experiment"):
        maintenance.apply(
            plan, confirmation=plan.confirmation, jobs_stopped=True, quarantine_files=True
        )
    assert counts(database) == (2, 2, 2)


def test_legacy_database_without_seed_column_is_supported(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    with database.engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE experiments DROP COLUMN synthesis_seed")
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    assert maintenance.preview().delete_ids == (2,)


def test_notebook_compiles_and_defaults_to_preview_only() -> None:
    notebook = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "notebooks/maintenance/cleanup_synthesis_duplicates.ipynb"
        ).read_text()
    )
    sources = []
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            compile(source, "maintenance-notebook", "exec")
            sources.append(source)
            assert cell["outputs"] == []
    assert "APPLY_CLEANUP = False" in "\n".join(sources)
    assert "JOBS_STOPPED = False" in "\n".join(sources)
    assert "COLLAPSE_VALID_RUNS = False" in "\n".join(sources)


def test_missing_summary_does_not_delete_a_completed_finite_candidate(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1, error=None)
    add(database, tmp_path, 2)
    with database.engine.begin() as connection:
        connection.exec_driver_sql("UPDATE iterations SET final_error=0.2 WHERE experiment_id=1")
    plan = SynthesisDuplicateMaintenance(SQLiteDuplicateStorage(database)).preview()
    assert plan.delete_ids == ()
    assert all(row.valid_completed for row in plan.rows)


def test_model_scope_does_not_remove_another_models_records(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    add(database, tmp_path, 3, llm_name="other-model")
    add(database, tmp_path, 4, llm_name="other-model", status="failed", error=None)
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview(models=["full-model-name"])
    assert plan.delete_ids == (2,)
    assert {row.experiment_id for row in plan.rows} == {1, 2}
    with pytest.raises(ValueError, match="not present"):
        maintenance.preview(models=["missing-model"])


def test_failed_deletion_rolls_back_rows_and_restores_quarantined_files(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    with database.engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TRIGGER protect BEFORE DELETE ON experiments WHEN OLD.id=2 BEGIN SELECT RAISE(ABORT, 'protected'); END"
        )
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview()
    with pytest.raises(Exception, match="protected"):
        maintenance.apply(
            plan, confirmation=plan.confirmation, jobs_stopped=True, quarantine_files=True
        )
    assert counts(database) == (2, 2, 2)
    assert (tmp_path / "code/experiment_2/iter_1.py").is_file()
    assert list((tmp_path / "maintenance_backups").glob("*/database.sqlite3"))


def test_symlink_artifact_is_refused_before_any_deletion(
    database: Database, tmp_path: Path
) -> None:
    add(database, tmp_path, 1)
    add(database, tmp_path, 2, status="failed", error=None)
    directory = tmp_path / "code/experiment_2"
    outside = tmp_path / "keep-directory"
    directory.rename(outside)
    directory.symlink_to(outside, target_is_directory=True)
    maintenance = SynthesisDuplicateMaintenance(
        SQLiteDuplicateStorage(database, data_directory=tmp_path)
    )
    plan = maintenance.preview()
    with pytest.raises(ValueError, match="Unsafe artifact"):
        maintenance.apply(
            plan, confirmation=plan.confirmation, jobs_stopped=True, quarantine_files=True
        )
    assert counts(database) == (2, 2, 2)
    assert (outside / "iter_1.py").is_file()
    assert not (tmp_path / "maintenance_backups").exists()
