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
    format_db_solver_name,
    get_clean_model_label,
    get_model_slug,
    resolve_canonical_model_slug,
    resolve_folder_solver_name,
)

__all__ = [
    "CLASSICAL_SOLVERS_MAP",
    "KNOWN_STRATEGIES",
    "format_db_solver_name",
    "get_clean_model_label",
    "get_model_slug",
    "resolve_canonical_model_slug",
    "resolve_folder_solver_name",
    "HypothesisTestingEngine",
    "EcdfConvergenceEngine",
    "PerformanceMetricsEngine",
    "ReliabilityEngine",
]
