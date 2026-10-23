"""Validate the synthesis TOML format before it enters application workflows."""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from evolution.domain.enums import PromptStrategy, SynthesisMode
from shared.domain.noise_model import NoiseModelEnum


def _lowercase_enum(value: object) -> object:
    """Normalize supported case-insensitive enum names only at the input boundary."""
    return value.lower() if isinstance(value, str) else value


def _single_or_list(value: object) -> object:
    """Accept the single-name shorthand without coercing other types."""
    return [value] if isinstance(value, str) else value


PromptValue = Annotated[PromptStrategy, Field(strict=False), BeforeValidator(_lowercase_enum)]
ModeValue = Annotated[SynthesisMode, Field(strict=False), BeforeValidator(_lowercase_enum)]
NoiseValue = Annotated[NoiseModelEnum, Field(strict=False), BeforeValidator(_lowercase_enum)]
PositiveInt = Annotated[int, Field(ge=1)]


class ProblemTargetToml(BaseModel):
    id: PositiveInt = 1
    dimensions: list[PositiveInt] = Field(default_factory=lambda: [2, 3, 5])

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class SynthesisModeToml(BaseModel):
    mode: ModeValue
    # Absence inherits matrix strategies; an explicit empty list stays empty.
    strategies: list[PromptValue] | None = None

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class NoiseConditionToml(BaseModel):
    std: float = 0.0
    # Absent models inherit the matrix default (or "none" for zero noise).
    noise_model: NoiseValue | None = None
    model: NoiseValue | None = None
    # Absence applies all selected synthesis modes.
    mode: ModeValue | None = None

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class MatrixToml(BaseModel):
    problem_targets: list[ProblemTargetToml] = Field(default_factory=list)
    problem_ids: list[PositiveInt] = Field(default_factory=lambda: [1, 8, 11, 15, 21])
    dimensions: list[PositiveInt] = Field(default_factory=lambda: [2, 3, 5])
    noise_conditions: list[NoiseConditionToml] = Field(default_factory=list)
    noise_stds: list[float] = Field(default_factory=lambda: [0.0, 0.05])
    noise_model: NoiseValue = NoiseModelEnum.HETEROSCEDASTIC
    prompt_strategies: Annotated[list[PromptValue], BeforeValidator(_single_or_list)] = Field(
        default_factory=lambda: list(PromptStrategy)
    )
    synthesis_modes: Annotated[
        list[ModeValue | SynthesisModeToml], BeforeValidator(_single_or_list)
    ] = Field(default_factory=list)
    # Absence falls back to evolution.synthesis_mode, then Explicit + Implicit.
    synthesis_mode: ModeValue | None = None

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class EvolutionToml(BaseModel):
    budget: PositiveInt = 1_000_000
    # Absence uses the supported eval_timeout_seconds alias/default.
    timeout_seconds: Annotated[float, Field(gt=0)] | None = None
    eval_timeout_seconds: Annotated[float, Field(gt=0)] = 30.0
    iterations: PositiveInt = 10
    stagnation_threshold: PositiveInt = 3
    convergence_threshold: Annotated[float, Field(ge=0)] = 1e-6
    runs_per_config: PositiveInt = 1
    name: str = "bbob_comprehensive_matrix"
    synthesis_mode: ModeValue | None = None

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class ExecutionToml(BaseModel):
    max_workers: Annotated[int, Field(ge=0)] = 0
    auto_resume: bool = True
    skip_completed: bool = True
    retry_failed_synthesis: bool = True
    only_incomplete: bool = False

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    @model_validator(mode="before")
    @classmethod
    def reject_invocation_options(cls, value: object) -> object:
        if isinstance(value, dict):
            dynamic_keys = {
                "recover",
                "resume_experiment_ids",
                "rerun_experiment_ids",
                "rerun_repeats",
                "target_experiment_ids",
                "target_exp_ids",
            }
            if misplaced := dynamic_keys.intersection(value):
                raise ValueError(
                    f"Move dynamic campaign options {sorted(misplaced)} out of synthesis.toml "
                    "and into run_campaign(...); use resume_experiment_ids for targeted resumption. "
                    "Remove rerun_repeats: replacement restarts each selected ID once."
                )
        return value


class SynthesisToml(BaseModel):
    matrix: MatrixToml = Field(default_factory=MatrixToml)
    evolution: EvolutionToml = Field(default_factory=EvolutionToml)
    execution: ExecutionToml = Field(default_factory=ExecutionToml)

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
