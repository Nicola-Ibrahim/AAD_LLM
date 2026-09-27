"""Seed metadata must not require migrating populated research databases."""

from pathlib import Path

import pytest

from evolution.domain.enums import SynthesisMode
from evolution.domain.vos import ProblemProfile
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.infra.database import Base, Database


@pytest.mark.parametrize("has_seed_column", [False, True])
def test_repository_reads_and_writes_without_migrating(
    tmp_path: Path, has_seed_column: bool
) -> None:
    database = Database(f"sqlite:///{tmp_path / 'synthesis.db'}")
    try:
        Base.metadata.create_all(database.engine)
        with database.engine.begin() as connection:
            if not has_seed_column:
                connection.exec_driver_sql("ALTER TABLE experiments DROP COLUMN synthesis_seed")
            schema_before = connection.exec_driver_sql(
                "SELECT name, sql FROM sqlite_master ORDER BY name"
            ).all()

        repository = SQLiteSynthesisRepository(database.session_factory)
        identifier = repository.create_experiment(
            problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0),
            mode=SynthesisMode.EXPLICIT,
            llm_name="test-model",
            synthesis_seed=43,
        )
        assert repository.get_experiment_status(identifier) == ("running", 0)
        experiment = repository.load_by_ids([identifier])[0]
        assert experiment.synthesis_seed == (43 if has_seed_column else None)
        assert repository.load(llm_name="test-model")[0].id == identifier
        experiment.status = "completed"
        repository.save_experiment_summary(experiment)
        assert repository.get_experiment_status(identifier) == ("completed", 0)
        repository.mark_failed(identifier)
        assert repository.load_by_ids([identifier])[0].status == "failed"

        with database.engine.connect() as connection:
            assert (
                connection.exec_driver_sql(
                    "SELECT name, sql FROM sqlite_master ORDER BY name"
                ).all()
                == schema_before
            )
    finally:
        database.dispose()
