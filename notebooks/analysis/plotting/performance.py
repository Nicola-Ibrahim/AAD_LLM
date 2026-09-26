"""Exploratory AUC and strategy-ablation figure exports."""

import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmarking.application.analysis.performance import PerformanceMetrics
from benchmarking.application.analysis.view_data import AnalysisInputs
from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.services.performance import PerformanceMetricsEngine
from shared.config import RESULTS_DIR

from .cache import FigureCache
from .style import (
    FONT_FAMILY,
    get_model_scale_color,
    get_solver_color,
    get_solver_line_style,
)

REPORTS_DIR = RESULTS_DIR / "reports"
THESIS_SUMMARY_DIR = RESULTS_DIR / "figures" / "06_thesis_summary"
EXPLICIT_DIR = RESULTS_DIR / "figures" / "02_explicit"


def export_performance_matrix(
    inputs: AnalysisInputs, metrics: PerformanceMetrics, cache: FigureCache
) -> None:
    if not cache.needs_export(THESIS_SUMMARY_DIR / "fig_09d_auc_ecdf_by_problem.png"):
        return
    prob_ids = [p for p in [1, 8, 11, 15, 21] if p in inputs.dataset.problem_ids]
    prob_labels = [f"{BBOBFunction.get_name(p)} (f{p})" for p in prob_ids]
    solvers_y = list(metrics.rankings.index)
    matrix_clean = np.zeros((len(solvers_y), len(prob_ids)))
    matrix_noisy = np.zeros((len(solvers_y), len(prob_ids)))
    for r_idx, s in enumerate(solvers_y):
        for c_idx, p in enumerate(prob_ids):
            c_sub = metrics.table[
                (metrics.table["Canonical Solver"] == s)
                & (metrics.table["Problem ID"] == p)
                & (metrics.table["Noise Std"] == inputs.clean_std)
            ]
            n_sub = metrics.table[
                (metrics.table["Canonical Solver"] == s)
                & (metrics.table["Problem ID"] == p)
                & (metrics.table["Noise Std"] == inputs.noisy_std)
            ]
            matrix_clean[r_idx, c_idx] = c_sub["AUC-ECDF (%)"].mean() if not c_sub.empty else 0.0
            matrix_noisy[r_idx, c_idx] = n_sub["AUC-ECDF (%)"].mean() if not n_sub.empty else 0.0
    fig9d = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            f"<b>(A) Clean (σ={inputs.clean_std})</b>",
            f"<b>(B) Noisy (σ={inputs.noisy_std})</b>",
        ],
        horizontal_spacing=0.1,
        shared_yaxes=True,
    )
    fig9d.add_trace(
        go.Heatmap(
            z=matrix_clean,
            x=prob_labels,
            y=solvers_y,
            colorscale=[
                [0.0, "#F8FAFC"],
                [0.25, "#E0F2FE"],
                [0.5, "#BAE6FD"],
                [0.75, "#7DD3FC"],
                [1.0, "#38BDF8"],
            ],
            zmin=0,
            zmax=70,
            text=[[f"{v:.1f}%" if v > 0 else "" for v in row] for row in matrix_clean],
            texttemplate="%{text}",
            textfont=dict(size=12, family=FONT_FAMILY),
            showscale=False,
        ),
        row=1,
        col=1,
    )
    fig9d.add_trace(
        go.Heatmap(
            z=matrix_noisy,
            x=prob_labels,
            y=solvers_y,
            colorscale=[
                [0.0, "#F8FAFC"],
                [0.25, "#E0F2FE"],
                [0.5, "#BAE6FD"],
                [0.75, "#7DD3FC"],
                [1.0, "#38BDF8"],
            ],
            zmin=0,
            zmax=70,
            text=[[f"{v:.1f}%" if v > 0 else "" for v in row] for row in matrix_noisy],
            texttemplate="%{text}",
            textfont=dict(size=12, family=FONT_FAMILY),
            colorbar=dict(
                title="<b>AUC-ECDF (%)</b>",
                title_font=dict(size=14, family=FONT_FAMILY),
                title_side="top",
                tickfont=dict(size=12, family=FONT_FAMILY),
                len=0.85,
            ),
        ),
        row=1,
        col=2,
    )
    for anno in fig9d.layout.annotations:
        anno.update(font=dict(size=16, color="#0F172A", family=FONT_FAMILY))
    plot_h = max(700, len(solvers_y) * 32 + 180)
    fig9d.update_layout(
        template="plotly_white",
        title=dict(
            text="<b>Figure 9D: Solver Performance Matrix Across BBOB Problem Landscapes</b><br><span style='font-size:13px;color:#475569;font-weight:normal;'>Area Under Runtime ECDF (AUC-ECDF %) Across Canonical Function Classes in Clean vs. Noisy Regimes</span>",
            font=dict(size=20, color="#0F172A", family=FONT_FAMILY),
            x=0.02,
            y=0.97,
        ),
        width=1420,
        height=plot_h,
        margin=dict(l=220, r=40, t=110, b=90),
    )
    fig9d.update_xaxes(
        tickangle=-25, tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"), row=1, col=1
    )
    fig9d.update_xaxes(
        tickangle=-25, tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"), row=1, col=2
    )
    fig9d.update_yaxes(
        tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"),
        autorange="reversed",
        row=1,
        col=1,
    )
    out_9d = THESIS_SUMMARY_DIR / "fig_09d_auc_ecdf_by_problem.png"
    if cache.needs_export(out_9d):
        cache.export(fig9d, out_9d)
    print("✅ Figure 9D (By Problem Heatmap) generated in results/figures/06_thesis_summary/.")


