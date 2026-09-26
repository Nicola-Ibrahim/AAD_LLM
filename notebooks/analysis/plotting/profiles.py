"""Reusable convergence/ECDF panels and separately runnable performance exports."""

from dataclasses import dataclass
from math import ceil
from typing import Literal

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmarking.application.analysis.view_data import AnalysisInputs
from benchmarking.domain.enums import BBOBFunction
from benchmarking.domain.vos import EvaluationDataset
from .cache import FigureCache
from .style import (
    FONT_FAMILY,
    CLASSICAL_BASELINES,
    clean_solver_name,
    get_solver_color,
    get_solver_line_style,
    get_rgba_fill,
)
from shared.config import RESULTS_DIR


@dataclass(frozen=True)
class ProfileCurve:
    solver: str
    label: str
    color: str
    dash: str
    noise_std: float


def build_profile(
    inputs: AnalysisInputs,
    dataset: EvaluationDataset,
    curves: list[ProfileCurve],
    targets: dict[float, np.ndarray],
    *,
    dim: int,
    kind: Literal["convergence", "ecdf"],
    title: str,
) -> go.Figure:
    """Construct the same condition panels without duplicating two Plotly loops."""
    problems = inputs.dataset.problem_ids
    titles = [
        f"<b>{BBOBFunction.get_name(p)}</b><br><sup>{BBOBFunction.get_class(p)}</sup>"
        for p in problems
    ]
    titles.append("<b>Overall Aggregate Profile</b><br><sup>Mean across available functions</sup>")
    rows = ceil(len(titles) / 3)
    figure = make_subplots(
        rows=rows,
        cols=3,
        subplot_titles=titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.22 if rows > 1 else 0.0,
    )
    grid = np.logspace(0, 6, 300)
    engine = inputs.service.ecdf_engine
    for index, problem in enumerate(problems + [0]):
        row, col = divmod(index, 3)
        for curve in curves:
            query = dict(dim=dim, noise_std=curve.noise_std, solver=curve.solver, eval_grid=grid)
            if kind == "convergence":
                data = (
                    engine.get_convergence_trajectory(dataset, problem_id=problem, **query)
                    if problem
                    else engine.get_aggregate_convergence(dataset, **query)
                )
                if data is None or np.isnan(data["median"]).all():
                    continue
                values = np.maximum(data["median"], 1e-12)
                for bound, fill in [("q75", False), ("q25", True)]:
                    figure.add_trace(
                        go.Scatter(
                            x=grid,
                            y=np.maximum(data[bound], 1e-12),
                            mode="lines",
                            line=dict(width=0),
                            fill="tonexty" if fill else "none",
                            fillcolor=get_rgba_fill(curve.color, 0.12),
                            showlegend=False,
                            hoverinfo="skip",
                        ),
                        row=row + 1,
                        col=col + 1,
                    )
            else:
                values = (
                    engine.get_target_ecdf_curve(
                        dataset, targets[curve.noise_std], problem_id=problem, **query
                    )
                    if problem
                    else engine.get_aggregate_target_ecdf_curve(
                        dataset, targets[curve.noise_std], **query
                    )
                )
                if values is None or np.isnan(values).all():
                    continue
            figure.add_trace(
                go.Scatter(
                    x=grid,
                    y=values,
                    mode="lines",
                    name=curve.label,
                    legendgroup=curve.label,
                    line=dict(color=curve.color, dash=curve.dash, width=2.2),
                    showlegend=index == 0,
                ),
                row=row + 1,
                col=col + 1,
            )
    figure.update_xaxes(
        type="log",
        range=[0, 6],
        title_text="<b>Evaluations</b>",
        tickvals=[1, 10, 100, 1000, 10000, 100000, 1000000],
        ticktext=["1", "10", "100", "1k", "10k", "100k", "1M"],
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        ticks="outside",
    )
    if kind == "convergence":
        figure.update_yaxes(
            type="log",
            title_text="<b>Median best-queried clean gap Δf</b>",
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
        )
    else:
        figure.update_yaxes(
            range=[0, 1.05],
            title_text="<b>Target attainment probability</b>",
            tickformat=".0%",
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
        )
    for annotation in figure.layout.annotations:
        annotation.update(font=dict(size=14, color="#0F172A", family=FONT_FAMILY))
    figure.update_layout(
        template="plotly_white",
        font=dict(family=FONT_FAMILY),
        title=dict(
            text=title, font=dict(size=18, color="#0F172A", family=FONT_FAMILY), x=0.02, y=0.97
        ),
        width=1340,
        height=max(860, rows * 420),
        margin=dict(l=70, r=40, t=110, b=120),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.14,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=12, family=FONT_FAMILY),
        ),
    )
    return figure


def export_performance_profiles(
    inputs: AnalysisInputs,
    targets: dict[float, np.ndarray],
    cache: FigureCache,
    *,
    mode: Literal["explicit", "implicit", "comparison"],
) -> None:
    """Run one profile family; skip each figure before constructing it."""
    directories = {
        "explicit": "02_explicit",
        "implicit": "03_implicit",
        "comparison": "04_implicit_vs_explicit",
    }
    prompt_colors = {
        "baseline": "#F59E0B",
        "guided": "#0284C7",
        "thinking": "#10B981",
        "vectorization": "#EF4444",
    }
    for dim in inputs.dataset.dims:
        for model, solvers in inputs.models_to_solvers.items():
            for noise in inputs.dataset.noise_stds:
                implicit = [s for s in solvers if "(noise-implicit)" in s]
                adapted = [s for s in solvers if "(noise-adapted)" in s]
                clean = [
                    s for s in solvers if "(noise-implicit)" not in s and "(noise-adapted)" not in s
                ]
                if mode == "explicit":
                    selected = clean if noise == 0.0 else (adapted or clean)
                elif mode == "implicit":
                    if noise == 0.0 or not implicit:
                        continue
                    selected = implicit
                else:
                    if noise == 0.0 or not implicit or not adapted:
                        continue
                    selected = adapted + implicit
                curves = []
                for solver in selected + ([] if mode == "comparison" else CLASSICAL_BASELINES):
                    label = clean_solver_name(solver)
                    style = get_solver_line_style(solver)
                    color, dash = get_solver_color(solver), str(style["dash"])
                    if mode == "comparison":
                        strategy = solver.split(" / ", 1)[1].split(" ", 1)[0]
                        informed = "(noise-adapted)" in solver
                        label = f"{strategy.title()} ({'noise-informed' if informed else 'noise-blind'})"
                        color, dash = (
                            prompt_colors.get(strategy, "#64748B"),
                            "solid" if informed else "dash",
                        )
                    curves.append(ProfileCurve(solver, label, color, dash, noise))
                output = (
                    RESULTS_DIR
                    / "figures"
                    / directories[mode]
                    / inputs.model_slugs[model]
                    / f"{dim}D"
                    / f"std_{noise}"
                )
                for kind, filename in [
                    (
                        "convergence",
                        "implicit_vs_noisy_convergence.png"
                        if mode == "comparison"
                        else "convergence_trajectories.png",
                    ),
                    ("ecdf", "target_precision_ecdf.png"),
                ]:
                    target = output / filename
                    if cache.needs_export(target):
                        figure = build_profile(
                            inputs,
                            inputs.dataset,
                            curves,
                            targets,
                            dim=dim,
                            kind=kind,
                            title=f"<b>{mode.title()} {kind.upper()} — {model} ({dim}D, σ={noise:g})</b><br><sup>Adaptive-target ECDFs are exploratory; fixed-target reliability is reported separately.</sup>",
                        )
                        cache.export(figure, target)
