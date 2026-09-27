"""Replacing synthesis results keeps the original ID and touches only its state."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import func, select

from evolution.application.synthesis.models import SessionConfig, SessionResult
from evolution.domain.enums import PromptStrategy, SynthesisMode
from evolution.domain.vos import ProblemProfile
from evolution.infra.engines.llamea import LLaMEASession
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.domain.noise import NoNoiseStrategy
from shared.infra.database import Base, Database
from shared.infra.database.tables import ErrorLogORM, ExperimentORM, IterationORM
from shared.infra.problems.bbob import BBOBProblem


def add_completed(repository: SQLiteSynthesisRepository, problem: ProblemProfile) -> int:
    identifier = repository.create_experiment(
        problem, SynthesisMode.EXPLICIT, "test-model", synthesis_seed=43
    )
    with repository.SessionLocal.begin() as session:
        row = session.get(ExperimentORM, identifier)
        row.status = "completed"
        row.best_algorithm = "old-optimizer"
        row.best_iteration = 1
        row.best_final_error = 0.5
        row.finished_at = "previous-finish"
        iteration = IterationORM(
            experiment_id=identifier,
            algorithm_name="old-optimizer",
            final_error=0.5,
            runtime_seconds=1.0,
            llm_generation_time=0.1,
            evaluations_used=10,
            budget_consumed_pct=0.1,
            evals_per_second=10.0,
            raw_fitness=0.5,
            relative_error=0.5,
            error_per_evaluation=0.05,
            code_lines=1,
            code_length=10,
            code_path="old.py",
            convergence_threshold=1e-6,
        )
        iteration.error_log = ErrorLogORM(error_type="old-diagnostic", error_message="old failure")
        session.add(iteration)
    return identifier


def test_reset_retains_id_and_condition_and_preserves_other_experiments() -> None:
    database = Database("sqlite:///:memory:")
    try:
        Base.metadata.create_all(database.engine)
        repository = SQLiteSynthesisRepository(database.session_factory)
        profile = ProblemProfile(problem_id=1, dim=2, noise_std=0.0)
        selected = add_completed(repository, profile)
        untouched = add_completed(repository, profile)
        repository.reset_experiment(selected)
        summaries = {row.id: row for row in repository.load()}
        assert set(summaries) == {selected, untouched}
        reset = summaries[selected]
        assert reset.status == "running"
        assert reset.problem == profile
        assert reset.llm_name == "test-model"
        assert reset.synthesis_seed == 43
        assert reset.best_algorithm is None and reset.best_iteration is None
        assert reset.best_final_error is None and reset.finished_at is None
        assert reset.iterations == []
        assert summaries[untouched].status == "completed"
        assert len(summaries[untouched].iterations) == 1
        with database.engine.connect() as connection:
            assert connection.scalar(select(func.count()).select_from(ErrorLogORM)) == 1
        with pytest.raises(ValueError, match="Unknown experiment"):
            repository.reset_experiment(999)
    finally:
        database.dispose()


@pytest.mark.parametrize("restart", [False, True])
def test_execution_clears_old_state_only_for_explicit_replacement(
    tmp_path: Path, monkeypatch, restart: bool
) -> None:
    import evolution.infra.engines.llamea.runner as runner

    monkeypatch.setattr(runner, "DATA_DIR", tmp_path / "data")
    database = Database("sqlite:///:memory:")
    try:
        Base.metadata.create_all(database.engine)
        repository = SQLiteSynthesisRepository(database.session_factory)
        problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)
        identifier = add_completed(
            repository,
            ProblemProfile(
                problem_id=1,
                dim=2,
                noise_std=0.0,
                noise_model=problem.noise_model,
            ),
        )
        code_store = CodeRepository(base_dir=tmp_path / "code")
        old_code = code_store.save_code("old optimizer", 1, identifier)
        trailing_code = code_store.save_code("old trailing candidate", 9, identifier)
        other_code = code_store.save_code("unrelated optimizer", 1, identifier + 1)
        session = LLaMEASession(
            problem=problem,
            experiment_id=identifier,
            prompt_strategy=PromptStrategy.BASELINE,
            llm_client=SimpleNamespace(model=SimpleNamespace(name="test-model")),
            db_repo=repository,
            code_repo=code_store,
            config=SessionConfig(),
            initial_iteration=5,
            restart=restart,
        )
        checkpoint = session._archive_dir / "llamea_config.pkl"
        checkpoint.write_bytes(b"old checkpoint")
        result = SessionResult(
            problem_id=1,
            dim=2,
            mode=SynthesisMode.EXPLICIT,
            noise_std=0.0,
            experiment_id=identifier,
        )

        def fake_loop() -> tuple[object, object]:
            assert session._initial_iteration == (0 if restart else 5)
            assert checkpoint.exists() is not restart
            assert old_code.exists() is not restart
            assert trailing_code.exists() is not restart
            assert other_code.exists()
            assert repository.get_experiment_status(identifier) == (
                ("running", 0) if restart else ("completed", 1)
            )
            return object(), object()

        session._execute_loop = MagicMock(side_effect=fake_loop)
        session._process_session_result = MagicMock(return_value=result)
        assert session.run().experiment_id == identifier
        assert len(repository.load()) == 1
    finally:
        database.dispose()


def test_code_cleanup_refuses_symlinks(tmp_path: Path) -> None:
    destination = tmp_path / "unrelated"
    destination.mkdir()
    marker = destination / "keep.py"
    marker.write_text("keep")
    (tmp_path / "experiment_1").symlink_to(destination, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic-link"):
        CodeRepository(tmp_path).clear_experiment(1)
    assert marker.read_text() == "keep"
