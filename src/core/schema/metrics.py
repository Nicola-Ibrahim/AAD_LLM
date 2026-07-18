import math
from typing import Any
from pydantic import BaseModel, Field, field_validator


class ExecutionProfile(BaseModel):
    """Timing and throughput metrics for candidate algorithm execution."""

    timed_out: bool = Field(
        description="True if the candidate algorithm exceeded the CPU time limit during execution.",
        examples=[False, True],
    )
    runtime_seconds: float = Field(
        description="Wall-clock runtime of the candidate algorithm execution in seconds.",
        examples=[0.45],
    )
    llm_generation_time: float | None = Field(
        default=None,
        description="Time taken by the LLM to generate the candidate algorithm source code in seconds.",
        examples=[4.5, None],
    )
    evaluations_used: int = Field(
        description="Number of clean objective function evaluations consumed by the algorithm before stopping.",
        examples=[1000],
    )
    budget_consumed_pct: float = Field(
        description="Percentage of the evaluation budget consumed during execution.",
        examples=[100.0],
    )
    evals_per_second: float = Field(
        description="Execution throughput measured in evaluations per second.", examples=[2222.2]
    )


class FitnessMetrics(BaseModel):
    """Objective values, errors, and noise properties for candidate execution."""

    raw_fitness: float | None = Field(
        default=None,
        description="The raw objective function score returned by the executed algorithm (with noise included).",
        examples=[80.12, None],
    )
    final_error: float | None = Field(
        default=None,
        description="The absolute difference between the true optimum and the best clean fitness achieved.",
        examples=[0.64, None],
    )
    relative_error: float | None = Field(
        default=None,
        description="Relative error ratio computed as final_error / true_optimum.",
        examples=[0.008, None],
    )
    error_per_evaluation: float | None = Field(
        default=None,
        description="The average error rate per evaluation (final_error / evaluations_used).",
        examples=[0.00064, None],
    )

    @field_validator(
        "raw_fitness",
        "final_error",
        "relative_error",
        "error_per_evaluation",
        mode="before",
    )
    @classmethod
    def sanitize_non_finite_floats(cls, v: Any) -> Any:
        if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
            return None
        return v


class CodeMetrics(BaseModel):
    """Metadata regarding generated Python source code."""

    code_lines: int = Field(
        description="The number of line breaks in the candidate algorithm source code.",
        examples=[42],
    )
    code_length: int = Field(
        description="The character length of the candidate algorithm source code.", examples=[1250]
    )
    code_path: str | None = Field(
        default=None,
        description="Path to the file containing the generated candidate algorithm source code.",
        examples=["data/code/bbob_1_dim5_noisy/iter_1.py", None],
    )


class ErrorProfile(BaseModel):
    """Exception traceback details if evaluation failed."""

    error_type: str | None = Field(
        default=None,
        description="Class name of the Python exception raised if evaluation failed.",
        examples=["ZeroDivisionError", "SyntaxError", None],
    )
    error_message: str | None = Field(
        default=None,
        description="Message content of the raised exception.",
        examples=["division by zero", None],
    )
    error_traceback: str | None = Field(
        default=None,
        description="Complete Python traceback trace of the raised exception.",
        examples=['Traceback (most recent call last):\n  File "...", line 15, in...', None],
    )


class ConvergenceProfile(BaseModel):
    """Resiliency and convergence details for candidate executions."""

    converged: bool = Field(
        description="True if the algorithm achieved a final error lower than the convergence threshold.",
        examples=[False, True],
    )
    convergence_threshold: float = Field(
        description="The target error difference threshold needed to consider a run converged.",
        examples=[1e-06],
    )
