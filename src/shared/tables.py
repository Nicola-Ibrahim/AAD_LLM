"""Shared declarative database models and schema definitions.

Defines `ExperimentORM`, `IterationORM`, `ErrorLogORM`, and `ExperimentMode`
shared across bounded contexts (evolution, benchmarking, analytics).
"""

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
    text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ExperimentMode(enum.StrEnum):
    CLEAN = "clean"
    NOISY = "noisy"
    IMPLICIT = "implicit"



class ExperimentORM(Base):
    """One row per experiment execution."""

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
    noise_model = Column(
        String, nullable=False, default="heteroscedastic", server_default=text("'heteroscedastic'")
    )
    budget = Column(Integer, nullable=True)  # Evaluation budget per iteration
    max_iterations = Column(Integer, nullable=True)  # Max synthesis iterations for the run

    true_optimum = Column(Float)

    # Summary/rollup fields, denormalized here for fast filtering/sorting
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
    """One row per LLM-generated-algorithm evaluation within an experiment run."""

    __tablename__ = "iterations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(
        Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )

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

    # Code artifact metadata
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
        Index("idx_iterations_exp_error", "experiment_id", "final_error"),
        CheckConstraint(
            "evaluations_used IS NULL OR evaluations_used >= 0",
            name="check_non_negative_evals",
        ),
    )


class ErrorLogORM(Base):
    """Separated concern: heavy text payloads (tracebacks, messages)."""

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
