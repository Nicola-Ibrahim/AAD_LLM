"""Synthesis condition Value Object representing a discrete algorithm synthesis experimental condition."""

from pydantic import Field

from evolution.domain.base import ValueObject
from evolution.domain.enums import NoiseModelEnum, PromptStrategy, SynthesisMode


class SynthesisCondition(ValueObject):
    """Strongly-typed, immutable Value Object identifying an algorithm synthesis condition."""

    problem_id: int = Field(description="BBOB objective function index (1-24).", ge=1, le=24)
    dim: int = Field(description="Search space dimension (e.g. 2, 5, 10, 20).", ge=1)
    mode: SynthesisMode = Field(description="Synthesis mode (clean, noisy, implicit).")
    noise_std: float = Field(default=0.0, description="Noise standard deviation factor.", ge=0.0)
    noise_model: NoiseModelEnum = Field(
        default=NoiseModelEnum.HETEROSCEDASTIC,
        description="Noise model strategy.",
    )
    strategy: PromptStrategy = Field(default=PromptStrategy.BASELINE, description="Prompt scaffolding strategy.")

    def __hash__(self) -> int:
        """Hash by condition values for dictionary key usage."""
        return hash((
            self.problem_id,
            self.dim,
            self.mode,
            round(self.noise_std, 6),
            self.noise_model,
            self.strategy,
        ))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SynthesisCondition):
            return False
        return (
            self.problem_id == other.problem_id
            and self.dim == other.dim
            and self.mode == other.mode
            and abs(self.noise_std - other.noise_std) < 1e-9
            and self.noise_model == other.noise_model
            and self.strategy == other.strategy
        )

    def __repr__(self) -> str:
        return (
            f"SynthesisCondition(f{self.problem_id}, {self.dim}D, {self.mode}, "
            f"σ={self.noise_std}, model={self.noise_model}, {self.strategy})"
        )
