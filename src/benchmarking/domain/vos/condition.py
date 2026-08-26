"""Benchmark condition Value Object representing a single (dim, noise_std, problem_id) configuration."""

from pydantic import Field
from benchmarking.domain.base import ValueObject


class BenchmarkCondition(ValueObject):
    """Strongly-typed Value Object identifying an experimental condition on BBOB."""

    dim: int = Field(description="Search space dimension (e.g. 2, 3, 5).", ge=1)
    noise_std: float = Field(description="Heteroscedastic Gaussian noise standard deviation (e.g. 0.0, 0.05).", ge=0.0)
    problem_id: int = Field(description="BBOB function index (1-24).", ge=1, le=24)

    def __hash__(self) -> int:
        """Hash by condition values for dictionary key usage."""
        return hash((self.dim, round(self.noise_std, 6), self.problem_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BenchmarkCondition):
            return False
        return (
            self.dim == other.dim
            and abs(self.noise_std - other.noise_std) < 1e-9
            and self.problem_id == other.problem_id
        )

    def __repr__(self) -> str:
        return f"BenchmarkCondition(dim={self.dim}D, noise_std={self.noise_std}, f{self.problem_id})"
