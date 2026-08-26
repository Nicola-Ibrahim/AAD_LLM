from enum import StrEnum


class ClassicalSolver(StrEnum):
    """Recognized classical baseline optimization algorithms."""

    CMA_ES = "CMA-ES"
    DE = "DE"
    PSO = "PSO"
