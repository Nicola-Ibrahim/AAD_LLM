"""Exploratory AUC, model-scale and hardness analysis use case."""

from benchmarking.application.analysis.data_loader import AnalysisDataLoader
from benchmarking.application.analysis.results import (
    HardnessSummary,
    PerformanceAnalysisResult,
)
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine
from benchmarking.domain.services.performance import PerformanceMetricsEngine


class AnalyzePerformance:
    def __init__(
        self,
        loader: AnalysisDataLoader,
        ecdf: EcdfConvergenceEngine,
        performance: PerformanceMetricsEngine,
    ) -> None:
        self.loader = loader
        self.ecdf = ecdf
        self.performance = performance

    def execute(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
    ) -> PerformanceAnalysisResult:
        snapshot = self.loader.load(dims=dims, problems=problems, noise_stds=noise_stds)
        targets = {
            noise: self.ecdf.compute_adaptive_targets(snapshot.dataset, noise_std=noise)
            for noise in snapshot.dataset.noise_stds
        }
        table = self.ecdf.compute_auc_ecdf_matrix(
            snapshot.dataset, snapshot.solver_order, targets=targets, group_by="condition"
        )
        table["Canonical Solver"] = table["Solver"].str.replace(
            r" \(noise-adapted\)", "", regex=True
        )
        dims = [d for d in [2, 3, 5, 10] if d in snapshot.dataset.dims]
        model_scale, rankings = self.performance.summarize_auc_results(
            table,
            list(snapshot.models_to_solvers),
            snapshot.classical_solvers,
            dims,
            [snapshot.clean_std, snapshot.noisy_std],
        )
        hardness = []
        for dim in snapshot.dataset.dims:
            for model, solvers in snapshot.models_to_solvers.items():
                selected = solvers + snapshot.classical_solvers
                tables = {
                    noise: self.performance.compute_hardness_success_rates(
                        snapshot.dataset, dim, selected, noise_level=noise
                    )
                    for noise in [snapshot.clean_std, snapshot.noisy_std]
                }
                hardness.append(HardnessSummary(model, dim, selected, tables))
        return PerformanceAnalysisResult(
            targets,
            table,
            rankings,
            model_scale,
            hardness,
            snapshot.models_to_solvers,
            snapshot.model_slugs,
            snapshot.classical_solvers,
            dims,
            snapshot.clean_std,
            snapshot.noisy_std,
            snapshot.provenance("profiles"),
            () if not table.empty else ("No eligible performance observations.",),
        )
