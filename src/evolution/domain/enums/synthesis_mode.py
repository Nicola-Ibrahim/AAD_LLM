"""Synthesis mode — Evolution Domain Enum."""

from enum import StrEnum


class SynthesisMode(StrEnum):
    """Governs how an algorithm is synthesized: prompt framing and noise exposure."""

    CLEAN = "clean"
    NOISY = "noisy"
    IMPLICIT = "implicit"


__all__ = ["SynthesisMode"]
