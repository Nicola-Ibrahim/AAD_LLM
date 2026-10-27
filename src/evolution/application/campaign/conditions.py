"""Campaign condition definitions, identity and experiment classification."""

from collections import defaultdict

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from evolution.domain.entities import ExperimentSummary
from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.noise_model import NoiseModelEnum


class ProblemTarget(BaseModel):
    """Target BBOB problem ID and its evaluated search space dimensions."""

    id: int = Field(ge=1, le=24)
    dimensions: list[int] = Field(min_length=1)

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, values: list[int]) -> list[int]:
        if any(value <= 0 for value in values):
            raise ValueError("Dimensions must be positive integers.")
        return values

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")


class SynthesisModeConfig(BaseModel):
    """Synthesis prompting mode and its evaluated prompt engineering strategies."""

    mode: SynthesisMode
    strategies: list[PromptStrategy] = Field(min_length=1)

    model_config = ConfigDict(frozen=True, extra="forbid")


class NoiseConditionConfig(BaseModel):
    """An explicitly selected noise level and model."""

    std: float = Field(strict=True, ge=0, allow_inf_nan=False)
    noise_model: NoiseModelEnum = NoiseModelEnum.NONE

    model_config = ConfigDict(frozen=True, extra="forbid")


class MatrixCondition(BaseModel):
    """Discrete, pre-computed search matrix unit ready for evaluation or dispatch."""

    problem_id: int
    dim: int
    mode: SynthesisMode
    noise_std: float
    noise_model: NoiseModelEnum
    strategy: PromptStrategy

    model_config = ConfigDict(frozen=True)


def condition_from_summary(exp: ExperimentSummary) -> MatrixCondition:
    """Constructs a MatrixCondition from an ExperimentSummary entity."""
    return MatrixCondition(
        problem_id=exp.problem.problem_id,
        dim=exp.problem.dim,
        mode=exp.mode,
        noise_std=round(exp.problem.noise_std, 4) if exp.problem.noise_std else 0.0,
        noise_model=exp.problem.noise_model,
        strategy=exp.prompt_strategy,
    )


def group_experiments_by_condition(
    experiments: list[ExperimentSummary],
) -> tuple[
    dict[MatrixCondition, list[ExperimentSummary]],
    dict[MatrixCondition, list[ExperimentSummary]],
    dict[MatrixCondition, list[ExperimentSummary]],
]:
    """Groups experiments by their matrix condition into completed, running, and failed categories."""
    completed: defaultdict[MatrixCondition, list[ExperimentSummary]] = defaultdict(list)
    running: defaultdict[MatrixCondition, list[ExperimentSummary]] = defaultdict(list)
    failed: defaultdict[MatrixCondition, list[ExperimentSummary]] = defaultdict(list)

    for exp in experiments:
        cond = condition_from_summary(exp)
        has_valid_champion = exp.best_final_error is not None and np.isfinite(exp.best_final_error)
        if exp.status == "completed":
            if has_valid_champion:
                completed[cond].append(exp)
            else:
                failed[cond].append(exp)
        elif exp.status == "failed":
            failed[cond].append(exp)
        elif exp.status == "running":
            running[cond].append(exp)

    return dict(completed), dict(running), dict(failed)
