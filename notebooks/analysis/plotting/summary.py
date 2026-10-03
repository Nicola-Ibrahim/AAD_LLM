"""Fixed-target attainment figure and reproducible terminal reliability CSVs."""

import numpy as np
import plotly.graph_objects as go

from benchmarking.application.analysis.results import ReliabilityAnalysisResult

from .style import FONT_FAMILY


def build_attainment_figure(results: ReliabilityAnalysisResult) -> go.Figure:
    model_order = results.model_order
    reliability_palette = ["#0284C7", "#7C3AED", "#0F766E", "#D97706", "#DB2777", "#475569"]
    model_colors = {
        model: reliability_palette[idx % len(reliability_palette)]
        for idx, model in enumerate(model_order)
    }
    baseline_styles = {"CMA-ES": "#334155", "DE": "#7C3AED", "PSO": "#0F766E"}
    eval_grid_reliability = results.evaluations
    if not len(eval_grid_reliability):
        raise ValueError("No complete native conditions available for attainment.")
    max_budget = eval_grid_reliability[-1]
    fig10b = go.Figure()
    for series in results.attainment:
        if series.baseline:
            fig10b.add_trace(
                go.Scatter(
                    x=eval_grid_reliability,
                    y=series.probability,
                    mode="lines",
                    name=series.solver,
                    line=dict(
                        color=baseline_styles.get(series.solver, "#475569"), width=3.2, dash="solid"
                    ),
                )
            )
            continue
        model = series.solver
        curve, lower, upper = series.probability, series.lower, series.upper
        color = model_colors[model]
        fig10b.add_trace(
            go.Scatter(
                x=eval_grid_reliability,
                y=upper,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig10b.add_trace(
            go.Scatter(
                x=eval_grid_reliability,
                y=lower,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(56, 189, 248, 0.12)",
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig10b.add_trace(
            go.Scatter(
                x=eval_grid_reliability,
                y=curve,
                mode="lines",
                name=model,
                line=dict(color=color, width=2.6, dash="dash"),
            )
        )
    fig10b.update_layout(
        template="plotly_white",
        title=dict(
            text='<b>Figure 10B: Clean Target Attainment During Search</b><br><span style="font-size:13px;color:#475569;font-weight:normal;">Best-queried clean-gap attainment (not returned-point reliability); LLMs dashed, classical baselines solid; 95% trial-bootstrap bands; shorter-budget traces are carried forward within the plotted range</span>',
            font=dict(size=20, color="#0F172A", family=FONT_FAMILY),
            x=0.02,
            y=0.97,
        ),
        width=1420,
        height=720,
        margin=dict(l=95, r=40, t=115, b=110),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=12, family=FONT_FAMILY),
        ),
    )
    fig10b.update_xaxes(
        type="log",
        range=[0, np.log10(max_budget)],
        title_text="<b>Evaluations</b>",
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        ticks="outside",
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
    )
    fig10b.update_yaxes(
        range=[0, 1.05],
        title_text="<b>Probability of Querying a Target Point</b>",
        tickformat=".0%",
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        ticks="outside",
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
    )
    return fig10b
