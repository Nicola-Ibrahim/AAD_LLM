"""Notebook-owned PNG export orchestration; accepts calculated results only."""

from pathlib import Path

import plotly.graph_objects as go

from benchmarking.application.analysis.results import (
    NoiseRobustnessResult,
    PerformanceAnalysisResult,
    ProfileAnalysisResult,
    ReliabilityAnalysisResult,
)

from . import generalization, performance, profiles, summary


class AnalysisFigureExporter:
    """Build and export figures without loading data or calculating statistics."""

    def __init__(self, results_dir: Path) -> None:
        self.results_dir = results_dir

    def export_figure(self, figure: go.Figure, target: Path) -> None:
        """Write a PNG on every call; images and Plotly objects are never cached."""
        if target.suffix.lower() != ".png":
            raise ValueError("Analysis figures are PNG-only.")
        target.parent.mkdir(parents=True, exist_ok=True)
        figure.write_image(str(target), scale=3)

    def export_profiles(self, results: ProfileAnalysisResult) -> None:
        """Optional presentation/export of already-calculated profiles."""
        directories = {
            "explicit": "02_explicit",
            "implicit": "03_implicit",
            "comparison": "04_implicit_vs_explicit",
        }
        for profile in results.conditions:
            if not profile.series:
                continue
            output = (
                self.results_dir
                / "figures"
                / directories[results.mode]
                / profile.model_slug
                / f"{profile.dim}D"
                / f"std_{profile.noise_std}"
            )
            for kind, filename in [
                (
                    "convergence",
                    "implicit_vs_noisy_convergence.png"
                    if results.mode == "comparison"
                    else "convergence_trajectories.png",
                ),
                ("ecdf", "target_precision_ecdf.png"),
            ]:
                target = output / filename
                figure = profiles.build_profile(
                    profile,
                    results.mode,
                    kind=kind,
                    title=f"<b>{results.mode.title()} {kind.upper()} — {profile.model} ({profile.dim}D, σ={profile.noise_std:g})</b><br><sup>Adaptive-target ECDFs are exploratory; fixed-target reliability is reported separately.</sup>",
                )
                self.export_figure(figure, target)

    def export_reliability(self, results: ReliabilityAnalysisResult) -> None:
        if not results.attainment:
            print("No current attainment traces; no aggregate thesis figures exported.")
            return
        path = (
            self.results_dir / "figures" / "06_thesis_summary"
        ) / "fig_10b_fixed_target_attainment.png"
        self.export_figure(summary.build_attainment_figure(results), path)

    def export_noise_robustness(self, results: NoiseRobustnessResult) -> None:
        if results.diagnostics:
            print("; ".join(results.diagnostics))
            return
        target = self.results_dir / "figures" / "05_noise_robustness" / "success_rate_vs_noise.png"
        self.export_figure(generalization.build_noise_success_figure(results), target)

    def export_model_scale(self, results: PerformanceAnalysisResult) -> None:
        target = (
            self.results_dir / "figures" / "06_thesis_summary"
        ) / "fig_09e_auc_ecdf_model_scale.png"
        if results.diagnostics:
            return
        self.export_figure(performance.build_model_scale_figure(results), target)

    def export_hardness_ablation(self, results: PerformanceAnalysisResult) -> None:
        for hardness in results.hardness:
            if not any(
                not table.empty and any(" / " in s for s in table["Solver"].unique())
                for table in hardness.tables.values()
            ):
                continue
            target = (
                (self.results_dir / "figures" / "02_explicit")
                / results.model_slugs[hardness.model]
                / f"{hardness.dim}D"
                / "figure_success_rate_by_hardness.png"
            )
            self.export_figure(performance.build_hardness_figure(results, hardness), target)
