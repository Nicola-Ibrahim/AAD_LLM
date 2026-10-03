"""Calculate paired convergence and ECDF profiles before presentation."""

from dataclasses import replace

import numpy as np

from benchmarking.application.analysis.data_loader import AnalysisDataLoader
from benchmarking.application.analysis.results import (
    ConditionProfile,
    ProfileAnalysisResult,
    ProfileMode,
    ProfileSeries,
)
from benchmarking.domain.services.ecdf import EcdfConvergenceEngine


class AnalyzeEcdfAndConvergence:
    def __init__(self, loader: AnalysisDataLoader, engine: EcdfConvergenceEngine) -> None:
        self.loader = loader
        self.engine = engine

    def execute(
        self,
        *,
        mode: ProfileMode,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
    ) -> ProfileAnalysisResult:
        if mode not in {"explicit", "implicit", "comparison"}:
            raise ValueError(f"Unsupported profile mode: {mode}")
        snapshot = self.loader.load(dims=dims, problems=problems, noise_stds=noise_stds)
        dataset = snapshot.dataset
        targets = {
            noise: self.engine.compute_adaptive_targets(dataset, noise_std=noise)
            for noise in dataset.noise_stds
        }
        grid = np.logspace(0, 6, 300)
        conditions = []
        diagnostics = []
        for dim in dataset.dims:
            for model, solvers in snapshot.models_to_solvers.items():
                for noise in dataset.noise_stds:
                    implicit = [s for s in solvers if "(noise-implicit)" in s]
                    adapted = [s for s in solvers if "(noise-adapted)" in s]
                    clean = [
                        s
                        for s in solvers
                        if "(noise-implicit)" not in s and "(noise-adapted)" not in s
                    ]
                    if mode == "explicit":
                        selected = clean if noise == 0.0 else (adapted or clean)
                    elif mode == "implicit":
                        if noise == 0.0 or not implicit:
                            continue
                        selected = implicit
                    else:
                        if noise == 0.0 or not implicit or not adapted:
                            continue
                        selected = adapted + implicit
                    selected = selected + ([] if mode == "comparison" else ["CMA-ES", "PSO", "DE"])
                    series = []
                    for problem in dataset.problem_ids:
                        for solver in selected:
                            runs = dataset.get_runs(dim, noise, problem, solver)
                            if not runs:
                                diagnostics.append(
                                    f"No traces: {model}, {dim}D, σ={noise}, f{problem}, {solver}"
                                )
                                continue
                            median, q25, q75, ecdf = self.engine.compute_trajectory_and_ecdf(
                                runs, grid, targets[noise]
                            )
                            series.append(
                                ProfileSeries(solver, problem, median, q25, q75, ecdf, len(runs))
                            )
                    conditions.append(
                        ConditionProfile(
                            model,
                            snapshot.model_slugs[model],
                            dim,
                            noise,
                            dataset.problem_ids,
                            selected,
                            grid,
                            targets[noise],
                            series,
                        )
                    )
        provenance = snapshot.provenance("profiles")
        provenance = replace(provenance, filters={**provenance.filters, "mode": mode})
        return ProfileAnalysisResult(mode, conditions, provenance, tuple(diagnostics))