def export_model_scale(
    inputs: AnalysisInputs, metrics: PerformanceMetrics, cache: FigureCache
) -> None:
    if not cache.needs_export(THESIS_SUMMARY_DIR / "fig_09e_auc_ecdf_model_scale.png"):
        return
    fig9e = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            f"<b>(A) Clean (σ={inputs.clean_std})</b>",
            f"<b>(B) Noisy (σ={inputs.noisy_std})</b>",
        ],
        horizontal_spacing=0.1,
        shared_yaxes=True,
    )
    dims = [d for d in [2, 3, 5, 10] if d in inputs.dataset.dims]

    def extract_model_scale(m: str) -> float:
        match = re.search("(\\d+(?:\\.\\d+)?)\\s*[bB]", m)
        return float(match.group(1)) if match else 0.0

    discovered_models = sorted(list(inputs.models_to_solvers.keys()), key=extract_model_scale)
    for col_idx, (n_std, title_sfx) in enumerate(
        [(inputs.clean_std, "Clean"), (inputs.noisy_std, "Noisy")], start=1
    ):
        for model_name in discovered_models:
            sub_m = metrics.table[metrics.table["Solver"].str.startswith(f"{model_name} /")]
            c_m = sub_m[sub_m["Noise Std"] == n_std]
            vals_m = [
                c_m[c_m["Dim"] == d]["AUC-ECDF (%)"].mean()
                if not c_m[c_m["Dim"] == d].empty
                else np.nan
                for d in dims
            ]
            if any((pd.notna(v) and (not np.isnan(v)) for v in vals_m)):
                m_color = get_model_scale_color(model_name, inputs.models_to_solvers)
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
        for baseline in inputs.classical_solvers:
            b_sub = metrics.table[
                (metrics.table["Solver"] == baseline) & (metrics.table["Noise Std"] == n_std)
            ]
            b_vals = [
                b_sub[b_sub["Dim"] == d]["AUC-ECDF (%)"].mean()
                if not b_sub[b_sub["Dim"] == d].empty
                else np.nan
                for d in dims
            ]
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
            text="<b>Figure 9E: LLM Parameter Scale Ablation Across Dimensions</b><br><span style='font-size:13px;color:#475569;font-weight:normal;'>Mean Area Under Runtime ECDF (AUC-ECDF %) Across Synthesized Model Scales vs. Classical Baselines in Clean and Noisy Regimes</span>",
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
    out_9e = THESIS_SUMMARY_DIR / "fig_09e_auc_ecdf_model_scale.png"
    if cache.needs_export(out_9e):
        cache.export(fig9e, out_9e)
    print("✅ Figure 9E (Model Scale Ablation) generated from currently discovered models.")


def export_hardness_ablation(
    inputs: AnalysisInputs, metrics: PerformanceMetrics, cache: FigureCache
) -> None:
    def render_model_success_rate_by_hardness(
        model_tag: str, solvers_list: list[str], dim: int
    ) -> None:
        out_p = (
            EXPLICIT_DIR
            / inputs.model_slugs[model_tag]
            / f"{dim}D"
            / "figure_success_rate_by_hardness.png"
        )
        if not cache.needs_export(out_p):
            return
        has_model_data = False
        for noise_level in [inputs.clean_std, inputs.noisy_std]:
            df_hard = PerformanceMetricsEngine().compute_hardness_success_rates(
                inputs.dataset, dim, solvers_list, noise_level=noise_level
            )
            if not df_hard.empty and any((" / " in s for s in df_hard["Solver"].unique())):
                has_model_data = True
                break
        if not has_model_data:
            return
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=(
                f"<b>(A) Deterministic Landscape (σ={inputs.clean_std}, {dim}D)</b>",
                f"<b>(B) Noisy Stochastic Landscape (σ={inputs.noisy_std}, {dim}D)</b>",
            ),
            horizontal_spacing=0.1,
        )
        for c_idx, noise_level in enumerate([inputs.clean_std, inputs.noisy_std], start=1):
            df_hard = PerformanceMetricsEngine().compute_hardness_success_rates(
                inputs.dataset, dim, solvers_list, noise_level=noise_level
            )
            for solver in solvers_list:
                sub_s = (
                    df_hard[df_hard["Solver"] == solver] if not df_hard.empty else pd.DataFrame()
                )
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
        slug = inputs.model_slugs[model_tag]
        m_dir = EXPLICIT_DIR / slug / f"{dim}D"
        m_dir.mkdir(parents=True, exist_ok=True)
        out_p = m_dir / "figure_success_rate_by_hardness.png"
        if cache.needs_export(out_p):
            cache.export(fig, out_p)

    for dim in inputs.dataset.dims:
        for model_name, solvers_list in inputs.models_to_solvers.items():
            solvers_to_plot = solvers_list + inputs.classical_solvers
            render_model_success_rate_by_hardness(model_name, solvers_to_plot, dim)
    print(
        "✅ Model-specific success rate by hardness generated for all discovered models and dimensions."
    )
