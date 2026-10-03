"""Reusable convergence/ECDF panels and separately runnable performance exports."""

from dataclasses import dataclass
from math import ceil
from typing import Literal

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmarking.application.analysis.results import (
    ConditionProfile,
    ProfileMode,
)
from benchmarking.domain.enums import BBOBFunction

from .style import (
    FONT_FAMILY,
    clean_solver_name,
    get_rgba_fill,
    get_solver_color,
    get_solver_line_style,
)


@dataclass(frozen=True)
class ProfileCurve:
    solver: str
    label: str
    color: str
    dash: str
    noise_std: float


def build_profile(
    profile: ConditionProfile,
    mode: ProfileMode,
    *,
    kind: Literal["convergence", "ecdf"],
    title: str,
) -> go.Figure:
    """Construct panels exclusively from precomputed scientific arrays."""
    problems = profile.problems
    curves = []
    prompt_colors = {
        "baseline": "#F59E0B",
        "guided": "#0284C7",
        "thinking": "#10B981",
        "vectorization": "#EF4444",
    }
    for solver in profile.solvers:
        label = clean_solver_name(solver)
        style = get_solver_line_style(solver)
        color, dash = get_solver_color(solver), str(style["dash"])
        if mode == "comparison":
            strategy = solver.split(" / ", 1)[1].split(" ", 1)[0]
            informed = "(noise-adapted)" in solver
            label = f"{strategy.title()} ({'noise-informed' if informed else 'noise-blind'})"
            color, dash = prompt_colors.get(strategy, "#64748B"), "solid" if informed else "dash"
        curves.append(ProfileCurve(solver, label, color, dash, profile.noise_std))
    by_condition = {(s.problem_id, s.solver): s for s in profile.series}
    titles = [
        f"<b>{BBOBFunction.get_name(p)}</b><br><sup>{BBOBFunction.get_class(p)}</sup>"
        for p in problems
    ]
    rows = ceil(len(titles) / 3)
    figure = make_subplots(
        rows=rows,
        cols=3,
        specs=[
            [{} if row * 3 + col < len(problems) else None for col in range(3)]
            for row in range(rows)
        ],
        subplot_titles=titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.22 if rows > 1 else 0.0,
    )
    grid = profile.evaluations
    for index, problem in enumerate(problems):
        row, col = divmod(index, 3)
        for curve in curves:
            series = by_condition.get((problem, curve.solver))
            if series is None:
                continue
            if kind == "convergence":
                data = {"median": series.median, "q25": series.q25, "q75": series.q75}
                if np.isnan(data["median"]).all():
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
                values = series.ecdf
                if np.isnan(values).all():
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
