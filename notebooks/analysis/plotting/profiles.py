"""Convergence/ECDF panels built solely from precomputed profile arrays."""

from collections.abc import Iterator
from dataclasses import dataclass
from math import ceil
from typing import Literal

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmark.application.analysis.results import (
    ConditionProfile,
    ProfileMode,
    ProfileSeries,
)
from benchmark.domain.enums import BBOBFunction

from .style import (
    FONT_FAMILY,
    STRATEGY_COLORS,
    clean_solver_name,
    get_rgba_fill,
    get_solver_line_style,
)


@dataclass(frozen=True)
class ProfileCurve:
    solver: str
    label: str
    color: str
    dash: str


def build_profile(
    profile: ConditionProfile,
    mode: ProfileMode,
    *,
    kind: Literal["convergence", "ecdf"],
    title: str,
) -> go.Figure:
    """Construct panels exclusively from precomputed scientific arrays."""
    problems = profile.problems
    if not problems:
        raise ValueError("A profile figure requires at least one problem.")
    curves = _profile_curves(profile.solvers, mode)
    by_condition = {(s.problem_id, s.solver): s for s in profile.series}
    titles = [
        f"<b>{BBOBFunction.get_name(p)}</b><br><sup>{BBOBFunction.get_class(p)}</sup>"
        for p in problems
    ]
    columns = min(3, len(problems))
    rows = ceil(len(titles) / columns)
    figure = make_subplots(
        rows=rows,
        cols=columns,
        specs=[
            [{} if row * columns + col < len(problems) else None for col in range(columns)]
            for row in range(rows)
        ],
        subplot_titles=titles,
        horizontal_spacing=0.08,
        vertical_spacing=0.22 if rows > 1 else 0.0,
    )
    grid = profile.evaluations
    max_evaluations = float(grid[-1])
    ticks = [10**power for power in range(int(np.floor(np.log10(max_evaluations))) + 1)]
    if ticks[-1] != max_evaluations:
        ticks.append(max_evaluations)
    tick_labels = [
        f"{tick / 1_000_000:g}M"
        if tick >= 1_000_000
        else f"{tick / 1000:g}k"
        if tick >= 1000
        else f"{tick:g}"
        for tick in ticks
    ]
    for index, problem in enumerate(problems):
        row, col = divmod(index, columns)
        for curve in curves:
            series = by_condition.get((problem, curve.solver))
            if series is None:
                continue
            for trace in _series_traces(
                series, curve, grid, kind, showlegend=index == 0 and mode != "comparison"
            ):
                figure.add_trace(trace, row=row + 1, col=col + 1)
    figure.update_xaxes(
        type="log",
        range=[float(np.log10(grid[0])), float(np.log10(max_evaluations))],
        title_text="<b>Objective evaluations</b>",
        tickvals=ticks,
        ticktext=tick_labels,
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        ticks="outside",
    )
    if kind == "convergence":
        figure.update_yaxes(
            type="log",
            dtick=1,
            exponentformat="power",
            showexponent="all",
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
        height=680 if rows == 1 else max(860, rows * 420),
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
    if mode == "comparison":
        _add_comparison_legend(figure, curves)
    return figure


def _profile_curves(solvers: list[str], mode: ProfileMode) -> list[ProfileCurve]:
    curves: list[ProfileCurve] = []
    for solver in solvers:
        label = clean_solver_name(solver)
        style = get_solver_line_style(solver)
        color, dash = str(style["color"]), str(style["dash"])
        if mode == "comparison":
            strategy = solver.split(" / ", 1)[1].split(" ", 1)[0]
            informed = "(noise-adapted)" in solver
            label = f"{strategy.title()} ({'noise-informed' if informed else 'noise-blind'})"
            color, dash = STRATEGY_COLORS.get(strategy, "#64748B"), "solid" if informed else "dash"
        curves.append(ProfileCurve(solver, label, color, dash))
    return curves


def _series_traces(
    series: ProfileSeries,
    curve: ProfileCurve,
    grid: np.ndarray,
    kind: Literal["convergence", "ecdf"],
    *,
    showlegend: bool,
) -> Iterator[go.Scatter]:
    values = series.median if kind == "convergence" else series.ecdf
    if np.isnan(values).all():
        return
    if kind == "convergence":
        values = np.maximum(values, 1e-12)
        for bound, fill in [(series.q75, "none"), (series.q25, "tonexty")]:
            yield go.Scatter(
                x=grid,
                y=np.maximum(bound, 1e-12),
                mode="lines",
                line=dict(width=0),
                fill=fill,
                fillcolor=get_rgba_fill(curve.color, 0.12),
                showlegend=False,
                hoverinfo="skip",
            )
    yield go.Scatter(
        x=grid,
        y=values,
        mode="lines",
        name=curve.label,
        legendgroup=curve.label,
        line=dict(color=curve.color, dash=curve.dash, width=2.2),
        showlegend=showlegend,
    )


def _add_comparison_legend(figure: go.Figure, curves: list[ProfileCurve]) -> None:
    # Independent visual keys: color identifies strategy, dash identifies mode.
    # Keep the full series labels for hover, without repeating them in the legend.
    active_colors = {curve.color for curve in curves}
    for strategy, color in STRATEGY_COLORS.items():
        if color not in active_colors:
            continue
        figure.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(color=color, size=11, symbol="square"),
                name="Baseline prompt" if strategy == "baseline" else strategy.title(),
                showlegend=True,
                hoverinfo="skip",
            )
        )
    for label, dash in [
        ("Explicit (noise-informed)", "solid"),
        ("Implicit (noise-blind)", "dash"),
    ]:
        figure.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color="#475569", dash=dash, width=2.2),
                name=label,
                legend="legend2",
                showlegend=True,
                hoverinfo="skip",
            )
        )
    figure.update_layout(
        height=figure.layout.height + 120,
        margin=dict(b=270),
        legend=dict(
            title=dict(text="Prompt strategy", side="top"),
            x=0.5,
            xanchor="center",
            y=-0.13,
            yanchor="top",
        ),
        legend2=dict(
            title=dict(text="Synthesis mode", side="top"),
            orientation="h",
            yanchor="top",
            y=-0.27,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#E2E8F0",
            borderwidth=1,
            font=dict(size=12, family=FONT_FAMILY),
        ),
    )
    figure.add_annotation(
        x=0,
        y=-0.41,
        xref="paper",
        yref="paper",
        xanchor="left",
        yanchor="top",
        showarrow=False,
        text="Both modes are evaluated under noise; noise-blind refers to the prompt, not the objective.",
        font=dict(size=12, color="#475569", family=FONT_FAMILY),
    )
