"""Typed synthesis matrix and campaign configuration models owned by the application."""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from evolution.application.synthesis.settings import SynthesisSettings
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


class CampaignSettings(BaseModel):
    """Validated matrix and scheduling settings for one campaign invocation."""

    # 1. Search Space Matrix
    problem_targets: list[ProblemTarget] = Field(default_factory=list)
    noise_conditions: list[NoiseConditionConfig] = Field(default_factory=list)
    synthesis_modes: list[SynthesisModeConfig] = Field(default_factory=list)
    matrix_conditions: list[MatrixCondition] = Field(default_factory=list)

    # 2. Execution & Evolutionary Hyperparameters
    budget: int = Field(default=100_000, gt=0)
    timeout_seconds: float = Field(default=30.0, gt=0, allow_inf_nan=False)
    iterations: int = Field(default=10, gt=0)
    stagnation_threshold: int = 3
    convergence_threshold: float = 1e-6
    runs_per_config: int = Field(default=1, gt=0)
    auto_resume: bool = True
    skip_completed: bool = True
    retry_failed_synthesis: bool = True
    only_incomplete: bool = False

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def resolve_matrix(self) -> "CampaignSettings":
        """Resolve the public matrix once, preserving declared iteration order."""
        if self.matrix_conditions or not self.problem_targets:
            return self
        conditions = [
            MatrixCondition(
                problem_id=target.id,
                dim=dim,
                mode=mode.mode,
                noise_std=noise.std,
                noise_model=noise.noise_model,
                strategy=strategy,
            )
            for target in self.problem_targets
            for dim in target.dimensions
            for noise in self.noise_conditions
            for mode in self.synthesis_modes
            for strategy in mode.strategies
        ]
        object.__setattr__(self, "matrix_conditions", conditions)
        return self

    # Derived dot-access properties:
    @property
    def problem_ids(self) -> list[int]:
        return [t.id for t in self.problem_targets]

    @property
    def dimensions(self) -> list[int]:
        return sorted({d for t in self.problem_targets for d in t.dimensions})

    @property
    def noise_stds(self) -> list[float]:
        return [c.std for c in self.noise_conditions]

    @property
    def synthesis_mode_names(self) -> list[str]:
        return [m.mode.value for m in self.synthesis_modes]

    @property
    def prompt_strategies(self) -> list[PromptStrategy]:
        all_s = {s for m in self.synthesis_modes for s in m.strategies}
        return sorted(all_s, key=lambda strategy: strategy.value)

    def synthesis_settings(self, *, iterations: int) -> SynthesisSettings:
        """Pass typed synthesis settings directly to the synthesis workflow."""
        return SynthesisSettings(
            budget=self.budget,
            timeout_seconds=self.timeout_seconds,
            iterations=iterations,
            stagnation_threshold=self.stagnation_threshold,
            convergence_threshold=self.convergence_threshold,
        )
