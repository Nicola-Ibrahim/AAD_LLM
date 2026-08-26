"""Benchmark Configuration Read Repository (Pure I/O & TOML Parsing).

Encapsulates reading, parsing, and resolving configs/benchmark.toml
for multi-trial benchmark evaluations and classical baselines.
"""

from pathlib import Path
from typing import Any
import tomllib

from shared.config import CONFIGS_DIR


class BenchmarkConfigRepository:
    """Infrastructure repository for reading and parsing benchmark.toml."""

    def __init__(
        self,
        config_path: Path = CONFIGS_DIR / "benchmark.toml",
    ):
        self.config_path = config_path

    def load_config(self) -> dict[str, Any]:
        """Loads and parses the benchmark.toml configuration."""
        cfg: dict[str, Any] = {}
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                cfg = tomllib.load(f)

        eval_cfg = cfg.get("evaluation", {})

        return {
            "evaluation": eval_cfg,
            "target_eval_runs": int(eval_cfg.get("target_eval_runs", 10)),
            "eval_timeout_seconds": float(eval_cfg.get("eval_timeout_seconds", 30.0)),
            "fill_missing_only": bool(eval_cfg.get("fill_missing_only", True)),
            "classical_baselines": eval_cfg.get(
                "classical_baselines", ["CMA-ES", "DE", "PSO"]
            ),
        }
