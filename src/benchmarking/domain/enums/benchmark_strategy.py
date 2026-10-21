from enum import StrEnum


class BenchmarkStrategy(StrEnum):
    """Enumeration of evolutionary prompt scaffolding strategies recognized in benchmarking."""

    BASELINE = "baseline"
    GUIDED = "guided"
    THINKING = "thinking"
    VECTORIZATION = "vectorization"
    CHAMPION = "champion"
