"""Secondary frozen-champion noise and cross-function figure exports."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from benchmarking.application.analysis.view_data import AnalysisInputs
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationDataset
from shared.config import RESULTS_DIR

from .cache import FigureCache
from .profiles import ProfileCurve, build_profile
from .style import CLASSICAL_BASELINES, FONT_FAMILY, clean_solver_name, get_solver_line_style

REPORTS_DIR = RESULTS_DIR / "reports"
TRANSFER_FIGURES_DIR = RESULTS_DIR / "figures" / "07_cross_function"


def export_cross_function(inputs: AnalysisInputs, cache: FigureCache) -> pd.DataFrame:
    engine = TransferAnalysisEngine()
    rel = inputs.config.reliability
    transfer_table = engine.condition_table(
        inputs.transfer_records,
        rel.primary_target,
        rel.secondary_target,
        inputs.config.target_eval_runs,
    )
    aggregate = engine.aggregate_transfer(transfer_table, rel.bootstrap_samples, rel.bootstrap_seed)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    transfer_table.to_csv(REPORTS_DIR / "cross_function_reliability_v1.csv", index=False)
    aggregate.to_csv(REPORTS_DIR / "cross_function_aggregate_v1.csv", index=False)
    baseline_table = engine.condition_table(
        [r for r in inputs.reference_records if float(r["noise_std"]) == 0.0],
        rel.primary_target,
        rel.secondary_target,
        inputs.config.target_eval_runs,
    )
    if transfer_table.empty:
        print("No current cross-function results yet; run the opt-in campaign in notebook 03.")
    else:
        TRANSFER_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
        for (model, dim), group in transfer_table.groupby(["Model", "Dim"], sort=True):
            targets = sorted(
                set(inputs.config.cross_function_problem_ids) | set(group["Source Problem"])
            )
            model_slug = inputs.model_names.get_model_slug(model)
            target_path = TRANSFER_FIGURES_DIR / f"{model_slug}_{dim}D_transfer_matrix.png"
            if not cache.needs_export(target_path):
                continue
            complete = group[group["Complete"]]
            matrix = complete.pivot(
                index="Source Problem", columns="Target Problem", values="Success Rate"
            ).reindex(index=targets, columns=targets)
            annotations = np.full(matrix.shape, "Missing", dtype=object)
            for _, result in complete.iterrows():
                if result["Source Problem"] in targets and result["Target Problem"] in targets:
                    annotations[
                        targets.index(result["Source Problem"]),
                        targets.index(result["Target Problem"]),
                    ] = f"{int(result['Successes'])}/{int(result['Trials'])}"
            fig = go.Figure(
                go.Heatmap(
                    z=matrix.to_numpy(),
                    x=[f"f{p}" for p in targets],
                    y=[f"f{p}" for p in targets],
                    zmin=0,
                    zmax=1,
                    colorscale="Blues",
                    text=annotations,
                    texttemplate="%{text}",
                    hoverongaps=False,
                    colorbar=dict(title="Success probability"),
                )
            )
            for row_index, source in enumerate(targets):
                for col_index, target in enumerate(targets):
                    if pd.isna(matrix.iloc[row_index, col_index]):
                        fig.add_annotation(
                            x=f"f{target}", y=f"f{source}", text="Missing", showarrow=False
                        )
            references = []
            if not baseline_table.empty:
                for baseline, reference in baseline_table[
                    baseline_table["Complete"] & (baseline_table["Dim"] == dim)
                ].groupby("Model", sort=True):
                    reference = reference.set_index("Target Problem")["Success Rate"]
                    references.append(
                        f"{baseline}: "
                        + ", ".join(
                            (
                                f"f{p}={reference[p]:.0%}" if p in reference else f"f{p}=missing"
                                for p in targets
                            )
                        )
                    )
            fig.update_layout(
                template="plotly_white",
                font=dict(family=FONT_FAMILY, size=15),
                title=f"Frozen-Champion Cross-Function Generalization — {inputs.model_names.get_clean_model_label(model)} ({dim}D)",
                xaxis_title="Evaluation function",
                yaxis_title="Synthesis function",
                plot_bgcolor="#D1D5DB",
                width=1150,
                height=820,
                margin=dict(l=90, r=80, t=100, b=160),
            )
            fig.add_annotation(
                x=0,
                y=-0.22,
                xref="paper",
                yref="paper",
                xanchor="left",
                showarrow=False,
                text="<br>".join(references)
                + f"<br>Fixed returned-point target: Δf ≤ {rel.primary_target:g}; diagonal = native function.",
                font=dict(size=12),
            )
            model_slug = inputs.model_names.get_model_slug(model)
            cache.export(fig, TRANSFER_FIGURES_DIR / f"{model_slug}_{dim}D_transfer_matrix.png")
        print("Cross-function tables and PNG matrices exported; native rankings are unchanged.")
    return transfer_table


def export_noise_robustness(inputs: AnalysisInputs, cache: FigureCache) -> None:
    noise_data = EvaluationDataset()
    for record in inputs.noise_records:
        label = inputs.model_names.resolve_folder_solver_name(str(record["solver_folder"]))
        for condition, solvers in inputs.dataset.items():
            if (condition.dim, condition.noise_std, condition.problem_id) == (
                record["dim"],
                record["noise_std"],
                record["problem_id"],
            ):
                for run in solvers.get(label, [])[: int(record["n_runs"])]:
                    noise_data.add_run(condition, label, run)
    colors = {0.0: "#0284C7", 0.05: "#10B981", 0.1: "#F59E0B", 0.2: "#EF4444"}
    rel = inputs.config.reliability
    targets = {
        noise: np.array([rel.primary_target, rel.secondary_target])
        for noise in noise_data.noise_stds
    }
    for dim in noise_data.dims:
        for solver in noise_data.solvers:
            dash = str(get_solver_line_style(solver)["dash"])
            curves = [
                ProfileCurve(solver, f"σ = {noise:g}", colors.get(noise, "#64748B"), dash, noise)
                for noise in noise_data.noise_stds
            ]
            if solver in CLASSICAL_BASELINES:
                directory = Path("classical_baselines") / solver.lower().replace("-", "_")
            else:
                model, strategy = clean_solver_name(solver).split(" / ", 1)
                directory = Path("explicit") / model.lower().replace(" ", "-") / strategy.lower()
            output = RESULTS_DIR / "figures" / "05_noise_robustness" / f"{dim}D" / directory
            for kind, filename in [
                ("convergence", "convergence_noise_overlay.png"),
                ("ecdf", "ecdf_noise_overlay.png"),
            ]:
                path = output / filename
                if cache.needs_export(path):
                    figure = build_profile(
                        inputs,
                        noise_data,
                        curves,
                        targets,
                        dim=dim,
                        kind=kind,
                        title=f"<b>Frozen-Champion Noise Robustness — {clean_solver_name(solver)} ({dim}D)</b><br><sup>Same code across noise levels; fixed-target ECDF, best-queried clean-gap convergence.</sup>",
                    )
                    cache.export(figure, path)
