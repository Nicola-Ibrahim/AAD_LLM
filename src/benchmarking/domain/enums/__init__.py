"""Benchmarking domain enums."""

from shared.domain.bbob import (
    BBOB_CLASSES_ORDER,
    BBOBFunction,
)
from benchmarking.domain.enums.benchmark_strategy import EvaluationStrategy
from benchmarking.domain.enums.classical_solver import ClassicalSolver

__all__ = [
    "ClassicalSolver",
    "EvaluationStrategy",
    "BBOBFunction",
    "BBOB_CLASSES_ORDER",
]
