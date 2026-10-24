"""Exploratory AUC, model-scale and hardness analysis use case."""

from dataclasses import replace

from benchmark.application.analysis.data_loader import AnalysisDataLoader
from benchmark.application.analysis.results import (
    HardnessSummary,
    PerformanceAnalysisResult,
)
from benchmark.domain.services.ecdf import EcdfConvergenceEngine
from benchmark.domain.services.performance import PerformanceMetricsEngine
from benchmark.domain.vos import BenchmarkDataset


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
        # Model comparisons use observed model traces and their paired baselines,
        # not a condition matrix inferred from synthesis or configuration.
        dataset = BenchmarkDataset(
            conditions_data={
                condition: solvers
                for condition, solvers in snapshot.dataset.items()
                if any(" / " in solver and runs for solver, runs in solvers.items())
            }
        )
        targets = {
            noise: self.ecdf.compute_adaptive_targets(snapshot.dataset, noise_std=noise)
            for noise in dataset.noise_stds
        }
        table = self.ecdf.compute_auc_ecdf_matrix(
            dataset,
            snapshot.solver_order,
            targets=targets,
            group_by="condition",
            budget=snapshot.config.budget,
        )
        table["Canonical Solver"] = table["Solver"].str.replace(
            r" \(noise-adapted\)", "", regex=True
        )
        scale_dimensions = dataset.dims
        model_scale, rankings = self.performance.summarize_auc_results(
            table,
            list(snapshot.models_to_solvers),
            snapshot.classical_solvers,
            scale_dimensions,
            dataset.noise_stds,
        )
        hardness: list[HardnessSummary] = []
        for dim in dataset.dims:
            for model, solvers in snapshot.models_to_solvers.items():
                selected = solvers + snapshot.classical_solvers
                tables = {
                    noise: self.performance.compute_hardness_success_rates(
                        dataset, dim, selected, noise_level=noise
                    )
                    for noise in dataset.noise_stds
                    if any(
                        dataset.get_runs(dim, noise, problem, solver)
                        for problem in dataset.problem_ids
                        for solver in solvers
                    )
                }
                if tables:
                    hardness.append(HardnessSummary(model, dim, selected, tables))
        provenance = snapshot.provenance("profiles")
        provenance = replace(
            provenance,
            settings={
                **provenance.settings,
                "auc_grid_policy": "fixed_budget_v3",
                "auc_grid_points": 200,
            },
        )
        return PerformanceAnalysisResult(
            targets,
            table,
            rankings,
            model_scale,
            hardness,
            snapshot.models_to_solvers,
            snapshot.model_slugs,
            snapshot.classical_solvers,
            scale_dimensions,
            snapshot.clean_std,
            snapshot.noisy_std,
            provenance,
            () if not table.empty else ("No eligible performance observations.",),
        )
