"""Application evaluation configuration models for benchmark execution.

Defines the strongly-typed configuration parameter object for EvaluationService.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.domain.bbob import BBOBFunction


class ReliabilityConfig(BaseModel):
    """Fixed, reproducible settings for LLM champion reliability analysis."""

    primary_prompt_strategy: str = "baseline"
    primary_target: float = Field(default=1e-8, gt=0.0)
    secondary_target: float = Field(default=1e-2, gt=0.0)
    bootstrap_samples: int = Field(default=1000, ge=100)
    bootstrap_seed: int = 20260923
    checkpoint_fractions: list[float] = Field(default_factory=lambda: [0.01, 0.1, 0.5, 1.0])
    discover_models: bool = True
    incomplete_condition_policy: str = "exclude"


class EvaluationConfig(BaseModel):
    """Strongly-typed application configuration for multi-trial benchmarking campaigns.

    Provides typed attributes and validated defaults for EvaluationService.
    """

    target_eval_runs: int = Field(
        default=20,
        ge=1,
        description="Number of evaluation trials per condition.",
    )
    random_seed: int = Field(
        default=42,
        description="Base seed for reproducible optimizer randomness and benchmark noise.",
    )
    budget_multiplier: int = Field(
        default=10_000,
        ge=1,
        description="Budget multiplier per dimension (budget = dim * multiplier).",
    )
    eval_timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Timeout limit per benchmark trial execution in seconds.",
    )
    observation_trace_points: int = Field(
        default=64,
        ge=1,
        description="Maximum logarithmic checkpoints per noisy trial for actual observed values.",
    )
    force_rerun: bool = Field(
        default=False,
        description="Whether to overwrite existing completed benchmark runs.",
    )
    fill_missing_only: bool = Field(
        default=True,
        description="Whether to only execute missing runs up to target_eval_runs.",
    )
    classical_baselines: list[str] = Field(
        default_factory=lambda: ["cmaes", "de", "pso"],
        description="List of classical baseline optimizer slugs.",
    )
    baseline_labels: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of baseline slugs to display labels.",
    )
    cross_eval_clean_champions: bool = Field(
        default=True,
        description="Whether to evaluate clean champions under noisy conditions.",
    )
    cross_function_enabled: bool = False
    cross_function_problem_ids: list[int] = Field(default_factory=lambda: [1, 8, 11, 15, 21])

    @field_validator("cross_function_problem_ids")
    @classmethod
    def validate_transfer_targets(cls, targets: list[int]) -> list[int]:
        if not targets or any(BBOBFunction.from_id(target) is None for target in targets):
            raise ValueError("Cross-function targets must be nonempty BBOB IDs (1–24).")
        return sorted(set(targets))

    target_noise_stds: list[float] = Field(
        default_factory=list,
        description="Optional filtered noise levels for evaluation.",
    )
    benchmarking: dict[str, object] = Field(
        default_factory=dict,
        description="Raw benchmark section dictionary from TOML.",
    )
    reliability: ReliabilityConfig = Field(default_factory=ReliabilityConfig)

    model_config = ConfigDict(arbitrary_types_allowed=True)
