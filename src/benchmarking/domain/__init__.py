"""Benchmarking domain models, taxonomy, classical baseline solvers, and statistical analytics."""

from benchmarking.domain.baselines import (
    BASELINES,
    run_cmaes,
    run_de,
    run_pso,
)
from benchmarking.domain.resolvers import (
    CLASSICAL_SOLVERS_MAP,
    KNOWN_STRATEGIES,
    format_db_solver_name,
    get_clean_model_label,
    get_model_slug,
    resolve_canonical_model_slug,
    resolve_folder_solver_name,
)
from benchmarking.domain.statistics import StatisticalEngine
from benchmarking.domain.taxonomy import (
    BBOB_CLASSES,
    BBOB_CLASSES_ORDER,
    BBOB_METADATA,
    BBOB_NAMES,
    get_bbob_class,
    get_bbob_name,
)

__all__ = [
    "StatisticalEngine",
    "BASELINES",
    "run_cmaes",
    "run_de",
    "run_pso",
    "BBOB_CLASSES",
    "BBOB_CLASSES_ORDER",
    "BBOB_METADATA",
    "BBOB_NAMES",
    "get_bbob_class",
    "get_bbob_name",
    "CLASSICAL_SOLVERS_MAP",
    "KNOWN_STRATEGIES",
    "format_db_solver_name",
    "get_clean_model_label",
    "get_model_slug",
    "resolve_canonical_model_slug",
    "resolve_folder_solver_name",
]
