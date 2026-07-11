from pathlib import Path
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    event,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from schema import ExperimentSummary, IterationMetadata
from storage.base import ExperimentStore

Base = declarative_base()


class ExperimentORM(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, nullable=False)
    dim = Column(Integer, nullable=False)
    mode = Column(String, nullable=False)
    llm_name = Column(String, nullable=False)
    noise_std = Column(Float)
    true_optimum = Column(Float)
    best_iteration = Column(Integer)
    best_algorithm = Column(String)
    best_final_error = Column(Float)
    created_at = Column(String, server_default=text("(datetime('now'))"))

    iterations = relationship(
        "IterationORM",
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_experiments", "problem_id", "llm_name", "dim", "mode"),
        UniqueConstraint("problem_id", "dim", "mode", "llm_name", name="uq_experiment_run"),
    )


class IterationORM(Base):
    __tablename__ = "iterations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(
        Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    iteration = Column(Integer)
    instance_id = Column(Integer)
    algorithm_name = Column(String)
    raw_fitness = Column(Float)
    final_error = Column(Float)
    true_optimum = Column(Float)
    noise_std = Column(Float)
    timed_out = Column(Boolean)
    runtime_seconds = Column(Float)
    evaluations_used = Column(Integer)
    budget_consumed_pct = Column(Float)
    relative_error = Column(Float)
    evals_per_second = Column(Float)
    error_per_evaluation = Column(Float)
    converged = Column(Boolean)
    convergence_threshold = Column(Float)
    code_lines = Column(Integer)
    code_length = Column(Integer)
    code_path = Column(String)
    error_type = Column(String)
    error_message = Column(String)
    error_traceback = Column(String)

    experiment = relationship("ExperimentORM", back_populates="iterations")

    __table_args__ = (Index("idx_iterations_experiment", "experiment_id"),)


class SQLiteStore(ExperimentStore):
    """SQLite-based storage backend for LLaMEA experiment summaries using SQLAlchemy ORM."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

        # Ensure parent directories exist
        if self.db_path.parent:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._init_db()

    @property
    def base_dir(self) -> Path:
        """Returns the base directory for storing blobs, which is the directory containing the SQLite DB."""
        return self.db_path.parent

    def _init_db(self) -> None:
        """Initializes database schema and indexes."""

        # SQLite foreign keys must be enabled on every connection
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # Create tables if they do not exist
        Base.metadata.create_all(self.engine)

    def save(self, summary: ExperimentSummary) -> None:
        """Saves or updates an ExperimentSummary in the SQLite database using SQLAlchemy."""
        with self.SessionLocal() as session:
            # 1. Look for existing experiment
            existing = (
                session.query(ExperimentORM)
                .filter_by(
                    problem_id=summary.problem_id,
                    dim=summary.dim,
                    mode=summary.mode,
                    llm_name=summary.llm_name,
                )
                .first()
            )

            if existing:
                session.delete(existing)
                session.flush()  # Cascade deletes iterations immediately

            # 2. Map Pydantic model to ORM models
            experiment = ExperimentORM(
                problem_id=summary.problem_id,
                dim=summary.dim,
                mode=summary.mode,
                llm_name=summary.llm_name,
                noise_std=summary.noise_std,
                true_optimum=summary.true_optimum,
                best_iteration=summary.best_iteration,
                best_algorithm=summary.best_algorithm,
                best_final_error=summary.best_final_error,
            )

            for it in summary.iterations:
                it_dict = it.model_dump()
                # filter keys to only columns that exist in IterationORM
                filtered_dict = {
                    k: v for k, v in it_dict.items() if k in IterationORM.__table__.columns
                }
                iteration = IterationORM(**filtered_dict)
                experiment.iterations.append(iteration)

            session.add(experiment)
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
                query = query.filter(ExperimentORM.mode == mode)

            query = query.order_by(ExperimentORM.problem_id.asc(), ExperimentORM.llm_name.asc())
            experiments = query.all()

            summaries: list[ExperimentSummary] = []
            for exp in experiments:
                iterations = []
                for it in exp.iterations:
                    # Map SQLAlchemy ORM model to IterationMetadata Pydantic model
                    it_dict = {
                        col.name: getattr(it, col.name)
                        for col in it.__table__.columns
                        if col.name != "id" and col.name != "experiment_id"
                    }
                    # Populate values that are at the iteration metadata level
                    it_dict["problem_id"] = exp.problem_id
                    it_dict["dim"] = exp.dim
                    if "noise_std" not in it_dict or it_dict["noise_std"] is None:
                        it_dict["noise_std"] = exp.noise_std
                    if "true_optimum" not in it_dict or it_dict["true_optimum"] is None:
                        it_dict["true_optimum"] = exp.true_optimum

                    iterations.append(IterationMetadata(**it_dict))

                summaries.append(
                    ExperimentSummary(
                        problem_id=exp.problem_id,
                        dim=exp.dim,
                        mode=exp.mode,
                        llm_name=exp.llm_name,
                        noise_std=exp.noise_std,
                        true_optimum=exp.true_optimum,
                        best_iteration=exp.best_iteration,
                        best_algorithm=exp.best_algorithm,
                        best_final_error=exp.best_final_error,
                        iterations=iterations,
                    )
                )
        return summaries

    def print_table(self) -> None:
        """Prints a formatted table of all saved summaries in the SQLite database."""
        summaries = self.load()
        if not summaries:
            print(f"No experiment summaries found in database '{self.db_path}'.")
            return

        lines = [
            "=======================================================================================================================",
            "Experiment Results - Collected Summaries from SQLite Database",
            "=======================================================================================================================",
            f"{'Problem ID':<10} | {'Dim':<5} | {'Mode':<8} | {'LLM Target':<35} | {'Best Error':<12} | {'Best Algorithm'}",
            "-----------|-------|----------|-------------------------------------|--------------|-----------------------------------",
        ]
        for s in summaries:
            pid = s.problem_id
            dim = s.dim
            mode = s.mode
            llm = s.llm_name
            best_err = s.best_final_error
            best_err_str = (
                f"{best_err:.4f}"
                if isinstance(best_err, (int, float)) and best_err != float("inf")
                else "FAILED"
            )
            best_algo = s.best_algorithm or "N/A"
            lines.append(
                f"{pid:<10} | {dim:<5} | {mode:<8} | {llm:<35} | {best_err_str:<12} | {best_algo}"
            )
        lines.append(
            "======================================================================================================================="
        )
        print("\n".join(lines))
