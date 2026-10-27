"""Reliability metrics for repeatedly evaluated LLM-evolved optimizers."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from benchmark.domain.vos import RunTrace


class ReliabilityEngine:
    """Compute fixed-target reliability metrics without conflating missing data and failure."""

    @staticmethod
    def wilson_interval(
        successes: int, trials: int, confidence: float = 0.95
    ) -> tuple[float, float]:
        """Return a Wilson binomial confidence interval without a SciPy dependency."""
        if trials <= 0:
            return float("nan"), float("nan")
        # z for the only supported/reporting confidence level (95%).
        if not np.isclose(confidence, 0.95):
            raise ValueError("ReliabilityEngine currently supports confidence=0.95 only.")
        z = 1.959963984540054
        p = successes / trials
        denom = 1.0 + z * z / trials
        centre = (p + z * z / (2.0 * trials)) / denom
        half = z * np.sqrt((p * (1.0 - p) + z * z / (4.0 * trials)) / trials) / denom
        return max(0.0, float(centre - half)), min(1.0, float(centre + half))

    @staticmethod
    def evaluations_to_target(run: RunTrace, threshold: float) -> float:
        """First evaluation reaching ``threshold``; NaN represents right-censoring."""
        if not len(run.evaluations):
            return float("nan")
        hits = np.flatnonzero(np.minimum.accumulate(run.raw_objectives) <= threshold)
        return float(run.evaluations[hits[0]]) if len(hits) else float("nan")

    def compute_aggregate_reliability(
        self,
        reliability_table: pd.DataFrame,
        primary_strategy: str = "baseline",
        bootstrap_samples: int = 1000,
        bootstrap_seed: int = 20260923,
    ) -> pd.DataFrame:
        """Aggregate complete condition rates with a deterministic condition bootstrap."""
        if reliability_table.empty:
            return pd.DataFrame()
        rows: list[dict[str, object]] = []
        subset = reliability_table[
            (reliability_table["Strategy"] == primary_strategy) & reliability_table["Complete"]
        ]
        rng = np.random.default_rng(bootstrap_seed)
        for model, group in subset.groupby("Model", sort=True):
            rates = group["Primary Success Rate"].to_numpy(dtype=float)
            if not len(rates):
                continue
            samples = np.mean(
                rng.choice(rates, size=(bootstrap_samples, len(rates)), replace=True), axis=1
            )
            rows.append(
                {
                    "Model": model,
                    "Conditions": len(group),
                    "Trials": int(group["Trials"].sum()),
                    "Primary Success Rate": float(np.mean(rates)),
                    "Bootstrap CI Lower": float(np.quantile(samples, 0.025)),
                    "Bootstrap CI Upper": float(np.quantile(samples, 0.975)),
                }
            )
        return (
            pd.DataFrame(rows).sort_values("Primary Success Rate", ascending=False)
            if rows
            else pd.DataFrame()
        )

    def compute_attainment_band(
        self,
        runs: Iterable[RunTrace],
        eval_grid: np.ndarray,
        threshold: float = 1e-8,
        bootstrap_samples: int = 1000,
        bootstrap_seed: int = 20260923,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Fixed-target attainment curve and trial-bootstrap 95% confidence band."""
        traces = list(runs)
        if not traces:
            missing = np.full(len(eval_grid), np.nan)
            return missing, missing.copy(), missing.copy()
        matrix = []
        for run in traces:
            hit = self.evaluations_to_target(run, threshold)
            matrix.append(
                eval_grid >= hit if np.isfinite(hit) else np.zeros(len(eval_grid), dtype=bool)
            )
        values = np.asarray(matrix, dtype=float)
        curve = values.mean(axis=0)
        rng = np.random.default_rng(bootstrap_seed)
        indices = rng.integers(0, len(values), size=(bootstrap_samples, len(values)))
        resampled = values[indices].mean(axis=1)
        return curve, np.quantile(resampled, 0.025, axis=0), np.quantile(resampled, 0.975, axis=0)


def search_success_rate(runs: Iterable[RunTrace], threshold: float = 1e-8) -> float:
    """Fraction of recorded search trials attaining the target; NaN means no trials."""
    traces = list(runs)
    return (
        sum(run.is_success(threshold) for run in traces) / len(traces) if traces else float("nan")
    )
