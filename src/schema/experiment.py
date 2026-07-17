import math
from typing import Any
from pydantic import BaseModel, Field, field_validator


class ExecutionProfile(BaseModel):
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
    converged: bool = Field(
        description="True if the algorithm achieved a final error lower than the convergence threshold.",
        examples=[False, True],
    )
    convergence_threshold: float = Field(
        description="The target error difference threshold needed to consider a run converged.",
        examples=[1e-06],
    )


class ProblemProfile(BaseModel):
    problem_id: int = Field(
        description="The BBOB problem ID representing the objective function.", examples=[1, 14, 24]
    )
    dim: int = Field(
        description="Dimension of the search space of the BBOB problem.", examples=[2, 5, 10, 20]
    )
    noise_std: float = Field(
        description="Standard deviation of the Gaussian noise added to the clean evaluations.",
        examples=[0.0, 0.1, 1.0],
    )
    instance_id: int = Field(
        description="The BBOB instance ID chosen for this problem execution run.", examples=[1, 5]
    )
    true_optimum: float | None = Field(
        default=None,
        description="The actual clean theoretical optimum value of the objective function (if known).",
        examples=[79.48],
    )


class IterationMetadata(BaseModel):
    """Structured result of one algorithm evaluation by the Evaluator."""

    iteration: int | None = Field(
        default=None,
        description="The 1-based index representing the generation or iteration of the evolution loop.",
        examples=[1, 5, 10],
    )
    algorithm_name: str = Field(
        description="Name of the generated algorithm candidate.",
        examples=["NoisyHillClimber", "RandomSearchAlgorithm"],
    )

    execution: ExecutionProfile = Field(
        description="Timing and throughput metrics for the iteration's execution run."
    )
    fitness: FitnessMetrics = Field(
        description="Fitness metrics and errors achieved by the candidate algorithm."
    )
    code: CodeMetrics = Field(
        description="Attributes and metadata about the candidate algorithm code."
    )
    error: ErrorProfile = Field(
        description="Traceback and exception info if the candidate algorithm failed."
    )
    convergence: ConvergenceProfile = Field(
        description="Details about convergence of the execution run."
    )

    def to_json_dict(self) -> dict[str, Any]:
        """Return a plain dict safe for JSON serialization."""
        return self.model_dump(mode="json")


class ExperimentSummary(BaseModel):
    """Aggregated result of a full LLaMEA evolution run."""

    mode: str = Field(description="Experiment running mode.", examples=["noisy", "clean"])
    llm_name: str = Field(
        description="Name of the LLM used to generate algorithm candidates.",
        examples=["qwen2.5-coder-7b-instruct-q4_k_m", "gpt-4o-mini"],
    )
    run_id: int = Field(
        default=1,
        description="Explicit repetition index assigned by the orchestrator."
    )
    problem: ProblemProfile = Field(
        description="Configuration of the BBOB problem for this execution run."
    )
    best_iteration: int | None = Field(
        default=None,
        description="The 1-based iteration index that produced the minimum final error.",
        examples=[8, None],
    )
    best_algorithm: str | None = Field(
        default=None,
        description="Name of the best-performing algorithm iteration.",
        examples=["NoisyHillClimber", None],
    )
    best_final_error: float | None = Field(
        default=None,
        description="The minimum final error achieved across all iterations in this run.",
        examples=[0.0001, None],
    )
    iterations: list[IterationMetadata] = Field(
        description="List of individual iteration metadata records."
    )

    @field_validator("best_final_error", mode="before")
    @classmethod
    def sanitize_best_error(cls, v: Any) -> Any:
        if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
            return None
        return v

    def to_json_dict(self) -> dict[str, Any]:
        """Return a plain dict safe for JSON serialization."""
        return self.model_dump(mode="json")
