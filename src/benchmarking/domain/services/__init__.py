"""Benchmarking domain computational and normalization services."""

from benchmarking.domain.services.baselines import (
    BASELINES,
    run_cmaes,
    run_de,
    run_pso,
)
from benchmarking.domain.services.resolvers import (
    CLASSICAL_SOLVERS_MAP,
    KNOWN_STRATEGIES,
    format_db_solver_name,
    get_clean_model_label,
    get_model_slug,
    resolve_canonical_model_slug,
    resolve_folder_solver_name,
)
from benchmarking.domain.services.statistics import StatisticalEngine
from benchmarking.domain.services.taxonomy import (
    BBOB_CLASSES,
    BBOB_CLASSES_ORDER,
    BBOB_METADATA,
    BBOB_NAMES,
    get_bbob_class,
    get_bbob_name,
)

__all__ = [
    "BASELINES",
    "run_cmaes",
    "run_de",
    "run_pso",
    "CLASSICAL_SOLVERS_MAP",
    "KNOWN_STRATEGIES",
    "format_db_solver_name",
    "get_clean_model_label",
    "get_model_slug",
    "resolve_canonical_model_slug",
    "resolve_folder_solver_name",
    "StatisticalEngine",
    "BBOB_CLASSES",
    "BBOB_CLASSES_ORDER",
    "BBOB_METADATA",
    "BBOB_NAMES",
    "get_bbob_class",
    "get_bbob_name",
]
