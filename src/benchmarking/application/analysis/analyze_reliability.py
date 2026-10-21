"""Terminal reliability and fixed-target search attainment use case."""

import numpy as np

from benchmarking.application.analysis.data_loader import AnalysisDataLoader
from benchmarking.application.analysis.results import (
    AttainmentSeries,
    ReliabilityAnalysisResult,
)
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationCondition, RunTrace


class AnalyzeReliability:
    def __init__(
        self,
        loader: AnalysisDataLoader,
        conditions: TransferAnalysisEngine,
        attainment: ReliabilityEngine,
    ) -> None:
        self.loader = loader
        self.conditions = conditions
        self.attainment = attainment

    def execute(
        self,
        *,
        dims: list[int] | None,
        problems: list[int] | None,
        noise_stds: list[float] | None,
    ) -> ReliabilityAnalysisResult:
        snapshot = self.loader.load(dims=dims, problems=problems, noise_stds=noise_stds)
        config = snapshot.config.reliability
        native = self.conditions.condition_table(
            snapshot.native_records,
            config.primary_target,
            config.secondary_target,
            snapshot.config.target_eval_runs,
        ).rename(
            columns={
                "Target Problem": "Problem ID",
                "Successes": "Primary Successes",
                "Success Rate": "Primary Success Rate",
            }
        )
        noise = self.conditions.condition_table(
            snapshot.noise_records,
            config.primary_target,
            config.secondary_target,
            snapshot.config.target_eval_runs,
        )
        display = native.copy()
        if not display.empty:
            display["Model"] = display["Model"].map(snapshot.model_labels)
            display["Solver"] = display["Solver"].map(snapshot.solver_labels)
        primary = (
            display[
                (display["Strategy"] == config.primary_prompt_strategy) & display["Complete"]
            ].copy()
            if not display.empty
            else display
        )
        grid = np.array([], dtype=float)
        series: list[AttainmentSeries] = []
        models = sorted(primary["Model"].unique()) if not primary.empty else []
        diagnostics: list[str] = []
        if primary.empty:
            diagnostics.append("No complete current native primary-strategy conditions.")
        else:
            grid = np.logspace(0, np.log10(snapshot.config.budget), 200)
            grouped_runs: list[tuple[str, bool, list[RunTrace]]] = []
            for model in models:
                runs: list[RunTrace] = []
                for _, row in primary[primary["Model"] == model].iterrows():
                    runs.extend(
                        snapshot.dataset.get_runs(
                            int(row["Dim"]),
                            float(row["Noise Std"]),
                            int(row["Problem ID"]),
                            row["Solver"],
                        )
                    )
                if not runs:
                    diagnostics.append(f"No attainment traces: {model}")
                    continue
                grouped_runs.append((model, False, runs))
            paired = {
                (int(row["Dim"]), float(row["Noise Std"]), int(row["Problem ID"]))
                for _, row in primary.iterrows()
            }
            for baseline in snapshot.classical_solvers:
                runs = []
                for dim, noise_std, problem in paired:
                    condition = EvaluationCondition(
                        dim=dim, noise_std=noise_std, problem_id=problem
                    )
                    runs.extend(snapshot.dataset.get(condition, {}).get(baseline, []))
                if not runs:
                    continue
                grouped_runs.append((str(baseline), True, runs))
            for solver, is_baseline, runs in grouped_runs:
                curve, lower, upper = self.attainment.compute_attainment_band(
                    runs,
                    grid,
                    config.primary_target,
                    config.bootstrap_samples,
                    config.bootstrap_seed,
                )
                series.append(AttainmentSeries(solver, is_baseline, curve, lower, upper, len(runs)))
        return ReliabilityAnalysisResult(
            native,
            noise,
            primary,
            grid,
            series,
            models,
            snapshot.provenance("summary"),
            tuple(diagnostics),
        )
