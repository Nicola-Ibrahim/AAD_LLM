"""Experiment query filter Criteria Value Object."""

from pydantic import Field

from evolution.domain.base import ValueObject
from evolution.domain.enums import PromptStrategy, SynthesisMode


class ExperimentFilter(ValueObject):
    """Strongly-typed criteria Value Object for querying stored experiments."""

    experiment_id: int | None = Field(default=None, description="Primary key ID filter.")
    problem_id: int | None = Field(default=None, description="BBOB function ID filter (1-24).")
    instance_id: int | None = Field(default=None, description="BBOB instance ID filter.")
    llm_name: str | None = Field(default=None, description="LLM model name filter.")
    dim: int | None = Field(default=None, description="Dimension filter.")
    mode: SynthesisMode | None = Field(default=None, description="Synthesis mode filter.")
    prompt_strategy: PromptStrategy | None = Field(default=None, description="Prompt strategy filter.")
    status: str | None = Field(default=None, description="Experiment lifecycle status filter.")
