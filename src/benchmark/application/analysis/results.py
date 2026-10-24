"""Calculated scientific results. Arrays and tables must be treated as read-only."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

ProfileMode = Literal["explicit", "implicit", "comparison"]


@dataclass(frozen=True)
class AnalysisProvenance:
    settings: dict[str, object]
    filters: dict[str, object]
    model_slugs: dict[str, str]
    records: list[dict[str, object]]
    trace_signature: str


@dataclass(frozen=True)
class ProfileSeries:
    solver: str
    problem_id: int
    median: np.ndarray
    q25: np.ndarray
    q75: np.ndarray
    ecdf: np.ndarray
    trace_count: int


@dataclass(frozen=True)
class ConditionProfile:
    model: str
    model_slug: str
    dim: int
    noise_std: float
    problems: list[int]
    solvers: list[str]
    evaluations: np.ndarray
    targets: np.ndarray
    series: list[ProfileSeries]


@dataclass(frozen=True)
class ProfileAnalysisResult:
    mode: ProfileMode
    conditions: list[ConditionProfile]
    provenance: AnalysisProvenance
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class AttainmentSeries:
    solver: str
    baseline: bool
    probability: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    trace_count: int


@dataclass(frozen=True)
class ReliabilityAnalysisResult:
    native: pd.DataFrame
    noise_terminal: pd.DataFrame
    primary: pd.DataFrame
    evaluations: np.ndarray
    attainment: list[AttainmentSeries]
    model_order: list[str]
    provenance: AnalysisProvenance
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class NoiseRobustnessResult:
    conditions: pd.DataFrame
    aggregate: pd.DataFrame
    model_labels: dict[str, str]
    primary_target: float
    provenance: AnalysisProvenance
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class HardnessSummary:
    model: str
    dim: int
    solvers: list[str]
    tables: dict[float, pd.DataFrame]


@dataclass(frozen=True)
class PerformanceAnalysisResult:
    targets: dict[float, np.ndarray]
    table: pd.DataFrame
    rankings: pd.Series
    model_scale: pd.DataFrame
    hardness: list[HardnessSummary]
    models_to_solvers: dict[str, list[str]]
    model_slugs: dict[str, str]
    classical_solvers: list[str]
    dims: list[int]
    clean_std: float
    noisy_std: float
    provenance: AnalysisProvenance
    diagnostics: tuple[str, ...]
