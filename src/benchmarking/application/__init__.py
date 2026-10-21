"""Benchmarking Application Layer (Use Cases).

Provides high-level application services orchestrating domain logic and infrastructure repositories:
- `ChampionSelectionService`: Discover and export problem champions.
- `BenchmarkService`: Audit evaluation workload and orchestrate empirical benchmark trials.
- `BenchmarkAuditService`: Audit multi-condition coverage matrix.
- Analysis use cases load validated data and calculate detached scientific results.
"""

from benchmarking.application.benchmark.audit import (
    AuditCoverageSummary,
    AuditSnapshot,
    BenchmarkAuditService,
)
from benchmarking.application.benchmark.run import BenchmarkService
from benchmarking.application.benchmark_config import BenchmarkConfig
from benchmarking.application.select_champions import ChampionSelectionService

__all__ = [
    "AuditCoverageSummary",
    "AuditSnapshot",
    "ChampionSelectionService",
    "BenchmarkAuditService",
    "BenchmarkConfig",
    "BenchmarkService",
]
