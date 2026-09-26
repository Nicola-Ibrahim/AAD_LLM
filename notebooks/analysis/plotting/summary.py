"""Three cached primary thesis PNGs; no detailed profile sweeps."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from benchmarking.application.analysis.view_data import AnalysisInputs
from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationCondition
from .cache import FigureCache
from .style import FONT_FAMILY
from shared.config import RESULTS_DIR

REPORTS_DIR = RESULTS_DIR / "reports"
THESIS_SUMMARY_DIR = RESULTS_DIR / "figures" / "06_thesis_summary"


def _reliability_matrix(
    inputs: AnalysisInputs, primary: pd.DataFrame, noise_terminal: pd.DataFrame
) -> go.Figure:
    model_order = sorted(primary["Model"].unique())
    problem_order = [p for p in [1, 8, 11, 15, 21] if p in primary["Problem ID"].unique()]
    problem_labels = [f"{BBOBFunction.get_name(p)} (f{p})" for p in problem_order]
    blue_scale = [
        [0.0, "#F8FAFC"],
        [0.25, "#E0F2FE"],
        [0.5, "#BAE6FD"],
        [0.75, "#7DD3FC"],
        [1.0, "#38BDF8"],
    ]
    fig10a = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        horizontal_spacing=0.1,
        subplot_titles=[
            "<b>(A) Clean (sigma = 0.0)</b>",
            "<b>(B) Noisy (mean across sigma > 0)</b>",
        ],
    )
    for col, subset in enumerate(
        [primary[primary["Noise Std"] == 0.0], primary[primary["Noise Std"] > 0.0]], start=1
    ):
        grouped = subset.groupby(["Model", "Problem ID"], as_index=False)[
            ["Primary Successes", "Trials"]
        ].sum()
        grouped["Rate"] = grouped["Primary Successes"] / grouped["Trials"]
        rate = grouped.pivot(index="Model", columns="Problem ID", values="Rate").reindex(
            index=model_order, columns=problem_order
        )
        ann = (
            grouped.assign(
                label=grouped["Primary Successes"].astype(int).astype(str)
                + "/"
                + grouped["Trials"].astype(int).astype(str)
            )
            .pivot(index="Model", columns="Problem ID", values="label")
            .reindex(index=model_order, columns=problem_order)
            .fillna("—")
        )
        fig10a.add_trace(
            go.Heatmap(
                z=rate.to_numpy() * 100,
                x=problem_labels,
                y=model_order,
                colorscale=blue_scale,
                zmin=0,
                zmax=100,
                text=ann.to_numpy(),
                texttemplate="%{text}",
                textfont=dict(size=12, family=FONT_FAMILY),
                showscale=col == 2,
                colorbar=dict(
                    title="<b>Success (%)</b>",
                    title_side="top",
                    tickfont=dict(size=12, family=FONT_FAMILY),
                    len=0.82,
                ),
            ),
            row=1,
            col=col,
        )
    for annotation in fig10a.layout.annotations:
        annotation.update(font=dict(size=16, color="#0F172A", family=FONT_FAMILY))
    fig10a.update_layout(
        template="plotly_white",
        title=dict(
            text='<b>Figure 10A: Reliable Solution Attainment Across BBOB Landscapes</b><br><span style="font-size:13px;color:#475569;font-weight:normal;">Fixed target Delta y <= 10^-8; cells show successful trials / completed trials; baseline prompt strategy</span>',
            font=dict(size=20, color="#0F172A", family=FONT_FAMILY),
            x=0.02,
            y=0.97,
        ),
        width=1420,
        height=max(620, 130 * len(model_order) + 230),
        margin=dict(l=220, r=80, t=115, b=105),
    )
    fig10a.update_xaxes(tickangle=-22, tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B"))
    fig10a.update_yaxes(
        autorange="reversed", tickfont=dict(size=13, family=FONT_FAMILY, color="#1E293B")
    )
    return fig10a


def _attainment_profile(
    inputs: AnalysisInputs, primary: pd.DataFrame, noise_terminal: pd.DataFrame
) -> go.Figure:
    model_order = sorted(primary["Model"].unique())
    reliability_palette = ["#0284C7", "#7C3AED", "#0F766E", "#D97706", "#DB2777", "#475569"]
    model_colors = {
        model: reliability_palette[idx % len(reliability_palette)]
        for idx, model in enumerate(model_order)
    }
    baseline_styles = {"CMA-ES": "#334155", "DE": "#7C3AED", "PSO": "#0F766E"}
    baseline_solvers = [solver for solver in inputs.dataset.solvers if " / " not in str(solver)]
    eval_grid_reliability = np.logspace(0, 6, 200)
    fig10b = go.Figure()
    for model in model_order:
        rows = primary[primary["Model"] == model]
        runs = []
        for _, row in rows.iterrows():
            condition = EvaluationCondition(
                dim=int(row["Dim"]),
                noise_std=float(row["Noise Std"]),
                problem_id=int(row["Problem ID"]),
            )
            runs.extend(inputs.dataset.get(condition, {}).get(row["Solver"], []))
        if not runs:
            continue
        curve, lower, upper = inputs.service.reliability_engine.compute_attainment_band(
            runs,
            eval_grid_reliability,
            inputs.config.reliability.primary_target,
            inputs.config.reliability.bootstrap_samples,
            inputs.config.reliability.bootstrap_seed,
        )
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
    primary_conditions = {
        (int(row["Dim"]), float(row["Noise Std"]), int(row["Problem ID"]))
        for _, row in primary.iterrows()
    }
    for baseline in baseline_solvers:
        label = baseline.value if hasattr(baseline, "value") else str(baseline)
        baseline_runs = []
        for dim, noise_std, problem_id in primary_conditions:
            baseline_runs.extend(
                inputs.dataset.get(
                    EvaluationCondition(dim=dim, noise_std=noise_std, problem_id=problem_id), {}
                ).get(baseline, [])
            )
        if not baseline_runs:
            continue
        curve, _, _ = inputs.service.reliability_engine.compute_attainment_band(
            baseline_runs,
            eval_grid_reliability,
            inputs.config.reliability.primary_target,
            inputs.config.reliability.bootstrap_samples,
            inputs.config.reliability.bootstrap_seed,
        )
        fig10b.add_trace(
            go.Scatter(
                x=eval_grid_reliability,
                y=curve,
                mode="lines",
                name=label,
                line=dict(color=baseline_styles.get(label, "#475569"), width=3.2, dash="solid"),
            )
        )
    fig10b.update_layout(
        template="plotly_white",
        title=dict(
            text='<b>Figure 10B: Clean Target Attainment During Search</b><br><span style="font-size:13px;color:#475569;font-weight:normal;">Best-queried clean-gap attainment (not returned-point reliability); LLMs dashed, classical baselines solid; shaded bands are 95% trial-bootstrap intervals</span>',
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


def _noise_summary(
    inputs: AnalysisInputs, primary: pd.DataFrame, noise_terminal: pd.DataFrame
) -> go.Figure:
    model_order = sorted(primary["Model"].unique())
    reliability_palette = ["#0284C7", "#7C3AED", "#0F766E", "#D97706", "#DB2777", "#475569"]
    model_colors = {
        model: reliability_palette[idx % len(reliability_palette)]
        for idx, model in enumerate(model_order)
    }
    noise_primary = (
        noise_terminal[
            (noise_terminal["Strategy"] == inputs.config.reliability.primary_prompt_strategy)
            & noise_terminal["Complete"]
        ]
        .rename(columns={"Successes": "Primary Successes"})
        .copy()
        if not noise_terminal.empty
        else primary.iloc[:0].copy()
    )
    noise_primary["Model"] = noise_primary["Model"].map(
        inputs.service.model_names.get_clean_model_label
    )
    dims = sorted(primary["Dim"].unique())
    fig10c = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[f"<b>{dim}D</b>" for dim in dims],
        horizontal_spacing=0.1,
        vertical_spacing=0.18,
    )
    for idx, dim in enumerate(dims):
        row, col = divmod(idx, 2)
        row += 1
        col += 1
        panel = (
            noise_primary[noise_primary["Dim"] == dim]
            .groupby(["Model", "Noise Std"], as_index=False)[["Primary Successes", "Trials"]]
            .sum()
        )
        panel["Rate"] = panel["Primary Successes"] / panel["Trials"]
        for model in model_order:
            series = panel[panel["Model"] == model].sort_values("Noise Std")
            fig10c.add_trace(
                go.Scatter(
                    x=series["Noise Std"],
                    y=series["Rate"],
                    mode="lines+markers",
                    name=model,
                    legendgroup=model,
                    showlegend=idx == 0,
                    line=dict(color=model_colors[model], width=2.6),
                    marker=dict(size=8),
                ),
                row=row,
                col=col,
            )
    for annotation in fig10c.layout.annotations:
        annotation.update(font=dict(size=16, color="#0F172A", family=FONT_FAMILY))
    fig10c.update_layout(
        template="plotly_white",
        title=dict(
            text='<b>Figure 10C: Noise Robustness of LLM-Evolved Optimizers</b><br><span style="font-size:13px;color:#475569;font-weight:normal;">Returned-point success for identical frozen clean champions across noise levels</span>',
            font=dict(size=20, color="#0F172A", family=FONT_FAMILY),
            x=0.02,
            y=0.97,
        ),
        width=1420,
        height=930,
        margin=dict(l=90, r=40, t=115, b=115),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=12, family=FONT_FAMILY),
        ),
    )
    fig10c.update_xaxes(
        title_text="<b>Noise standard deviation (sigma)</b>",
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        ticks="outside",
        tickfont=dict(size=12, family=FONT_FAMILY, color="#1E293B"),
    )
    fig10c.update_yaxes(
        range=[0, 1.05],
        title_text="<b>Success probability</b>",
        tickformat=".0%",
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        ticks="outside",
        tickfont=dict(size=12, family=FONT_FAMILY, color="#1E293B"),
    )
    return fig10c


def export_summary(inputs: AnalysisInputs, cache: FigureCache) -> pd.DataFrame:
    engine = TransferAnalysisEngine()
    config = inputs.config.reliability
    native = engine.condition_table(
        inputs.native_records,
        config.primary_target,
        config.secondary_target,
        inputs.config.target_eval_runs,
    ).rename(
        columns={
            "Target Problem": "Problem ID",
            "Successes": "Primary Successes",
            "Success Rate": "Primary Success Rate",
        }
    )
    noise = engine.condition_table(
        inputs.noise_records,
        config.primary_target,
        config.secondary_target,
        inputs.config.target_eval_runs,
    )
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    native.to_csv(REPORTS_DIR / "native_reliability_v1.csv", index=False)
    noise.to_csv(REPORTS_DIR / "noise_robustness_terminal_v1.csv", index=False)
    if native.empty:
        print("No current native terminal results; check readiness in notebook 03.")
        return native
    native["Model"] = native["Model"].map(inputs.service.model_names.get_clean_model_label)
    native["Solver"] = native["Solver"].map(inputs.service.model_names.resolve_folder_solver_name)
    primary = native[
        (native["Strategy"] == config.primary_prompt_strategy) & native["Complete"]
    ].copy()
    if primary.empty:
        print("Native conditions are incomplete; no aggregate thesis figures exported.")
        return native
    for filename, builder in [
        ("fig_10a_llm_reliability_matrix.png", _reliability_matrix),
        ("fig_10b_fixed_target_attainment.png", _attainment_profile),
        ("fig_10c_llm_noise_robustness.png", _noise_summary),
    ]:
        path = THESIS_SUMMARY_DIR / filename
        if cache.needs_export(path):
            cache.export(builder(inputs, primary, noise), path)
    print("Primary thesis figures are up to date (three PNGs, no inline rendering).")
    return native
