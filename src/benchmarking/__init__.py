"""Benchmarking and Analytics Bounded Context.

Clean 3-Layer Domain-Driven Architecture (Backend):
- Application: `ChampionSelectionService`, `BenchmarkEvaluationService`, `BenchmarkAuditService`, `StatisticalEvaluationService`, `generate_markdown_report`
- Domain: `StatisticalEngine`, taxonomy, classical baseline solvers, naming resolvers (Zero I/O)
- Infra: `SQLiteBenchmarkReadRepository`, `ChampionsReadRepository`, `IOHTraceReader`, hashing (Pure I/O)
"""

from benchmarking.application import (
    AuditMatrixData,
    BenchmarkAuditService,
    BenchmarkEvaluationService,
    ChampionSelectionService,
    StatisticalEvaluationService,
    generate_markdown_report,
)
from benchmarking.domain import (
    BASELINES,
    BBOB_CLASSES,
    BBOB_CLASSES_ORDER,
    BBOB_METADATA,
    BBOB_NAMES,
    CLASSICAL_SOLVERS_MAP,
    KNOWN_STRATEGIES,
    StatisticalEngine,
    format_db_solver_name,
    get_bbob_class,
    get_bbob_name,
    get_clean_model_label,
    get_model_slug,
    resolve_canonical_model_slug,
    resolve_folder_solver_name,
    run_cmaes,
    run_de,
    run_pso,
)
from benchmarking.infra import (
    ChampionsReadRepository,
    IOHTraceReader,
    SQLiteBenchmarkReadRepository,
    compute_code_hash,
)

__all__ = [
    # Application Services (Use Cases) & Reports
    "ChampionSelectionService",
    "BenchmarkEvaluationService",
    "BenchmarkAuditService",
    "StatisticalEvaluationService",
    "AuditMatrixData",
    "generate_markdown_report",
    # Domain Solvers (Classical Baselines)
    "BASELINES",
    "run_cmaes",
    "run_de",
    "run_pso",
    # Domain Engine & Taxonomy
    "StatisticalEngine",
    "BBOB_CLASSES",
    "BBOB_CLASSES_ORDER",
    "BBOB_METADATA",
    "BBOB_NAMES",
    "get_bbob_class",
    "get_bbob_name",
    # Resolvers
    "CLASSICAL_SOLVERS_MAP",
    "KNOWN_STRATEGIES",
    "format_db_solver_name",
    "get_clean_model_label",
    "get_model_slug",
    "resolve_canonical_model_slug",
    "resolve_folder_solver_name",
    # Infrastructure Repositories & Utilities
    "SQLiteBenchmarkReadRepository",
    "ChampionsReadRepository",
    "IOHTraceReader",
    "compute_code_hash",
]
