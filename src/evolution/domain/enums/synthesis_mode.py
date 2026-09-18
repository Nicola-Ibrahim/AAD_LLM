"""Synthesis mode — Evolution Domain Enum."""

from enum import StrEnum


class SynthesisMode(StrEnum):
    """Level 1 — epistemic prior. Stored in DB and config."""

    EXPLICIT = "explicit"  # LLM is told the truth about the environment
    IMPLICIT = "implicit"  # Neutral black-box framing
