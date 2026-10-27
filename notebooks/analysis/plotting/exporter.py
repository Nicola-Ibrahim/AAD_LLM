"""Notebook-owned PNG export orchestration; accepts calculated results only."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import plotly.graph_objects as go

from benchmark.application.analysis.results import (
    NoiseRobustnessResult,
    PerformanceAnalysisResult,
    ProfileAnalysisResult,
    ReliabilityAnalysisResult,
)
from shared.application.diagnostics import report_operation
from shared.application.errors import StorageError

from . import generalization, performance, profiles, summary

PROFILE_DIRECTORIES = {
    "explicit": "02_explicit",
    "implicit": "03_implicit",
    "comparison": "04_implicit_vs_explicit",
}


@dataclass(frozen=True)
class ExportSummary:
    written: tuple[Path, ...]
    skipped: tuple[str, ...]


class AnalysisFigureExporter:
    """Build and export figures without loading data or calculating statistics."""

    def __init__(self, results_dir: Path) -> None:
        self.results_dir = results_dir

    def export_figure(self, figure: go.Figure, target: Path) -> Path:
        """Write a PNG on every call; images and Plotly objects are never cached."""
        with report_operation(logging.getLogger("benchmark.exports"), "export figure"):
            if target.suffix.lower() != ".png":
                raise ValueError("Analysis figures are PNG-only.")
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                figure.write_image(str(target), scale=3)
            except (OSError, ValueError, RuntimeError) as error:
                raise StorageError(
                    f"PNG export failed: {target}. Check Kaleido/Chrome and write access."
                ) from error
            return target

    def export_profiles(self, results: ProfileAnalysisResult) -> ExportSummary:
        """Optional presentation/export of already-calculated profiles."""
        with report_operation(logging.getLogger("benchmark.exports"), "export profiles"):
            heading = (
                "Explicit versus implicit" if results.mode == "comparison" else results.mode.title()
            )
            outputs: dict[Literal["convergence", "ecdf"], str] = {
                "convergence": "implicit_vs_noisy_convergence.png"
                if results.mode == "comparison"
                else "convergence_trajectories.png",
                "ecdf": "target_precision_ecdf.png",
            }
            written = []
            skipped = []
            for profile in results.conditions:
                if not profile.series:
                    skipped.append(
                        f"No profile series: {profile.model}, {profile.dim}D, σ={profile.noise_std}"
                    )
                    continue
                output = (
                    self.results_dir
                    / "figures"
                    / PROFILE_DIRECTORIES[results.mode]
                    / profile.model
                    / f"{profile.dim}D"
                    / f"std_{profile.noise_std}"
                )
                for kind, filename in outputs.items():
                    target = output / filename
                    description = (
                        "Median with interquartile bands across available benchmark trials; lower is better."
                        if kind == "convergence"
                        else "Adaptive-target ECDFs are exploratory; fixed-target reliability is reported separately."
                    )
                    figure = profiles.build_profile(
                        profile,
                        results.mode,
                        kind=kind,
                        title=f"<b>{heading} {kind.upper()} — {profile.model} ({profile.dim}D, σ={profile.noise_std:g})</b><br><sup>{description}</sup>",
                    )
                    self.export_figure(figure, target)
                    written.append(target)
            return ExportSummary(tuple(written), tuple(skipped) + results.diagnostics)

    def export_reliability(self, results: ReliabilityAnalysisResult) -> ExportSummary:
        with report_operation(logging.getLogger("benchmark.exports"), "export reliability"):
            if not results.attainment:
                return ExportSummary((), ("No current attainment traces.",))
            path = (
                self.results_dir / "figures" / "06_thesis_summary"
            ) / "fig_10b_fixed_target_attainment.png"
            self.export_figure(summary.build_attainment_figure(results), path)
            return ExportSummary((path,), ())

    def export_noise_robustness(self, results: NoiseRobustnessResult) -> ExportSummary:
        with report_operation(logging.getLogger("benchmark.exports"), "export noise robustness"):
            if results.diagnostics:
                return ExportSummary((), results.diagnostics)
            target = (
                self.results_dir / "figures" / "05_noise_robustness" / "success_rate_vs_noise.png"
            )
            self.export_figure(generalization.build_noise_success_figure(results), target)
            return ExportSummary((target,), ())

    def export_model_scale(self, results: PerformanceAnalysisResult) -> ExportSummary:
        with report_operation(logging.getLogger("benchmark.exports"), "export model scale"):
            target = (
                self.results_dir / "figures" / "08_performance_comparison"
            ) / "fig_09e_auc_ecdf_model_scale.png"
            if results.diagnostics:
                return ExportSummary((), results.diagnostics)
            self.export_figure(performance.build_model_scale_figure(results), target)
            return ExportSummary((target,), ())

    def export_hardness_ablation(self, results: PerformanceAnalysisResult) -> ExportSummary:
        with report_operation(logging.getLogger("benchmark.exports"), "export hardness ablation"):
            written = []
            skipped = []
            for hardness in results.hardness:
                if not any(
                    not table.empty and any(" / " in s for s in table["Solver"].unique())
                    for table in hardness.tables.values()
                ):
                    skipped.append(f"No model hardness results: {hardness.model}, {hardness.dim}D")
                    continue
                target = (
                    (self.results_dir / "figures" / "02_explicit")
                    / hardness.model
                    / f"{hardness.dim}D"
                    / "figure_success_rate_by_hardness.png"
                )
                self.export_figure(performance.build_hardness_figure(results, hardness), target)
                written.append(target)
            return ExportSummary(tuple(written), tuple(skipped))
