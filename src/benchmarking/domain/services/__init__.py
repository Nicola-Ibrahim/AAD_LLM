"""Benchmarking domain computational, normalization, and baseline services."""

from benchmarking.domain.services.ecdf import (
    EcdfConvergenceEngine,
)
from benchmarking.domain.services.hypothesis import (
    HypothesisTestingEngine,
)
from benchmarking.domain.services.performance import (
    PerformanceMetricsEngine,
)
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.resolvers import (
    CLASSICAL_SOLVERS_MAP,
    KNOWN_STRATEGIES,
    LLMModelSpec,
    ModelNames,
)

__all__ = [
    "CLASSICAL_SOLVERS_MAP",
    "KNOWN_STRATEGIES",
    "LLMModelSpec",
    "ModelNames",
    "HypothesisTestingEngine",
    "EcdfConvergenceEngine",
    "PerformanceMetricsEngine",
    "ReliabilityEngine",
]
