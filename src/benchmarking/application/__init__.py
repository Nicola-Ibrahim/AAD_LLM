"""Benchmarking Application Layer (Use Cases).

Provides high-level application services orchestrating domain logic and infrastructure repositories:
- `ChampionSelectionService`: Discover and export problem champions.
- `EvaluationService`: Audit evaluation workload and orchestrate empirical benchmark trials.
- `EvaluationAuditService`: Audit multi-condition coverage matrix.
- Analysis use cases load validated data and calculate detached scientific results.
"""

from benchmarking.application.evaluation.audit import (
    AuditCoverageSummary,
    AuditSnapshot,
    EvaluationAuditService,
)
from benchmarking.application.evaluation.run import EvaluationService
from benchmarking.application.evaluation_config import EvaluationConfig
from benchmarking.application.select_champions import ChampionSelectionService

__all__ = [
    "AuditCoverageSummary",
    "AuditSnapshot",
    "ChampionSelectionService",
    "EvaluationAuditService",
    "EvaluationConfig",
    "EvaluationService",
]
