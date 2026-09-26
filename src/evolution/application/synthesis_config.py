"""Typed synthesis matrix and campaign configuration models owned by the application."""

from pydantic import BaseModel, ConfigDict, Field

from evolution.domain.enums import (
    NoiseEnvironment,
    NoiseModelEnum,
    PromptStrategy,
    SynthesisMode,
)


class ProblemTarget(BaseModel):
    """Target BBOB problem ID and its evaluated search space dimensions."""

    id: int
    dimensions: list[int]

    model_config = ConfigDict(frozen=True)


class SynthesisModeConfig(BaseModel):
    """Synthesis prompting mode and its evaluated prompt engineering strategies."""

    mode: SynthesisMode
    strategies: list[PromptStrategy]

    model_config = ConfigDict(frozen=True)


class NoiseConditionConfig(BaseModel):
    """Evaluated noise condition (std, noise model strategy, optional mode override, and pre-associated modes)."""

    std: float
    noise_model: NoiseModelEnum = NoiseModelEnum.NONE
    mode: str | None = None
    modes: list[SynthesisModeConfig] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class MatrixCondition(BaseModel):
    """Discrete, pre-computed search matrix unit ready for evaluation or dispatch."""

    problem_id: int
    dim: int
    mode: SynthesisMode
    noise_std: float
    noise_model: NoiseModelEnum
    strategy: PromptStrategy

    model_config = ConfigDict(frozen=True)

    @property
    def prompt_template(self) -> str:
        """Resolve (SynthesisMode + noise_std) → mode template filename. Single decision point."""
        if self.mode == SynthesisMode.IMPLICIT:
            return "modes/implicit.j2"
        env = NoiseEnvironment.from_std(self.noise_std)
        return f"modes/{env}.j2"

    @property
    def env_label(self) -> str:
        """Display label for environment status in audit table."""
        if self.mode == SynthesisMode.IMPLICIT:
            return f"Implicit ({self.noise_std})"
        return f"Explicit ({self.noise_std})"

    @property
    def task_mode_label(self) -> str:
        """Task mode label used for execution logging and task naming."""
        if self.mode == SynthesisMode.IMPLICIT:
            return f"implicit_std_{self.noise_std}"
        return f"explicit_std_{self.noise_std}"


class SynthesisConfig(BaseModel):
    """Strongly-typed, structured domain configuration for evolutionary synthesis campaigns."""

    # 1. Search Space Matrix
    problem_targets: list[ProblemTarget] = Field(default_factory=list)
    noise_conditions: list[NoiseConditionConfig] = Field(default_factory=list)
    synthesis_modes: list[SynthesisModeConfig] = Field(default_factory=list)
    matrix_conditions: list[MatrixCondition] = Field(default_factory=list)

    # 2. Execution & Evolutionary Hyperparameters
    budget: int = 1_000_000
    timeout_seconds: float = 30.0
    iterations: int = 10
    stagnation_threshold: int = 3
    convergence_threshold: float = 1e-6
    runs_per_config: int = 1
    num_processes: int = 8
    auto_resume: bool = True
    skip_completed: bool = True
    retry_failed_synthesis: bool = True
    only_incomplete: bool = False
    target_exp_ids: list[int] = Field(default_factory=list)
    name: str = "bbob_comprehensive_matrix"
    noise_model: NoiseModelEnum = NoiseModelEnum.HETEROSCEDASTIC

    model_config = ConfigDict(frozen=True)

    # Derived dot-access properties:
    @property
    def problem_ids(self) -> list[int]:
        return [t.id for t in self.problem_targets]

    @property
    def dimensions(self) -> list[int]:
        return sorted(list({d for t in self.problem_targets for d in t.dimensions}))

    @property
    def noise_stds(self) -> list[float]:
        return [c.std for c in self.noise_conditions]

    @property
    def synthesis_mode_names(self) -> list[str]:
        return [m.mode.value for m in self.synthesis_modes]

    @property
    def prompt_strategies(self) -> list[PromptStrategy]:
        all_s = {s for m in self.synthesis_modes for s in m.strategies}
        return sorted(list(all_s), key=lambda x: str(x.value))

    def to_session_config_dict(self) -> dict[str, int | float]:
        """Derive a dictionary of session execution configuration parameters."""
        return {
            "budget": self.budget,
            "timeout_seconds": self.timeout_seconds,
            "iterations": self.iterations,
            "stagnation_threshold": self.stagnation_threshold,
            "convergence_threshold": self.convergence_threshold,
        }
