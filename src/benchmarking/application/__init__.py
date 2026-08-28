"""Benchmarking Application Layer (Use Cases).

Provides high-level application services orchestrating domain logic and infrastructure repositories:
- `ChampionSelectionService`: Discover and export problem champions.
- `EvaluationService`: Audit evaluation workload and orchestrate empirical benchmark trials.
- `EvaluationAuditService`: Audit multi-condition coverage matrix.
- `StatisticalEvaluationService`: Hypothesis testing, effect sizes, and reporting.
"""

from benchmarking.application.audit_service import (
    AuditCoverageSummary,
    AuditMatrixData,
    EvaluationAuditService,
)
from benchmarking.application.evaluation_service import EvaluationService
from benchmarking.application.selection_service import ChampionSelectionService
from benchmarking.application.statistical_service import (
    StatisticalEvaluationService,
    generate_markdown_report,
)

__all__ = [
    "AuditCoverageSummary",
    "AuditMatrixData",
    "ChampionSelectionService",
    "EvaluationAuditService",
    "EvaluationService",
    "StatisticalEvaluationService",
    "generate_markdown_report",
]
