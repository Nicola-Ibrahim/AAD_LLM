"""Application evaluation configuration models for benchmark execution.

Defines the strongly-typed configuration parameter object for EvaluationService.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class EvaluationConfig(BaseModel):
    """Strongly-typed application configuration for multi-trial benchmarking campaigns.

    Provides typed attributes and validated defaults for EvaluationService.
    """

    target_eval_runs: int = Field(
        default=20,
        ge=1,
        description="Number of evaluation trials per condition.",
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
    target_noise_stds: list[float] = Field(
        default_factory=list,
        description="Optional filtered noise levels for evaluation.",
    )
    benchmarking: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw benchmark section dictionary from TOML.",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get(self, item: str, default: Any = None) -> Any:
        """Dictionary-like access helper for backward compatibility with config dicts."""
        return getattr(self, item, default)

    def __getitem__(self, item: str) -> Any:
        """Subscript access helper for backward compatibility with config dicts."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)
