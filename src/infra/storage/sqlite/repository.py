from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import sessionmaker

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
    ) -> int:
        """Creates the experiment DB row and returns its id."""
        with self.SessionLocal() as session:
            experiment = ExperimentORM(
                problem_id=problem_id,
                dim=dim,
                mode=ExperimentMode(mode),
                llm_name=llm_name,
                noise_std=noise_std,
                true_optimum=true_optimum,
                status="running",
                started_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(experiment)
            session.commit()
            session.refresh(experiment)
            return experiment.id

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
            flat_data["instance_id"] = experiment_meta.get("instance_id", 1)

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

            best_row = (
                session.query(IterationORM)
                .filter(
                    IterationORM.experiment_id == experiment_id,
                    IterationORM.final_error.isnot(None),
                )
                .order_by(IterationORM.final_error.asc())
                .first()
            )

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
        """Forces SQLite to flush WAL logs to the main db file by issuing a PRAGMA wal_checkpoint."""
        from sqlalchemy import text
        with self.SessionLocal() as session:
            session.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
            session.commit()

    def load(
        self,
        problem_id: int | None = None,
        llm_name: str | None = None,
        dim: int | None = None,
        mode: str | None = None,
    ) -> list[ExperimentSummary]:
        """Loads and filters ExperimentSummary objects from SQLite database using SQLAlchemy."""
        with self.SessionLocal() as session:
            query = session.query(ExperimentORM)
            if problem_id is not None:
                query = query.filter(ExperimentORM.problem_id == problem_id)
            if llm_name is not None:
                query = query.filter(ExperimentORM.llm_name == llm_name)
            if dim is not None:
                query = query.filter(ExperimentORM.dim == dim)
            if mode is not None:
                query = query.filter(ExperimentORM.mode == ExperimentMode(mode))

            experiments = query.order_by(
                ExperimentORM.problem_id.asc(), ExperimentORM.llm_name.asc()
            ).all()

            summaries: list[ExperimentSummary] = []
            for exp in experiments:
                instance_id = (
                    exp.iterations[0].instance_id
                    if exp.iterations and exp.iterations[0].instance_id
                    else 1
                )

                problem_profile = ProblemProfile(
                    problem_id=exp.problem_id,
                    dim=exp.dim,
                    noise_std=exp.noise_std or 0.0,
                    instance_id=instance_id,
                    true_optimum=exp.true_optimum,
                )

                iterations = [self._to_iteration_metadata(it) for it in exp.iterations]

                summaries.append(
                    ExperimentSummary(
                        mode=exp.mode.value,
                        llm_name=exp.llm_name,
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
                raw_fitness=it.raw_fitness if it.raw_fitness is not None else float("inf"),
                final_error=it.final_error if it.final_error is not None else float("inf"),
                relative_error=it.relative_error if it.relative_error is not None else float("inf"),
                error_per_evaluation=it.error_per_evaluation
                if it.error_per_evaluation is not None
                else float("inf"),
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
