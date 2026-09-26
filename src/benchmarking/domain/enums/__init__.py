"""Benchmarking domain enums."""

from benchmarking.domain.enums.benchmark_strategy import EvaluationStrategy
from benchmarking.domain.enums.classical_solver import ClassicalSolver
from shared.domain.bbob import (
    BBOB_CLASSES_ORDER,
    BBOBFunction,
)

__all__ = [
    "ClassicalSolver",
    "EvaluationStrategy",
    "BBOBFunction",
    "BBOB_CLASSES_ORDER",
]
