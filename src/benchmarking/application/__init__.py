"""Benchmarking Application Layer (Use Cases).

Provides high-level application services orchestrating domain logic and infrastructure repositories:
- `ChampionSelectionService`: Discover and export problem champions (Notebook 03).
- `BenchmarkEvaluationService`: Audit and run empirical benchmark trials (Notebooks 04 & 05).
- `BenchmarkAuditService`: Audit multi-condition coverage matrix (Notebook 06).
- `StatisticalEvaluationService`: Hypothesis testing, effect sizes, and reporting (Notebooks 07 & 08).
"""

from benchmarking.application.audit_service import (
    AuditMatrixData,
    BenchmarkAuditService,
)
from benchmarking.application.evaluation_service import BenchmarkEvaluationService
from benchmarking.application.selection_service import ChampionSelectionService
from benchmarking.application.statistical_service import (
    StatisticalEvaluationService,
    generate_markdown_report,
)

__all__ = [
    "ChampionSelectionService",
    "BenchmarkEvaluationService",
    "BenchmarkAuditService",
    "StatisticalEvaluationService",
    "AuditMatrixData",
    "generate_markdown_report",
]
