"""Benchmark Configuration Read Repository (Pure I/O & TOML Parsing).

Encapsulates reading, parsing, and resolving configs/benchmark.toml and configs/baselines.toml
for multi-trial benchmark evaluations and classical baselines.
"""

from pathlib import Path
from typing import Any
import tomllib

from shared.config import CONFIGS_DIR


class EvaluationConfigRepository:
    """Infrastructure repository for reading and parsing benchmark.toml and baselines.toml."""

    def __init__(
        self,
        config_path: Path = CONFIGS_DIR / "benchmark.toml",
        baselines_path: Path = CONFIGS_DIR / "baselines.toml",
    ):
        self.config_path = config_path
        self.baselines_path = baselines_path

    def load_baselines(self) -> dict[str, dict[str, Any]]:
        """Loads baseline optimizer metadata and display labels from baselines.toml."""
        if not self.baselines_path.exists():
            return {
                "cmaes": {"slug": "cmaes", "display_name": "CMA-ES"},
                "de": {"slug": "de", "display_name": "Differential Evolution"},
                "pso": {"slug": "pso", "display_name": "Particle Swarm Optimization"},
            }
        with open(self.baselines_path, "rb") as f:
            return tomllib.load(f).get("baselines", {})

    def load_config(self) -> dict[str, Any]:
        """Loads and parses the benchmark.toml configuration."""
        cfg: dict[str, Any] = {}
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                cfg = tomllib.load(f)

        bench_cfg = cfg.get("benchmarking") or cfg.get("evaluation") or {}
        baselines_data = self.load_baselines()
        baseline_labels = {
            slug: info.get("display_name", slug.upper())
            for slug, info in baselines_data.items()
        }

        return {
            "benchmarking": bench_cfg,
            "target_eval_runs": int(bench_cfg.get("target_eval_runs", 10)),
            "budget_multiplier": int(bench_cfg.get("budget_multiplier", 10000)),
            "eval_timeout_seconds": float(bench_cfg.get("eval_timeout_seconds", 300.0)),
            "fill_missing_only": bool(bench_cfg.get("fill_missing_only", True)),
            "classical_baselines": bench_cfg.get(
                "classical_baselines", ["cmaes", "de", "pso"]
            ),
            "target_problems": bench_cfg.get("target_problems", [1, 8, 11, 15, 21]),
            "target_dims": bench_cfg.get("target_dims", [2, 3, 5]),
            "target_noise_levels": bench_cfg.get("target_noise_levels", [0.0, 0.05]),
            "target_models": bench_cfg.get("target_models", []),
            "target_prompt_strategies": bench_cfg.get("target_prompt_strategies", []),
            "baseline_labels": baseline_labels,
        }
