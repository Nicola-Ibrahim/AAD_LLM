from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload, sessionmaker

from core.schema.experiment import ExperimentSummary
from core.schema.iteration import (
    CodeMetrics,
    ConvergenceProfile,
    ErrorProfile,
    ExecutionProfile,
    FitnessMetrics,
    IterationMetadata,
)
from core.schema.problem import ProblemProfile
from infra.storage.base import ExperimentRepository
from infra.storage.sqlite.tables import ErrorLogORM, ExperimentMode, ExperimentORM, IterationORM


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
        problem_id: int,
        dim: int,
        mode: str,
        llm_name: str,
        noise_std: float,
        true_optimum: float,
        instance_id: int = 1,
        prompt_strategy: str = "baseline",
    ) -> int:
        """Creates the experiment DB row and returns its id."""
        with self.SessionLocal() as session:
            experiment = ExperimentORM(
                problem_id=problem_id,
                instance_id=instance_id,
                dim=dim,
                mode=ExperimentMode(mode),
                llm_name=llm_name,
                prompt_strategy=prompt_strategy,
                noise_std=noise_std,
                true_optimum=true_optimum,
                status="running",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(experiment)
            session.commit()
            session.refresh(experiment)
            return experiment.id

    def get_incomplete_experiments(
        self,
        problem_id: int,
        dim: int,
        mode: str,
        llm_name: str,
        noise_std: float,
        instance_id: int = 1,
        prompt_strategy: str = "baseline",
    ) -> list[int]:
        """Returns a list of experiment IDs with status 'running' that match the given parameters."""
        stmt = select(ExperimentORM.id).where(
            ExperimentORM.problem_id == problem_id,
            ExperimentORM.instance_id == instance_id,
            ExperimentORM.dim == dim,
            ExperimentORM.mode == ExperimentMode(mode),
            ExperimentORM.llm_name == llm_name,
            ExperimentORM.prompt_strategy == prompt_strategy,
            ExperimentORM.status == "running",
        )
        if noise_std > 0.0:
            stmt = stmt.where(ExperimentORM.noise_std == noise_std)
        else:
            stmt = stmt.where(
                (ExperimentORM.noise_std == 0.0) | (ExperimentORM.noise_std.is_(None))
            )
        stmt = stmt.order_by(ExperimentORM.id.asc())

        with self.SessionLocal() as session:
            rows = session.execute(stmt).scalars().all()
            return list(rows)

    def get_experiment_status(self, experiment_id: int) -> tuple[str | None, int]:
        """Returns tuple of (status_string, max_iteration_number) for an experiment, or (None, 0) if not found."""
        with self.SessionLocal() as session:
            exp = session.get(ExperimentORM, experiment_id)
            if not exp:
                return None, 0
            stmt = select(func.max(IterationORM.iteration)).where(
                IterationORM.experiment_id == experiment_id
            )
            max_iter = session.execute(stmt).scalar()
            return exp.status, max_iter if max_iter is not None else 0

    def append_iteration(
        self,
        experiment_id: int,
        metadata: IterationMetadata,
        experiment_meta: dict[str, Any],
    ) -> None:
        """Inserts one IterationORM row per call. Each call is its own committed transaction."""
        with self.SessionLocal() as session:
            it_dict = metadata.model_dump()

            # Flatten nested profiles (execution, fitness, code, error, convergence)
            flat_data = {}
            for key, value in it_dict.items():
                if isinstance(value, dict):
                    flat_data.update(value)
                else:
                    flat_data[key] = value

            flat_data["experiment_id"] = experiment_id

            # Filter fields to only columns defined on IterationORM
            valid_columns = IterationORM.__table__.columns.keys()
            filtered_data = {k: v for k, v in flat_data.items() if k in valid_columns}
            iteration_orm = IterationORM(**filtered_data)

            error_dict = it_dict.get("error") or {}
            if error_dict.get("error_type"):
                iteration_orm.error_log = ErrorLogORM(
                    error_type=error_dict["error_type"],
                    error_message=error_dict.get("error_message"),
                    error_traceback=error_dict.get("error_traceback"),
                )

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
                exp.best_iteration = best_row.iteration
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
        problem_id: int | None = None,
        instance_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
        prompt_strategy: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters ExperimentSummary objects from SQLite database using SQLAlchemy 2.0 select."""
        stmt = select(ExperimentORM).options(
            selectinload(ExperimentORM.iterations).selectinload(IterationORM.error_log)
        )

        raw_filters = {
            "problem_id": problem_id,
            "instance_id": instance_id,
            "llm_name": llm_name,
            "dim": dim,
            "prompt_strategy": prompt_strategy,
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
                    instance_id=exp.instance_id,
                    true_optimum=exp.true_optimum,
                )

                iterations = [self._to_iteration_metadata(it) for it in exp.iterations]

                summaries.append(
                    ExperimentSummary(
                        mode=exp.mode.value,
                        llm_name=exp.llm_name,
                        prompt_strategy=exp.prompt_strategy or "baseline",
                        experiment_id=exp.id,
                        problem=problem_profile,
                        best_iteration=exp.best_iteration,
                        best_algorithm=exp.best_algorithm,
                        best_final_error=exp.best_final_error,
                        iterations=iterations,
                    )
                )
        return summaries

    @staticmethod
    def _to_iteration_metadata(it: IterationORM) -> IterationMetadata:
        """Helper to convert an IterationORM database instance into an IterationMetadata schema object."""
        error_fields = {
            "error_type": it.error_log.error_type if it.error_log else None,
            "error_message": it.error_log.error_message if it.error_log else None,
            "error_traceback": it.error_log.error_traceback if it.error_log else None,
        }

        return IterationMetadata(
            algorithm_name=it.algorithm_name,
            iteration=it.iteration,
            execution=ExecutionProfile(
                timed_out=it.timed_out,
                runtime_seconds=it.runtime_seconds,
                llm_generation_time=it.llm_generation_time,
                evaluations_used=it.evaluations_used,
                budget_consumed_pct=it.budget_consumed_pct,
                evals_per_second=it.evals_per_second,
            ),
            fitness=FitnessMetrics(
                raw_fitness=it.raw_fitness,
                final_error=it.final_error,
                relative_error=it.relative_error,
                error_per_evaluation=it.error_per_evaluation,
            ),
            code=CodeMetrics(
                code_lines=it.code_lines,
                code_length=it.code_length,
                code_path=it.code_path,
            ),
            error=ErrorProfile(**error_fields),
            convergence=ConvergenceProfile(
                converged=it.converged,
                convergence_threshold=it.convergence_threshold,
            ),
        )
