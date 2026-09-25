"""Benchmarking Application Layer (Use Cases).

Provides high-level application services orchestrating domain logic and infrastructure repositories:
- `ChampionSelectionService`: Discover and export problem champions.
- `EvaluationService`: Audit evaluation workload and orchestrate empirical benchmark trials.
- `EvaluationAuditService`: Audit multi-condition coverage matrix.
- `AnalysisData`: Load traces and synthesis data for domain analysis engines.
"""

from benchmarking.application.evaluation.audit import (
    AuditCoverageSummary,
    AuditMatrixData,
    EvaluationAuditService,
)
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.evaluation.run import EvaluationService
from benchmarking.application.select_champions import ChampionSelectionService
from benchmarking.application.analysis import (
    AnalysisData,
    generate_markdown_report,
)

__all__ = [
    "AuditCoverageSummary",
    "AuditMatrixData",
    "ChampionSelectionService",
    "EvaluationAuditService",
    "EvaluationConfig",
    "EvaluationService",
    "AnalysisData",
    "generate_markdown_report",
]
