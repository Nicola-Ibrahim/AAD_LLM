from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, sessionmaker

from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import NoiseModelEnum, ProblemMode
from evolution.domain.vos import (
    Code,
    Convergence,
    Error,
    Execution,
    Fitness,
    IterationMetadata,
    ProblemProfile,
)
from evolution.infra.storage.base import ExperimentRepository
from evolution.infra.storage.sqlite.tables import ErrorLogORM, ExperimentMode, ExperimentORM, IterationORM


class SQLiteExperimentRepository(ExperimentRepository):
    """SQLite-based repository for LLaMEA experiment summaries and session state management using SQLAlchemy ORM."""

    def __init__(self, session_factory: sessionmaker):
        self.SessionLocal = session_factory

    def __getstate__(self) -> dict[str, Any]:
        """Strip non-picklable SQLAlchemy session_factory before serialization."""
        state = self.__dict__.copy()
        state.pop("SessionLocal", None)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore state for process workers (SessionLocal will be None if unpickled directly)."""
        self.__dict__.update(state)
        self.SessionLocal = state.get("SessionLocal", None)

    def create_experiment(
        self,
        problem: ProblemProfile,
        mode: ProblemMode | str,
        llm_name: str,
        prompt_strategy: str = "baseline",
        budget: int = 1000000,
        iterations: int = 10,
    ) -> int:
        """Creates the experiment DB row and returns its id."""
        mode_str = mode.value if hasattr(mode, "value") else str(mode)
        noise_model_str = (
            problem.noise_model.value
            if hasattr(problem.noise_model, "value")
            else str(problem.noise_model)
        )
        with self.SessionLocal() as session:
            experiment = ExperimentORM(
                problem_id=problem.problem_id,
                instance_id=problem.instance_id,
                dim=problem.dim,
                mode=ExperimentMode(mode_str),
                llm_name=llm_name,
                prompt_strategy=prompt_strategy,
                noise_std=problem.noise_std,
                noise_model=noise_model_str,
                budget=budget,
                max_iterations=iterations,
                true_optimum=problem.true_optimum,
                status="running",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(experiment)
            session.commit()
            session.refresh(experiment)
            return experiment.id

    def get_experiment_status(self, experiment_id: int) -> tuple[str | None, int]:
        """Returns tuple of (status_string, max_iteration_number) for an experiment, or (None, 0) if not found."""
        with self.SessionLocal() as session:
            exp = session.get(ExperimentORM, experiment_id)
            if not exp:
                return None, 0
            stmt = select(func.count(IterationORM.id)).where(
                IterationORM.experiment_id == experiment_id
            )
            count_iter = session.execute(stmt).scalar()
            return exp.status, count_iter if count_iter is not None else 0

    @staticmethod
    def _from_iteration_metadata(
        experiment_id: int, metadata: IterationMetadata
    ) -> tuple[IterationORM, ErrorLogORM | None]:
        """Explicit domain IterationMetadata to ORM mapper."""
        iteration_orm = IterationORM(
            experiment_id=experiment_id,
            algorithm_name=metadata.algorithm_name,
            timed_out=metadata.execution.timed_out,
            runtime_seconds=metadata.execution.runtime_seconds,
            llm_generation_time=metadata.execution.llm_generation_time,
            evaluations_used=metadata.execution.evaluations_used,
            budget_consumed_pct=metadata.execution.budget_consumed_pct,
            evals_per_second=metadata.execution.evals_per_second,
            raw_fitness=metadata.fitness.raw_fitness,
            final_error=metadata.fitness.final_error,
            relative_error=metadata.fitness.relative_error,
            error_per_evaluation=metadata.fitness.error_per_evaluation,
            code_lines=metadata.code.code_lines,
            code_length=metadata.code.code_length,
            code_path=metadata.code.code_path,
            converged=metadata.convergence.converged,
            convergence_threshold=metadata.convergence.convergence_threshold,
        )

        error_orm = None
        if metadata.error.error_type:
            error_orm = ErrorLogORM(
                error_type=metadata.error.error_type,
                error_message=metadata.error.error_message,
                error_traceback=metadata.error.error_traceback,
            )

        return iteration_orm, error_orm

    def append_iteration(
        self,
        experiment_id: int,
        metadata: IterationMetadata,
    ) -> None:
        """Inserts one IterationORM row per call. Each call is its own committed transaction."""
        iteration_orm, error_orm = self._from_iteration_metadata(experiment_id, metadata)
        if error_orm:
            iteration_orm.error_log = error_orm

        with self.SessionLocal() as session:
            session.add(iteration_orm)
            session.commit()

    def mark_completed(self, experiment_id: int) -> None:
        """Marks experiment completed and computes best_* rollup fields from the iterations table."""
        with self.SessionLocal() as session:
            exp = session.get(ExperimentORM, experiment_id)
            if not exp:
                print(f"[WARN] mark_completed: no experiment row for id={experiment_id}")
                return

            stmt = (
                select(IterationORM)
                .where(
                    IterationORM.experiment_id == experiment_id,
                    IterationORM.final_error.isnot(None),
                )
                .order_by(IterationORM.final_error.asc())
            )
            best_row = session.execute(stmt).scalars().first()

            if best_row:
                count_stmt = select(func.count(IterationORM.id)).where(
                    IterationORM.experiment_id == experiment_id,
                    IterationORM.id <= best_row.id,
                )
                exp.best_iteration = session.execute(count_stmt).scalar()
                exp.best_algorithm = best_row.algorithm_name
                exp.best_final_error = best_row.final_error

            exp.status = "completed"
            exp.finished_at = datetime.now(timezone.utc).isoformat()
            session.commit()

        self.checkpoint_wal()

    def mark_failed(self, experiment_id: int, reason: str = "") -> None:
        """Marks an experiment as failed so it is not left as 'running' forever."""
        with self.SessionLocal() as session:
            exp = session.get(ExperimentORM, experiment_id)
            if exp:
                exp.status = "failed"
                exp.finished_at = datetime.now(timezone.utc).isoformat()
                session.commit()

        self.checkpoint_wal()

    def checkpoint_wal(self) -> None:
        """Flushes WAL log frames to the main database file using PASSIVE mode without truncating or deleting the WAL file."""
        if not self.SessionLocal:
            return
        from sqlalchemy import text

        try:
            with self.SessionLocal() as session:
                session.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
                session.commit()
        except Exception as e:
            print(f"[WARN] checkpoint_wal failed non-fatally: {e}")

    def get_best_raw_fitness(self, experiment_id: int) -> float | None:
        """Returns the raw algorithm objective value from the best (lowest-error) iteration of an experiment."""
        stmt = (
            select(IterationORM.raw_fitness)
            .where(
                IterationORM.experiment_id == experiment_id,
                IterationORM.final_error.isnot(None),
                IterationORM.raw_fitness.isnot(None),
            )
            .order_by(IterationORM.final_error.asc())
        )
        with self.SessionLocal() as session:
            best_val = session.execute(stmt).scalar()
            return float(best_val) if best_val is not None else None

    def load(
        self,
        experiment_id: int | None = None,
        problem_id: int | None = None,
        instance_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
        prompt_strategy: str | None = None,
        status: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters ExperimentSummary objects from SQLite database using SQLAlchemy 2.0 select."""
        stmt = select(ExperimentORM).options(
            selectinload(ExperimentORM.iterations).selectinload(IterationORM.error_log)
        )

        raw_filters = {
            "id": experiment_id,
            "problem_id": problem_id,
            "instance_id": instance_id,
            "llm_name": llm_name,
            "dim": dim,
            "prompt_strategy": prompt_strategy,
            "status": status,
        }
        active_filters = {k: v for k, v in raw_filters.items() if v is not None}
        if active_filters:
            stmt = stmt.filter_by(**active_filters)

        if mode is not None:
            stmt = stmt.where(ExperimentORM.mode == ExperimentMode(mode))

        stmt = stmt.order_by(ExperimentORM.problem_id.asc(), ExperimentORM.llm_name.asc())

        with self.SessionLocal() as session:
            experiments = session.scalars(stmt).all()

            summaries: list[ExperimentSummary] = []
            for exp in experiments:
                problem_profile = ProblemProfile(
                    problem_id=exp.problem_id,
                    dim=exp.dim,
                    noise_std=exp.noise_std or 0.0,
                    noise_model=NoiseModelEnum(exp.noise_model)
                    if exp.noise_model
                    else NoiseModelEnum.MULTIPLICATIVE,
                    instance_id=exp.instance_id,
                    true_optimum=exp.true_optimum,
                )

                iterations = [
                    self._to_iteration_metadata(it, idx)
                    for idx, it in enumerate(exp.iterations, start=1)
                ]

                summaries.append(
                    ExperimentSummary(
                        mode=exp.mode.value,
                        llm_name=exp.llm_name,
                        prompt_strategy=exp.prompt_strategy or "baseline",
                        budget=exp.budget,
                        max_iterations=exp.max_iterations,
                        id=exp.id,
                        status=exp.status,
                        started_at=exp.started_at,
                        finished_at=exp.finished_at,
                        problem=problem_profile,
                        best_iteration=exp.best_iteration,
                        best_algorithm=exp.best_algorithm,
                        best_final_error=exp.best_final_error,
                        iterations=iterations,
                    )
                )
        return summaries

    @staticmethod
    def _to_iteration_metadata(
        it: IterationORM, iteration_number: int | None = None
    ) -> IterationMetadata:
        """Helper to convert an IterationORM database instance into an IterationMetadata schema object."""
        error_fields = {
            "error_type": it.error_log.error_type if it.error_log else None,
            "error_message": it.error_log.error_message if it.error_log else None,
            "error_traceback": it.error_log.error_traceback if it.error_log else None,
        }

        return IterationMetadata(
            algorithm_name=it.algorithm_name,
            iteration=iteration_number,
            execution=Execution(
                timed_out=it.timed_out,
                runtime_seconds=it.runtime_seconds,
                llm_generation_time=it.llm_generation_time,
                evaluations_used=it.evaluations_used,
                budget_consumed_pct=it.budget_consumed_pct,
                evals_per_second=it.evals_per_second,
            ),
            fitness=Fitness(
                raw_fitness=it.raw_fitness,
                final_error=it.final_error,
                relative_error=it.relative_error,
                error_per_evaluation=it.error_per_evaluation,
            ),
            code=Code(
                code_lines=it.code_lines,
                code_length=it.code_length,
                code_path=it.code_path,
            ),
            error=Error(**error_fields),
            convergence=Convergence(
                converged=it.converged,
                convergence_threshold=it.convergence_threshold,
            ),
        )
