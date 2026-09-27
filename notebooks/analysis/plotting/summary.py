"""Fixed-target attainment figure and reproducible terminal reliability CSVs."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from benchmarking.application.analysis.view_data import AnalysisInputs
from benchmarking.domain.services.reliability import ReliabilityEngine
from benchmarking.domain.services.transfer import TransferAnalysisEngine
from benchmarking.domain.vos import EvaluationCondition
from shared.config import RESULTS_DIR

from .cache import FigureCache
from .style import FONT_FAMILY

REPORTS_DIR = RESULTS_DIR / "reports"
THESIS_SUMMARY_DIR = RESULTS_DIR / "figures" / "06_thesis_summary"


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
    max_budget = int(primary["Dim"].max()) * inputs.config.budget_multiplier
    eval_grid_reliability = np.logspace(0, np.log10(max_budget), 200)
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
        curve, lower, upper = ReliabilityEngine().compute_attainment_band(
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
        curve, _, _ = ReliabilityEngine().compute_attainment_band(
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
    native["Model"] = native["Model"].map(inputs.model_names.get_clean_model_label)
    native["Solver"] = native["Solver"].map(inputs.model_names.resolve_folder_solver_name)
    primary = native[
        (native["Strategy"] == config.primary_prompt_strategy) & native["Complete"]
    ].copy()
    if primary.empty:
        print("Native conditions are incomplete; no aggregate thesis figures exported.")
        return native
    for filename, builder in [
        ("fig_10b_fixed_target_attainment.png", _attainment_profile),
    ]:
        path = THESIS_SUMMARY_DIR / filename
        if cache.needs_export(path):
            cache.export(builder(inputs, primary, noise), path)
    print("Fixed-target attainment PNG and reliability CSVs are up to date.")
    return native
