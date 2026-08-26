from enum import StrEnum


class PromptStrategy(StrEnum):
    """Enumeration of evolutionary system prompt structuring strategies."""

    BASELINE = "baseline"
    THINKING = "thinking"
    VECTORIZATION = "vectorization"
    GUIDED = "guided"
