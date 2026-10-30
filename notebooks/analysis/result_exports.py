"""Notebook host boundary for numerical snapshots and downstream CSV exports."""

import logging
from pathlib import Path

from benchmark.application.analysis.results import NoiseRobustnessResult, ReliabilityAnalysisResult
from benchmark.infra.storage.analysis_results_store import AnalysisResult, AnalysisResultsStore
from shared.application.diagnostics import report_operation
from shared.application.errors import StorageError
from shared.infra.artifacts import atomic_write


class AnalysisResultsExporter:
    """Publish detached results, then export the established downstream report tables."""

    def __init__(self, store: AnalysisResultsStore) -> None:
        self.store = store

    def save(self, result: AnalysisResult) -> Path:
        """Publish a numerical snapshot and the established downstream CSV reports."""
        with report_operation(logging.getLogger("benchmark.exports"), "export analysis results"):
            directory = self.store.save(result)
            reports = {}
            if isinstance(result, ReliabilityAnalysisResult):
                reports = {
                    "native_reliability_v1.csv": result.native,
                    "noise_robustness_terminal_v1.csv": result.noise_terminal,
                }
            elif isinstance(result, NoiseRobustnessResult):
                reports = {"noise_success_rates_v1.csv": result.aggregate}
            if reports:
                report_dir = self.store.root.parent / "reports"
                try:
                    report_dir.mkdir(parents=True, exist_ok=True)
                    for name, table in reports.items():
                        atomic_write(report_dir / name, table.to_csv(index=False).encode())
                except OSError as error:
                    raise StorageError(f"Cannot export analysis reports: {report_dir}") from error
            return directory

    def load(self, directory: Path) -> AnalysisResult:
        """Restore detached results at the notebook host's reporting boundary."""
        with report_operation(logging.getLogger("benchmark.exports"), "load analysis results"):
            return self.store.load(directory)
