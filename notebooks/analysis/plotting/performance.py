"""Exploratory AUC and strategy-ablation figure exports."""

import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmarking.application.analysis.results import (
    HardnessSummary,
    PerformanceAnalysisResult,
)

from .style import (
    FONT_FAMILY,
    get_model_scale_color,
    get_solver_color,
    get_solver_line_style,
)


def build_model_scale_figure(results: PerformanceAnalysisResult) -> go.Figure:
    fig9e = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            f"<b>(A) Clean (σ={results.clean_std})</b>",
            f"<b>(B) Noisy (σ={results.noisy_std})</b>",
        ],
        horizontal_spacing=0.1,
        shared_yaxes=True,
    )
    dims = [d for d in [2, 3, 5, 10] if d in results.dims]

    def extract_model_scale(m: str) -> float:
        match = re.search("(\\d+(?:\\.\\d+)?)\\s*[bB]", m)
        return float(match.group(1)) if match else 0.0

    discovered_models = sorted(list(results.models_to_solvers.keys()), key=extract_model_scale)
    for col_idx, (n_std, title_sfx) in enumerate(
        [(results.clean_std, "Clean"), (results.noisy_std, "Noisy")], start=1
    ):
        for model_name in discovered_models:
            c_m = results.model_scale[
                (results.model_scale["Model"] == model_name)
                & (results.model_scale["Noise Std"] == n_std)
            ].set_index("Dim")
            vals_m = c_m.reindex(dims)["AUC-ECDF (%)"].to_list()
            if any((pd.notna(v) and (not np.isnan(v)) for v in vals_m)):
                m_color = get_model_scale_color(model_name, results.models_to_solvers)
                fig9e.add_trace(
                    go.Bar(
                        x=[f"{d}D" for d in dims],
                        y=vals_m,
                        name=model_name,
                        marker=dict(color=m_color, line=dict(color="#0F172A", width=0.8)),
                        text=[
                            f"{v:.1f}%" if pd.notna(v) and (not np.isnan(v)) else "" for v in vals_m
                        ],
                        textposition="outside",
                        textfont=dict(size=11, family=FONT_FAMILY, color="#1E293B"),
                        showlegend=col_idx == 1,
                    ),
                    row=1,
                    col=col_idx,
                )
        for baseline in results.classical_solvers:
            b_sub = results.model_scale[
                (results.model_scale["Model"] == baseline)
                & (results.model_scale["Noise Std"] == n_std)
            ].set_index("Dim")
            b_vals = b_sub.reindex(dims)["AUC-ECDF (%)"].to_list()
            b_style = get_solver_line_style(baseline)
            fig9e.add_trace(
                go.Scatter(
                    x=[f"{d}D" for d in dims],
                    y=b_vals,
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
                    showlegend=col_idx == 1,
                ),
                row=1,
                col=col_idx,
            )
    for anno in fig9e.layout.annotations:
        anno.update(font=dict(size=16, color="#0F172A", family=FONT_FAMILY))
    fig9e.update_layout(
        template="plotly_white",
        title=dict(
            text="<b>Figure 9E: LLM Model Comparison Across Dimensions</b><br><span style='font-size:13px;color:#475569;font-weight:normal;'>Mean Area Under Runtime ECDF (AUC-ECDF %) Across Synthesized Models vs. Classical Baselines in Clean and Noisy Regimes</span>",
            font=dict(size=20, color="#0F172A", family=FONT_FAMILY),
            x=0.02,
            y=0.97,
        ),
        barmode="group",
        width=1380,
        height=640,
        margin=dict(l=70, r=40, t=110, b=90),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.14,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=13, family=FONT_FAMILY),
        ),
    )
    fig9e.update_yaxes(
        title_text="<b>Mean AUC-ECDF (%)</b>",
        title_font=dict(size=15, family=FONT_FAMILY, color="#0F172A"),
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
        range=[0, 65],
        showgrid=True,
        gridcolor="#F1F5F9",
        row=1,
        col=1,
    )
    fig9e.update_yaxes(
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
        range=[0, 65],
        showgrid=True,
        gridcolor="#F1F5F9",
        row=1,
        col=2,
    )
    fig9e.update_xaxes(
        title_text="<b>Problem Dimension</b>",
        title_font=dict(size=15, family=FONT_FAMILY, color="#0F172A"),
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
        row=1,
        col=1,
    )
    fig9e.update_xaxes(
        title_text="<b>Problem Dimension</b>",
        title_font=dict(size=15, family=FONT_FAMILY, color="#0F172A"),
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
        row=1,
        col=2,
    )
    return fig9e


def build_hardness_figure(
    results: PerformanceAnalysisResult, summary: HardnessSummary
) -> go.Figure:
    model_tag, dim, solvers_list = summary.model, summary.dim, summary.solvers
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            f"<b>(A) Deterministic Landscape (σ={results.clean_std}, {dim}D)</b>",
            f"<b>(B) Noisy Stochastic Landscape (σ={results.noisy_std}, {dim}D)</b>",
        ),
        horizontal_spacing=0.1,
    )
    for c_idx, noise_level in enumerate([results.clean_std, results.noisy_std], start=1):
        df_hard = summary.tables[noise_level]
        for solver in solvers_list:
            sub_s = df_hard[df_hard["Solver"] == solver] if not df_hard.empty else pd.DataFrame()
            if not sub_s.empty:
                fig.add_trace(
                    go.Bar(
                        name=solver,
                        x=sub_s["Class"],
                        y=sub_s["Success Rate"],
                        marker=dict(
                            color=get_solver_color(solver),
                            line=dict(color="#0F172A", width=0.8),
                        ),
                        showlegend=c_idx == 1,
                    ),
                    row=1,
                    col=c_idx,
                )
    fig.update_xaxes(
        title_text="<b>Landscape Hardness Class</b>",
        title_font=dict(size=14, family=FONT_FAMILY, color="#0F172A"),
        tickangle=-15,
        tickfont=dict(size=12, family=FONT_FAMILY, color="#1E293B"),
        row=1,
        col=1,
    )
    fig.update_xaxes(
        title_text="<b>Landscape Hardness Class</b>",
        title_font=dict(size=14, family=FONT_FAMILY, color="#0F172A"),
        tickangle=-15,
        tickfont=dict(size=12, family=FONT_FAMILY, color="#1E293B"),
        row=1,
        col=2,
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
        row=1,
        col=2,
    )
    for anno in fig.layout.annotations:
        anno.update(font=dict(size=15, color="#0F172A", family=FONT_FAMILY))
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"<b>Empirical Success Rate by BBOB Landscape Hardness — {model_tag.upper()} ({dim}D)</b><br><span style='font-size:13px;color:#475569;font-weight:normal;'>Comparison of Target Precision Hitting Rates Across 5 Problem Classes in Deterministic vs. Noisy Regimes</span>",
            x=0.02,
            y=0.96,
            font=dict(size=16, color="#1E293B", family=FONT_FAMILY),
        ),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.08,
        width=1240,
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
