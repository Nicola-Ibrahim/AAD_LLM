"""Reliability metrics for repeatedly evaluated LLM-evolved optimizers."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from benchmarking.domain.vos import EvaluationDataset, RunTrace


class ReliabilityEngine:
    """Compute fixed-target reliability metrics without conflating missing data and failure."""

    @staticmethod
    def split_solver_name(solver: str) -> tuple[str, str] | None:
        """Return canonical ``(model, strategy)`` for an LLM solver label.

        Classical baseline labels deliberately return ``None`` so they cannot enter
        LLM reliability rankings.
        """
        if " / " not in solver:
            return None
        model, strategy = solver.rsplit(" / ", 1)
        return model.strip(), strategy.split(" ", 1)[0].strip().lower()

    @classmethod
    def discover_models(cls, benchmark_data: EvaluationDataset) -> list[str]:
        """Discover LLM labels from loaded traces, including future models automatically."""
        return sorted({parsed[0] for s in benchmark_data.solvers if (parsed := cls.split_solver_name(s))})

    @staticmethod
    def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
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

    def compute_reliability_table(
        self,
        benchmark_data: EvaluationDataset,
        primary_threshold: float = 1e-8,
        secondary_threshold: float = 1e-2,
        expected_trials: int = 20,
    ) -> pd.DataFrame:
        """Return condition-level reliability rows for every discovered LLM strategy."""
        rows: list[dict[str, object]] = []
        for condition, solvers in benchmark_data.items():
            for solver, runs in solvers.items():
                parsed = self.split_solver_name(str(solver))
                if parsed is None:
                    continue
                model, strategy = parsed
                valid_runs = [r for r in runs if len(r.raw_objectives)]
                n_trials = len(valid_runs)
                primary_hits = sum(r.is_success(primary_threshold) for r in valid_runs)
                secondary_hits = sum(r.is_success(secondary_threshold) for r in valid_runs)
                lower, upper = self.wilson_interval(primary_hits, n_trials)
                terminal = [r.best_value for r in valid_runs if np.isfinite(r.best_value)]
                hit_times = [self.evaluations_to_target(r, primary_threshold) for r in valid_runs]
                hit_times = [v for v in hit_times if np.isfinite(v)]
                rows.append({
                    "Model": model,
                    "Strategy": strategy,
                    "Solver": str(solver),
                    "Dim": condition.dim,
                    "Noise Std": condition.noise_std,
                    "Problem ID": condition.problem_id,
                    "Trials": n_trials,
                    "Expected Trials": expected_trials,
                    "Complete": n_trials >= expected_trials,
                    "Primary Successes": primary_hits,
                    "Primary Success Rate": primary_hits / n_trials if n_trials else float("nan"),
                    "Primary CI Lower": lower,
                    "Primary CI Upper": upper,
                    "Secondary Successes": secondary_hits,
                    "Secondary Success Rate": secondary_hits / n_trials if n_trials else float("nan"),
                    "Median Best Error": float(np.median(terminal)) if terminal else float("nan"),
                    "Median Evals to Primary Target": float(np.median(hit_times)) if hit_times else float("nan"),
                })
        return pd.DataFrame(rows)

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
            (reliability_table["Strategy"] == primary_strategy)
            & reliability_table["Complete"]
        ]
        rng = np.random.default_rng(bootstrap_seed)
        for model, group in subset.groupby("Model", sort=True):
            rates = group["Primary Success Rate"].to_numpy(dtype=float)
            if not len(rates):
                continue
            samples = np.mean(rng.choice(rates, size=(bootstrap_samples, len(rates)), replace=True), axis=1)
            rows.append({
                "Model": model,
                "Conditions": len(group),
                "Trials": int(group["Trials"].sum()),
                "Primary Success Rate": float(np.mean(rates)),
                "Bootstrap CI Lower": float(np.quantile(samples, 0.025)),
                "Bootstrap CI Upper": float(np.quantile(samples, 0.975)),
            })
        return pd.DataFrame(rows).sort_values("Primary Success Rate", ascending=False) if rows else pd.DataFrame()

    def compute_attainment_band(
        self,
        runs: Iterable[RunTrace],
        eval_grid: np.ndarray,
        threshold: float = 1e-8,
        bootstrap_samples: int = 1000,
        bootstrap_seed: int = 20260923,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Fixed-target attainment curve and trial-bootstrap 95% confidence band."""
        traces = [r for r in runs if len(r.raw_objectives)]
        if not traces:
            zeros = np.zeros(len(eval_grid))
            return zeros, zeros, zeros
        matrix = []
        for run in traces:
            best = np.minimum.accumulate(run.raw_objectives)
            interpolated = np.interp(eval_grid, run.evaluations, best, left=best[0], right=best[-1])
            matrix.append(interpolated <= threshold)
        values = np.asarray(matrix, dtype=float)
        curve = values.mean(axis=0)
        rng = np.random.default_rng(bootstrap_seed)
        indices = rng.integers(0, len(values), size=(bootstrap_samples, len(values)))
        resampled = values[indices].mean(axis=1)
        return curve, np.quantile(resampled, 0.025, axis=0), np.quantile(resampled, 0.975, axis=0)

    def compute_checkpoint_table(
        self,
        benchmark_data: EvaluationDataset,
        checkpoint_fractions: list[float],
        budget_multiplier: int,
        threshold: float = 1e-8,
        primary_strategy: str = "baseline",
    ) -> pd.DataFrame:
        """Compute condition-level target attainment at fixed fractions of each evaluation budget."""
        rows: list[dict[str, object]] = []
        for condition, solvers in benchmark_data.items():
            budget = condition.dim * budget_multiplier
            for solver, runs in solvers.items():
                parsed = self.split_solver_name(str(solver))
                if parsed is None or parsed[1] != primary_strategy:
                    continue
                for fraction in checkpoint_fractions:
                    checkpoint = max(1, int(budget * fraction))
                    outcomes = []
                    for run in runs:
                        if not len(run.evaluations):
                            continue
                        idx = np.searchsorted(run.evaluations, checkpoint, side="right") - 1
                        if idx < 0:
                            continue
                        outcomes.append(float(np.min(run.raw_objectives[: idx + 1]) <= threshold))
                    if outcomes:
                        rows.append({
                            "Model": parsed[0], "Strategy": parsed[1], "Solver": str(solver),
                            "Dim": condition.dim, "Noise Std": condition.noise_std, "Problem ID": condition.problem_id,
                            "Checkpoint Fraction": fraction, "Checkpoint Evaluations": checkpoint,
                            "Attainment Rate": float(np.mean(outcomes)), "Trials": len(outcomes),
                        })
        return pd.DataFrame(rows)
