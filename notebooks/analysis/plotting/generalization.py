"""Frozen-champion noise-robustness figure exports."""

from math import ceil

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmarking.application.analysis.results import NoiseRobustnessResult

from .style import (
    FONT_FAMILY,
    get_model_scale_color,
    get_solver_line_style,
)


def build_noise_success_figure(results: NoiseRobustnessResult) -> go.Figure:
    """Present precomputed returned-point reliability and confidence intervals."""
    table, aggregate = results.conditions, results.aggregate
    if aggregate.empty or not (aggregate["Noise Std"] > 0).any():
        raise ValueError("No complete frozen-champion noisy trials.")
    dims = sorted(aggregate["Dim"].unique())
    models = sorted(aggregate["Model"].unique())
    labels = {model: results.model_labels[model] for model in models}
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
        title=f"Frozen-Champion Noise Robustness — Δf ≤ {results.primary_target:g}<br><sup>Baseline strategy; equal-weight available functions; 95% condition-bootstrap intervals; missing data unplotted.</sup>",
        width=1400,
        height=rows * 380 + 200,
        margin=dict(t=110, b=130),
        legend=dict(orientation="h", y=-0.17),
    )
    return figure
