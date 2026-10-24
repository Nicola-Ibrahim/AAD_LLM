"""Benchmark application layer (Use Cases).

Provides high-level application services orchestrating domain logic and infrastructure repositories:
- `ChampionSelectionService`: Discover and export problem champions.
- `BenchmarkCoordinator`: Audit evaluation workload and orchestrate empirical benchmark trials.
- `BenchmarkAuditService`: Audit multi-condition coverage matrix.
- Analysis use cases load validated data and calculate detached scientific results.
"""

from benchmark.application.benchmark_config import BenchmarkConfig
from benchmark.application.select_champions import ChampionSelectionService
from benchmark.application.trials.audit import (
    AuditCoverageSummary,
    AuditSnapshot,
    BenchmarkAuditService,
)
from benchmark.application.trials.coordinator import BenchmarkCoordinator

__all__ = [
    "AuditCoverageSummary",
    "AuditSnapshot",
    "ChampionSelectionService",
    "BenchmarkAuditService",
    "BenchmarkConfig",
    "BenchmarkCoordinator",
]
