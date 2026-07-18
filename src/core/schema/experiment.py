import math
from typing import Any
from pydantic import BaseModel, Field, field_validator

from core.schema.problem import ProblemProfile
from core.schema.iteration import IterationMetadata


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
