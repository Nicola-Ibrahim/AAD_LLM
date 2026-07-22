import enum

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ExperimentMode(enum.Enum):
    CLEAN = "clean"
    NOISY = "noisy"


class ExperimentORM(Base):
    """
    One row per (problem, dim, mode, llm, noise_std, run_id) combination.
    `run_id` must be assigned explicitly by the orchestrator (e.g. a simple
    `for run_id in range(n_repetitions)` loop) -- never rely on a DB default
    or a max()+1 query for this, to avoid races under parallel execution.
    """

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    problem_id = Column(Integer, nullable=False)
    dim = Column(Integer, nullable=False)
    mode = Column(Enum(ExperimentMode), nullable=False)
    llm_name = Column(String, nullable=False)
    noise_std = Column(Float, nullable=True)  # NULL for CLEAN mode
    run_id = Column(Integer, nullable=False)  # explicit repetition index, assigned by caller

    true_optimum = Column(Float)

    # Summary/rollup fields, denormalized here for fast filtering/sorting
    # without touching the iterations table.
    best_iteration = Column(Integer)
    best_algorithm = Column(String)
    best_final_error = Column(Float)

    status = Column(String, default="running")  # running / completed / failed
    started_at = Column(String, server_default=text("(datetime('now'))"))
    finished_at = Column(String)

    iterations = relationship(
        "IterationORM",
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_experiments_lookup", "problem_id", "llm_name", "dim", "mode"),
        UniqueConstraint(
            "problem_id",
            "dim",
            "mode",
            "llm_name",
            "noise_std",
            "run_id",
            name="uq_experiment_run",
        ),
    )


class IterationORM(Base):
    """
    One row per LLM-generated-algorithm evaluation within an experiment run.
    Code-artifact metadata is kept inline here (not split out) since it's
    populated on nearly every row -- splitting it would just force a join
    on almost every analysis query.
    """

    __tablename__ = "iterations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(
        Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )

    iteration = Column(Integer, nullable=False)
    instance_id = Column(Integer)
    algorithm_name = Column(String)

    # Core metrics
    raw_fitness = Column(Float)
    final_error = Column(Float)
    relative_error = Column(Float)
    error_per_evaluation = Column(Float)

    timed_out = Column(Boolean, default=False)
    converged = Column(Boolean, default=False)
    convergence_threshold = Column(Float)

    runtime_seconds = Column(Float)
    llm_generation_time = Column(Float)
    evaluations_used = Column(Integer)
    budget_consumed_pct = Column(Float)
    evals_per_second = Column(Float)

    # Code artifact metadata (kept inline -- see class docstring)
    code_lines = Column(Integer)
    code_length = Column(Integer)
    code_path = Column(String)

    experiment = relationship("ExperimentORM", back_populates="iterations")
    error_log = relationship(
        "ErrorLogORM",
        back_populates="iteration",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_iterations_experiment", "experiment_id"),
        # Speeds up groupby/analysis queries that filter or sort by iteration
        # number within an experiment (e.g. convergence curves).
        Index("idx_iterations_experiment_iter", "experiment_id", "iteration"),
        UniqueConstraint(
            "experiment_id",
            "instance_id",
            "iteration",
            name="uq_iteration_identity",
        ),
    )


class ErrorLogORM(Base):
    """
    Separated concern: heavy text payloads (tracebacks, messages) that are
    NULL on the large majority of successful iterations. Keeping these out
    of IterationORM keeps that table lean for dataframe loads.
    """

    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    iteration_id = Column(
        Integer,
        ForeignKey("iterations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    error_type = Column(String)
    error_message = Column(String)
    error_traceback = Column(String)

    iteration = relationship("IterationORM", back_populates="error_log")
