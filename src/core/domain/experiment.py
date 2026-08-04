import math
from typing import Any

from pydantic import Field, field_validator

from core.domain.base import DomainEntity
from core.domain.iteration import IterationMetadata
from core.domain.problem import ProblemProfile


class ExperimentSummary(DomainEntity):
    """Aggregated result of a full LLaMEA evolution run."""

    mode: str = Field(description="Experiment running mode.", examples=["noisy", "clean"])
    llm_name: str = Field(
        description="Name of the LLM used to generate algorithm candidates.",
        examples=["qwen2.5-coder-7b-instruct-q4_k_m", "gpt-4o-mini"],
    )
    prompt_strategy: str = Field(
        default="baseline",
        description="Name of the prompt strategy used for algorithm synthesis.",
        examples=["baseline", "vectorization", "math_hints", "full_scaffold"],
    )
    budget: int | None = Field(
        default=None,
        description="Evaluation budget allocated per candidate algorithm run.",
        examples=[1000, 10000],
    )
    max_iterations: int | None = Field(
        default=None,
        description="Maximum synthesis iterations set for the experiment run.",
        examples=[10, 20],
    )
    status: str = Field(
        default="running",
        description="Current lifecycle status of the experiment: running, completed, or failed.",
        examples=["completed", "running", "failed"],
    )
    started_at: str | None = Field(
        default=None,
        description="ISO timestamp string when the experiment execution started.",
        examples=["2026-08-02T10:00:00+00:00", None],
    )
    finished_at: str | None = Field(
        default=None,
        description="ISO timestamp string when the experiment execution finished.",
        examples=["2026-08-02T10:15:00+00:00", None],
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
