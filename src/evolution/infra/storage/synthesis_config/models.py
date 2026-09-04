"""Strongly-typed Pydantic models for synthesis configuration and search space matrices."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from evolution.domain.enums import NoiseModelEnum, PromptStrategy, SynthesisMode


class ProblemTarget(BaseModel):
    """Target BBOB problem ID and its evaluated search space dimensions."""

    id: int
    dimensions: list[int]

    model_config = ConfigDict(frozen=True)

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "dimensions": list(self.dimensions)}

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, dict):
            return self.id == other.get("id") and list(self.dimensions) == list(other.get("dimensions", []))
        return super().__eq__(other)


class SynthesisModeConfig(BaseModel):
    """Synthesis prompting mode and its evaluated prompt engineering strategies."""

    mode: SynthesisMode
    strategies: list[PromptStrategy]

    model_config = ConfigDict(frozen=True)

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value if isinstance(self.mode, SynthesisMode) else str(self.mode),
            "strategies": [
                s.value if isinstance(s, PromptStrategy) else str(s)
                for s in self.strategies
            ],
        }

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, dict):
            other_mode = other.get("mode")
            if isinstance(other_mode, SynthesisMode):
                mode_match = self.mode == other_mode
            else:
                mode_match = self.mode.value == str(other_mode).lower()
            other_strats = [
                s.value if isinstance(s, PromptStrategy) else str(s).lower()
                for s in other.get("strategies", [])
            ]
            my_strats = [s.value if isinstance(s, PromptStrategy) else str(s) for s in self.strategies]
            return mode_match and my_strats == other_strats
        return super().__eq__(other)


class NoiseConditionConfig(BaseModel):
    """Evaluated noise condition (std, noise model strategy, optional mode override, and pre-associated modes)."""

    std: float
    model: NoiseModelEnum
    mode: str | None = None
    modes: list[SynthesisModeConfig] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)

    def __getitem__(self, idx: int | str) -> Any:
        if isinstance(idx, int):
            return (self.std, self.model, self.mode)[idx]
        if hasattr(self, idx):
            return getattr(self, idx)
        raise KeyError(idx)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def to_dict(self) -> dict[str, Any]:
        return {
            "std": self.std,
            "model": self.model.value if isinstance(self.model, NoiseModelEnum) else str(self.model),
            "mode": self.mode,
            "modes": [m.to_dict() for m in self.modes],
        }

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, dict):
            model_val = other.get("model")
            model_match = (
                self.model.value == str(model_val).lower()
                if model_val is not None
                else True
            )
            return (
                abs(self.std - float(other.get("std", 0.0))) < 1e-9
                and model_match
                and self.mode == other.get("mode")
            )
        if isinstance(other, (tuple, list)):
            return (self.std, self.model, self.mode)[:len(other)] == tuple(other)
        return super().__eq__(other)


class MatrixCondition(BaseModel):
    """Discrete, pre-computed search matrix unit ready for evaluation or dispatch."""

    problem_id: int
    dim: int
    mode: SynthesisMode
    noise_std: float
    noise_model: NoiseModelEnum
    strategy: PromptStrategy

    model_config = ConfigDict(frozen=True)

    def __hash__(self) -> int:
        return hash((
            self.problem_id,
            self.dim,
            self.mode,
            round(self.noise_std, 4),
            self.noise_model,
            self.strategy,
        ))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MatrixCondition):
            return False
        return (
            self.problem_id == other.problem_id
            and self.dim == other.dim
            and self.mode == other.mode
            and abs(self.noise_std - other.noise_std) < 1e-6
            and self.noise_model == other.noise_model
            and self.strategy == other.strategy
        )

    @property
    def condition(self) -> "MatrixCondition":
        """Returns self for backward compatibility."""
        return self

    @property
    def env_label(self) -> str:
        """Display label for environment status in audit table."""
        if self.mode == SynthesisMode.IMPLICIT:
            return f"Implicit ({self.noise_std})"
        elif self.mode == SynthesisMode.NOISY:
            return f"Noisy ({self.noise_std})"
        return f"Clean ({self.noise_std})"

    @property
    def task_mode_label(self) -> str:
        """Task mode label used for execution logging and task naming."""
        if self.mode == SynthesisMode.IMPLICIT:
            return f"implicit_std_{self.noise_std}"
        elif self.mode == SynthesisMode.NOISY:
            return f"noisy_std_{self.noise_std}"
        return "clean"

    @property
    def synthesis_mode(self) -> SynthesisMode | None:
        """SynthesisMode passed to EvolutionTask session kwargs (None for clean)."""
        return self.mode if self.mode != SynthesisMode.CLEAN else None

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class SynthesisConfig(BaseModel):
    """Strongly-typed, structured domain configuration for evolutionary synthesis campaigns."""

    # 1. Search Space Matrix
    problem_targets: list[ProblemTarget] = Field(default_factory=list)
    noise_conditions: list[NoiseConditionConfig] = Field(default_factory=list)
    synthesis_modes: list[SynthesisModeConfig] = Field(default_factory=list)
    matrix_conditions: list[MatrixCondition] = Field(default_factory=list)

    # 2. Execution & Evolutionary Hyperparameters
    budget: int = 1_000_000
    iterations: int = 10
    runs_per_config: int = 1
    num_processes: int = 8
    auto_resume: bool = True
    skip_completed: bool = True
    retry_failed_synthesis: bool = True
    only_incomplete: bool = False
    target_exp_ids: list[int] | None = None
    name: str = "bbob_comprehensive_matrix"
    noise_model: NoiseModelEnum = NoiseModelEnum.HETEROSCEDASTIC

    # 3. Raw dictionary sections preserved for backward compatibility
    matrix: dict[str, Any] = Field(default_factory=dict)
    evolution: dict[str, Any] = Field(default_factory=dict)
    execution: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Derived dot-access properties:
    @property
    def problem_ids(self) -> list[int]:
        return [t.id for t in self.problem_targets]

    @property
    def problems(self) -> list[int]:
        return self.problem_ids

    @property
    def dimensions(self) -> list[int]:
        return sorted(list({d for t in self.problem_targets for d in t.dimensions}))

    @property
    def noise_stds(self) -> list[float]:
        return [c.std for c in self.noise_conditions]

    @property
    def mode_enums(self) -> list[SynthesisMode]:
        return [m.mode for m in self.synthesis_modes]

    @property
    def synthesis_mode_names(self) -> list[str]:
        return [m.mode.value for m in self.synthesis_modes]

    @property
    def synthesis_mode(self) -> SynthesisMode | None:
        return self.synthesis_modes[0].mode if len(self.synthesis_modes) == 1 else None

    @property
    def prompt_strategies(self) -> list[PromptStrategy]:
        all_s = {s for m in self.synthesis_modes for s in m.strategies}
        return sorted(list(all_s), key=lambda x: str(x.value))

    @property
    def target_experiment_ids(self) -> list[int] | None:
        return self.target_exp_ids

    @property
    def max_workers(self) -> int:
        return self.num_processes

    # Dictionary emulation for backward compatibility:
    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Configuration key '{key}' not found in SynthesisConfig.")

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)
