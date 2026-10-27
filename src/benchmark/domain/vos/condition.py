"""Benchmark condition: one dimension, noise level and problem configuration."""

from pydantic import Field, field_validator

from benchmark.domain.base import ValueObject


class BenchmarkCondition(ValueObject):
    """Strongly-typed Value Object identifying an experimental condition on BBOB."""

    dim: int = Field(description="Search space dimension (e.g. 2, 3, 5).", ge=1)
    noise_std: float = Field(
        description="Heteroscedastic Gaussian noise standard deviation (e.g. 0.0, 0.05).",
        ge=0.0,
        allow_inf_nan=False,
    )
    problem_id: int = Field(description="BBOB function index (1-24).", ge=1, le=24)

    @field_validator("noise_std")
    @classmethod
    def normalize_noise(cls, value: float) -> float:
        """Use one nine-decimal identity for dictionary lookup and equality."""
        return round(value, 9)

    def __repr__(self) -> str:
        return (
            f"BenchmarkCondition(dim={self.dim}D, noise_std={self.noise_std}, f{self.problem_id})"
        )
