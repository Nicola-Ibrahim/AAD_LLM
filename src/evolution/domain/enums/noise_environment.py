"""Noise environment — Evolution Domain Enum."""

from enum import StrEnum


class NoiseEnvironment(StrEnum):
    """Level 2 — physical landscape. Derived from noise_std. Never stored."""

    CLEAN = "clean"  # σ = 0.0 → renders modes/clean.j2
    NOISY = "noisy"  # σ > 0.0 → renders modes/noisy.j2

    @classmethod
    def from_std(cls, noise_std: float) -> "NoiseEnvironment":
        """Derive environment from physical noise standard deviation."""
        return cls.NOISY if noise_std > 0.0 else cls.CLEAN
