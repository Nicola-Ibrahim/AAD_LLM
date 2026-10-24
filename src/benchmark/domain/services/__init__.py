"""Benchmarking domain computational, normalization, and baseline services."""

from benchmark.domain.services.ecdf import (
    EcdfConvergenceEngine,
)
from benchmark.domain.services.hypothesis import (
    HypothesisTestingEngine,
)
from benchmark.domain.services.performance import (
    PerformanceMetricsEngine,
)
from benchmark.domain.services.reliability import ReliabilityEngine
from benchmark.domain.services.resolvers import (
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
