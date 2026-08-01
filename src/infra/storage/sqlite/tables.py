import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
    One row per experiment execution.
    `id` is the primary key and serves as the globally unique experiment identifier.
    """

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    problem_id = Column(Integer, nullable=False)
    instance_id = Column(Integer, nullable=False, default=1, server_default=text("1"))
    dim = Column(Integer, nullable=False)
    mode = Column(Enum(ExperimentMode), nullable=False)
    llm_name = Column(String, nullable=False)
    prompt_strategy = Column(
        String, nullable=False, default="baseline", server_default=text("'baseline'")
    )
    noise_std = Column(Float, nullable=True)  # NULL for CLEAN mode

    true_optimum = Column(Float)

    # Summary/rollup fields, denormalized here for fast filtering/sorting
    # without touching the iterations table.
    best_iteration = Column(Integer)
    best_algorithm = Column(String)
    best_final_error = Column(Float, nullable=True)

    status = Column(String, nullable=False, default="running")  # running / completed / failed
    started_at = Column(String, nullable=False, server_default=text("(datetime('now'))"))
    finished_at = Column(String)

    iterations = relationship(
        "IterationORM",
        back_populates="experiment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "idx_experiments_lookup",
            "problem_id",
            "instance_id",
            "llm_name",
            "dim",
            "mode",
            "prompt_strategy",
        ),
        Index("idx_experiments_status", "status"),
        CheckConstraint("dim > 0", name="check_positive_dim"),
        CheckConstraint("status IN ('running', 'completed', 'failed')", name="check_valid_status"),
        CheckConstraint("noise_std IS NULL OR noise_std >= 0", name="check_non_negative_noise"),
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
    algorithm_name = Column(String)

    # Core metrics
    raw_fitness = Column(Float, nullable=True)
    final_error = Column(Float, nullable=True)
    relative_error = Column(Float, nullable=True)
    error_per_evaluation = Column(Float, nullable=True)

    timed_out = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    converged = Column(Boolean, nullable=False, default=False, server_default=text("0"))
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
        # Speeds up groupby/analysis queries that filter or sort by iteration
        # number within an experiment (e.g. convergence curves).
        Index("idx_iterations_experiment_iter", "experiment_id", "iteration"),
        Index("idx_iterations_exp_error", "experiment_id", "final_error"),
        UniqueConstraint(
            "experiment_id",
            "iteration",
            name="uq_iteration_identity",
        ),
        CheckConstraint("iteration >= 0", name="check_non_negative_iteration"),
        CheckConstraint(
            "evaluations_used IS NULL OR evaluations_used >= 0",
            name="check_non_negative_evals",
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
    error_type = Column(String, nullable=False)
    error_message = Column(String)
    error_traceback = Column(String)

    iteration = relationship("IterationORM", back_populates="error_log")
