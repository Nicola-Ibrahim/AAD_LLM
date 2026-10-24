"""Exploratory AUC and strategy-ablation figure exports."""

import re
from math import ceil

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmark.application.analysis.results import (
    HardnessSummary,
    PerformanceAnalysisResult,
)

from .style import (
    FONT_FAMILY,
    get_model_scale_color,
    get_solver_color,
    get_solver_line_style,
)


def _model_size(model: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", model)
    return float(match.group(1)) if match else 0.0


def _dimension_values(table: pd.DataFrame, model: str, noise: float, dims: list[int]) -> pd.Series:
    selected = table.loc[(table["Model"] == model) & (table["Noise Std"] == noise)]
    return selected.set_index("Dim")["AUC-ECDF (%)"].reindex(dims)


def build_model_scale_figure(results: PerformanceAnalysisResult) -> go.Figure:
    noise_levels = sorted(results.model_scale["Noise Std"].unique())
    if not noise_levels:
        raise ValueError("No noise-level summaries available for performance comparison.")
    rows = ceil(len(noise_levels) / 2)
    figure = make_subplots(
        rows=rows,
        cols=2,
        subplot_titles=[
            f"<b>{'Clean' if noise == 0 else 'Noisy'} (σ={noise:g})</b>" for noise in noise_levels
        ],
        specs=[
            [{} if 2 * r + c < len(noise_levels) else None for c in range(2)] for r in range(rows)
        ],
        horizontal_spacing=0.1,
        vertical_spacing=0.18 if rows > 1 else 0,
        shared_yaxes=True,
    )
    dims = sorted(results.dims)

    discovered_models = sorted(results.models_to_solvers, key=_model_size)
    shown_models: set[str] = set()
    for panel_idx, n_std in enumerate(noise_levels):
        row_idx, col_idx = panel_idx // 2 + 1, panel_idx % 2 + 1
        for model_name in discovered_models:
            values = _dimension_values(results.model_scale, model_name, n_std, dims)
            auc_values = values.to_list()
            if values.isna().all():
                continue
            model_color = get_model_scale_color(model_name, results.models_to_solvers)
            figure.add_trace(
                go.Bar(
                    x=[f"{d}D" for d in dims],
                    y=auc_values,
                    name=model_name,
                    marker=dict(color=model_color, line=dict(color="#0F172A", width=0.8)),
                    text=[f"{v:.1f}%" if pd.notna(v) else "" for v in auc_values],
                    textposition="outside",
                    textfont=dict(size=11, family=FONT_FAMILY, color="#1E293B"),
                    legendgroup=model_name,
                    showlegend=model_name not in shown_models,
                ),
                row=row_idx,
                col=col_idx,
            )
            shown_models.add(model_name)
        for baseline in results.classical_solvers:
            baseline_values = _dimension_values(
                results.model_scale, baseline, n_std, dims
            ).to_list()
            b_style = get_solver_line_style(baseline)
            figure.add_trace(
                go.Scatter(
                    x=[f"{d}D" for d in dims],
                    y=baseline_values,
                    mode="lines+markers",
                    name=baseline,
                    line=dict(color=b_style["color"], dash=b_style["dash"], width=2.2),
                    marker=dict(
                        size=8,
                        symbol="diamond"
                        if "cma" in baseline.lower()
                        else "square"
                        if "pso" in baseline.lower()
                        else "circle",
                    ),
                    legendgroup=baseline,
                    showlegend=baseline not in shown_models,
                ),
                row=row_idx,
                col=col_idx,
            )
            shown_models.add(baseline)
    for anno in figure.layout.annotations:
        anno.update(font=dict(size=16, color="#0F172A", family=FONT_FAMILY))
    figure.update_layout(
        template="plotly_white",
        title=dict(
            text="<b>LLM Performance Across Dimensions and Noise Levels</b><br><span style='font-size:13px;color:#475569;font-weight:normal;'>Mean adaptive-target AUC-ECDF across included functions, strategies and synthesis modes; targets differ by noise level</span>",
            font=dict(size=20, color="#0F172A", family=FONT_FAMILY),
            x=0.02,
            y=0.97,
        ),
        barmode="group",
        width=1380,
        height=max(640, rows * 420 + 150),
        margin=dict(l=70, r=40, t=110, b=130),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=13, family=FONT_FAMILY),
        ),
    )
    figure.update_yaxes(
        title_text="<b>Mean AUC-ECDF (%)</b>",
        title_font=dict(size=15, family=FONT_FAMILY, color="#0F172A"),
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
        range=[0, 105],
        showgrid=True,
        gridcolor="#F1F5F9",
    )
    figure.update_xaxes(
        title_text="<b>Problem Dimension</b>",
        title_font=dict(size=15, family=FONT_FAMILY, color="#0F172A"),
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
    )
    return figure


def build_hardness_figure(
    results: PerformanceAnalysisResult, summary: HardnessSummary
) -> go.Figure:
    model_tag, dim, solvers_list = summary.model, summary.dim, summary.solvers
    tables = {noise: table for noise, table in summary.tables.items() if not table.empty}
    if not tables:
        raise ValueError("No available hardness results to plot.")
    fig = make_subplots(
        rows=1,
        cols=len(tables),
        subplot_titles=[
            f"<b>{'Deterministic' if noise == 0 else 'Noisy'} Landscape (σ={noise:g}, {dim}D)</b>"
            for noise in tables
        ],
        horizontal_spacing=0.1,
    )
    shown_solvers: set[str] = set()
    for c_idx, df_hard in enumerate(tables.values(), start=1):
        for solver in solvers_list:
            sub_s = df_hard.loc[df_hard["Solver"] == solver]
            if sub_s.empty:
                continue
            fig.add_trace(
                go.Bar(
                    name=solver,
                    x=sub_s["Class"],
                    y=sub_s["Success Rate"],
                    marker=dict(
                        color=get_solver_color(solver),
                        line=dict(color="#0F172A", width=0.8),
                    ),
                    showlegend=solver not in shown_solvers,
                ),
                row=1,
                col=c_idx,
            )
            shown_solvers.add(solver)
    fig.update_xaxes(
        title_text="<b>Landscape Hardness Class</b>",
        title_font=dict(size=14, family=FONT_FAMILY, color="#0F172A"),
        tickangle=-15,
        tickfont=dict(size=12, family=FONT_FAMILY, color="#1E293B"),
    )
    fig.update_yaxes(
        title_text="<b>Target Success Rate (Δy ≤ 10⁻⁸)</b>",
        title_font=dict(size=14, family=FONT_FAMILY, color="#0F172A"),
        tickfont=dict(size=12, family=FONT_FAMILY, color="#1E293B"),
        range=[0, 1.1],
        showgrid=True,
        gridcolor="#F1F5F9",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        tickfont=dict(size=12, family=FONT_FAMILY, color="#1E293B"),
        range=[0, 1.1],
        showgrid=True,
        gridcolor="#F1F5F9",
    )
    for anno in fig.layout.annotations:
        anno.update(font=dict(size=15, color="#0F172A", family=FONT_FAMILY))
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"<b>Empirical Success Rate by BBOB Landscape Hardness — {model_tag.upper()} ({dim}D)</b><br><span style='font-size:13px;color:#475569;font-weight:normal;'>Search-target success rates for available problem groups and noise levels</span>",
            x=0.02,
            y=0.96,
            font=dict(size=16, color="#1E293B", family=FONT_FAMILY),
        ),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        width=max(900, 620 * len(tables)),
        height=590,
        margin=dict(l=80, r=40, t=100, b=120),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=12, family=FONT_FAMILY),
        ),
    )
    return fig
