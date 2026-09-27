"""Frozen-champion noise-robustness figure exports."""

from math import ceil

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmarking.application.analysis.view_data import AnalysisInputs
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from shared.config import RESULTS_DIR

from .cache import FigureCache
from .style import (
    FONT_FAMILY,
    get_model_scale_color,
    get_solver_line_style,
)


def export_noise_success_rates(inputs: AnalysisInputs, cache: FigureCache) -> pd.DataFrame:
    """Export returned-point reliability versus noise, separately from convergence."""
    rel = inputs.config.reliability
    engine = TransferAnalysisEngine()
    table = engine.condition_table(
        engine.frozen_noise_records(inputs.noise_records),
        rel.primary_target,
        rel.secondary_target,
        inputs.config.target_eval_runs,
    )
    aggregate = engine.aggregate_noise(
        table, rel.primary_prompt_strategy, rel.bootstrap_samples, rel.bootstrap_seed
    )
    report = RESULTS_DIR / "reports" / "noise_success_rates_v1.csv"
    report.parent.mkdir(parents=True, exist_ok=True)
    aggregate.to_csv(report, index=False)
    if aggregate.empty or not (aggregate["Noise Std"] > 0).any():
        print("No complete frozen-champion noisy trials: success-rate plot not exported.")
        return aggregate
    target = RESULTS_DIR / "figures" / "05_noise_robustness" / "success_rate_vs_noise.png"
    if not cache.needs_export(target):
        return aggregate
    dims = sorted(aggregate["Dim"].unique())
    models = sorted(aggregate["Model"].unique())
    labels = {model: inputs.model_names.get_clean_model_label(model) for model in models}
    noises = sorted(table["Noise Std"].unique())
    rows = ceil(len(dims) / 2)
    figure = make_subplots(
        rows=rows,
        cols=2,
        subplot_titles=[f"{dim}D" for dim in dims],
        specs=[[{} if r * 2 + c < len(dims) else None for c in range(2)] for r in range(rows)],
    )
    for index, dim in enumerate(dims):
        for model in models:
            group = (
                aggregate[(aggregate["Dim"] == dim) & (aggregate["Model"] == model)]
                .set_index("Noise Std")
                .reindex(noises)
            )
            if group["Primary Success Rate"].isna().all():
                continue
            baseline = str(model).lower() in {"cmaes", "cma-es", "de", "pso"}
            style = get_solver_line_style(labels[model])
            color = (
                str(style["color"])
                if baseline
                else get_model_scale_color(labels[model], sorted(labels.values()))
            )
            figure.add_trace(
                go.Scatter(
                    x=noises,
                    y=group["Primary Success Rate"],
                    mode="lines+markers",
                    name=labels[model],
                    legendgroup=labels[model],
                    showlegend=index == 0,
                    connectgaps=False,
                    line=dict(color=color, dash="solid" if baseline else "dash", width=2.5),
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=group["Bootstrap CI Upper"] - group["Primary Success Rate"],
                        arrayminus=group["Primary Success Rate"] - group["Bootstrap CI Lower"],
                    ),
                    customdata=group[["Conditions", "Trials"]].to_numpy(),
                    hovertemplate="σ=%{x}<br>Success=%{y:.1%}<br>Conditions=%{customdata[0]}<br>Trials=%{customdata[1]}<extra>%{fullData.name}</extra>",
                ),
                row=index // 2 + 1,
                col=index % 2 + 1,
            )
    figure.update_xaxes(
        title_text="Noise level σ",
        tickmode="array",
        tickvals=noises,
        ticktext=[f"{noise:g}" for noise in noises],
    )
    figure.update_yaxes(title_text="Returned-point success rate", range=[0, 1.05], tickformat=".0%")
    figure.update_layout(
        template="plotly_white",
        font=dict(family=FONT_FAMILY, size=14),
        title=f"Frozen-Champion Noise Robustness — Δf ≤ {rel.primary_target:g}<br><sup>Baseline strategy; equal-weight available functions; 95% condition-bootstrap intervals; missing data unplotted.</sup>",
        width=1400,
        height=rows * 380 + 200,
        margin=dict(t=110, b=130),
        legend=dict(orientation="h", y=-0.17),
    )
    cache.export(figure, target)
    return aggregate
