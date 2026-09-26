"""Frozen-champion transfer rules and terminal-solution reliability statistics."""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from benchmarking.domain.services.reliability import ReliabilityEngine


class TransferAnalysisEngine:
    """Keep transfer results separate from native champion rankings."""

    @staticmethod
    def frozen_noise_records(
        records: Iterable[dict[str, object]],
    ) -> list[dict[str, object]]:
        """Only compare the same clean champion's code across noise levels."""
        records = list(records)
        clean_hashes = {
            (r.get("model"), r.get("strategy"), r["dim"], r["problem_id"]): r.get("code_hash")
            for r in records
            if float(r["noise_std"]) == 0.0
            and r.get("code_hash")
            and not str(r.get("solver_folder", "")).endswith(("_implicit", "_noisy"))
        }
        return [
            r
            for r in records
            if not str(r.get("solver_folder", "")).endswith(("_implicit", "_noisy"))
            and (
                "baseline" in r  # Classical reference across noise levels.
                or r.get("code_hash")
                == clean_hashes.get((r.get("model"), r.get("strategy"), r["dim"], r["problem_id"]))
                and bool(r.get("code_hash"))
            )
        ]

    @staticmethod
    def condition_table(
        records: Iterable[dict[str, object]],
        threshold: float = 1e-8,
        secondary_threshold: float = 1e-2,
        expected_trials: int = 20,
    ) -> pd.DataFrame:
        """Terminal returned-point success, not the best point queried during search."""
        rows: list[dict[str, object]] = []
        for record in records:
            errors = np.asarray(record.get("clean_errors", []), dtype=float)
            trials = len(errors)
            successes = int(np.count_nonzero(errors <= threshold))
            lower, upper = ReliabilityEngine.wilson_interval(successes, trials)
            rows.append(
                {
                    "Model": record.get("model", record.get("baseline", "")),
                    "Strategy": record.get("strategy", "classical"),
                    "Solver": record.get("solver_folder", ""),
                    "Source Problem": record.get("source_problem_id", record["problem_id"]),
                    "Target Problem": record["problem_id"],
                    "Dim": record["dim"],
                    "Noise Std": record["noise_std"],
                    "Code Hash": record.get("code_hash", ""),
                    "Trials": trials,
                    "Complete": trials >= expected_trials,
                    "Successes": successes,
                    "Success Rate": successes / trials if trials else float("nan"),
                    "Secondary Success Rate": float(np.mean(errors <= secondary_threshold))
                    if trials
                    else float("nan"),
                    "CI Lower": lower,
                    "CI Upper": upper,
                    "Median Terminal Error": float(np.median(errors)) if trials else float("nan"),
                }
            )
        return pd.DataFrame(
            rows,
            columns=[
                "Model",
                "Strategy",
                "Solver",
                "Source Problem",
                "Target Problem",
                "Dim",
                "Noise Std",
                "Code Hash",
                "Trials",
                "Complete",
                "Successes",
                "Success Rate",
                "Secondary Success Rate",
                "CI Lower",
                "CI Upper",
                "Median Terminal Error",
            ],
        )

    @staticmethod
    def aggregate_transfer(
        table: pd.DataFrame,
        bootstrap_samples: int = 1000,
        bootstrap_seed: int = 20260923,
    ) -> pd.DataFrame:
        """Equal-weight off-diagonal conditions; do not pool their individual trials."""
        columns = ["Model", "Conditions", "Success Rate", "CI Lower", "CI Upper"]
        if table.empty:
            return pd.DataFrame(columns=columns)
        subset = table[
            table["Complete"]
            & (table["Source Problem"] != table["Target Problem"])
            & (table["Strategy"] == "baseline")
        ]
        rows = []
        rng = np.random.default_rng(bootstrap_seed)
        for model, group in subset.groupby("Model", sort=True):
            rates = group["Success Rate"].to_numpy(dtype=float)
            samples = rng.choice(rates, (bootstrap_samples, len(rates))).mean(axis=1)
            rows.append(
                {
                    "Model": model,
                    "Conditions": len(rates),
                    "Success Rate": float(rates.mean()),
                    "CI Lower": float(np.quantile(samples, 0.025)),
                    "CI Upper": float(np.quantile(samples, 0.975)),
                }
            )
        return pd.DataFrame(rows, columns=columns)
