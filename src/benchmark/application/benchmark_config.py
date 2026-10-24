"""Application configuration models for benchmark execution.

Defines validated settings for benchmark execution and analysis workflows.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from benchmark.domain.trial_schedule import TrialIdentity
from shared.domain.bbob import BBOBFunction


class ReliabilityConfig(BaseModel):
    """Fixed, reproducible settings for LLM champion reliability analysis."""

    model_config = ConfigDict(strict=True, extra="forbid")

    primary_prompt_strategy: str = "baseline"
    primary_target: float = Field(default=1e-8, gt=0.0)
    secondary_target: float = Field(default=1e-2, gt=0.0)
    bootstrap_samples: int = Field(default=1000, ge=100)
    bootstrap_seed: int = 20260923
    checkpoint_fractions: list[float] = Field(default_factory=lambda: [0.01, 0.1, 0.5, 1.0])
    discover_models: bool = True
    incomplete_condition_policy: str = "exclude"


class BenchmarkConfig(BaseModel):
    """Strongly-typed application configuration for multi-trial benchmarking campaigns.

    Provides typed attributes and validated defaults for benchmarks and analysis.
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    trials_per_condition: int = Field(
        default=20,
        ge=1,
        description="Number of benchmark trials per condition.",
    )
    random_seed: int = Field(
        default=42,
        description="Base seed for reproducible optimizer randomness and benchmark noise.",
    )
    first_instance_id: int = Field(
        default=2,
        ge=1,
        description="First benchmark instance; instance 1 is reserved for synthesis.",
    )

    @property
    def trial_schedule(self) -> tuple[TrialIdentity, ...]:
        """Distinct instances paired with stable seeds, independent of trial position."""
        return tuple(
            (instance, self.random_seed + instance)
            for instance in range(
                self.first_instance_id, self.first_instance_id + self.trials_per_condition
            )
        )

    budget: int = Field(
        default=100_000,
        ge=1,
        description="Fixed objective-call allowance per trial, independent of dimension.",
    )

    trial_timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        allow_inf_nan=False,
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
        description="Whether to only execute missing runs up to trials_per_condition.",
    )
    classical_baselines: list[str] = Field(
        default_factory=lambda: ["cmaes", "de", "pso"],
        description="List of classical baseline optimizer slugs.",
    )
    baseline_labels: dict[str, str] = Field(
        default_factory=lambda: {
            "cmaes": "CMA-ES",
            "de": "Differential Evolution",
            "pso": "Particle Swarm Optimization",
        },
        description="Mapping of baseline slugs to display labels.",
    )
    noise_robustness_enabled: bool = Field(
        default=True,
        description="Whether to evaluate clean champions under noisy conditions.",
    )
    cross_function_enabled: bool = False
    cross_function_problem_ids: list[int] = Field(default_factory=lambda: [1, 8, 11, 15, 21])

    @field_validator("classical_baselines")
    @classmethod
    def validate_baselines(cls, solvers: list[str]) -> list[str]:
        if unknown := set(solvers) - {"cmaes", "de", "pso"}:
            raise ValueError(f"Unsupported classical baselines: {sorted(unknown)}")
        return solvers

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
    reliability: ReliabilityConfig = Field(default_factory=ReliabilityConfig)
