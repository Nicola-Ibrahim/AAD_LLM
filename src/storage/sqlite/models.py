from sqlalchemy import (
    Boolean,
    Column,
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
    llm_generation_time = Column(Float)
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
