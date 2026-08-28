"""Synthesis Configuration Read Repository (Pure I/O & TOML Parsing).

Encapsulates reading, parsing, and resolving synthesis.toml / experiments.toml
for evolutionary synthesis search spaces and execution parameters.
"""

import os
from pathlib import Path
from typing import Any
import tomllib

from shared.config import CONFIGS_DIR


class SynthesisConfigRepository:
    """Infrastructure repository for reading and parsing synthesis.toml."""

    def __init__(
        self,
        config_path: Path = CONFIGS_DIR / "synthesis.toml",
    ):
        self.config_path = config_path

    def load_config(self) -> dict[str, Any]:
        """Loads and parses the synthesis configuration."""
        cfg: dict[str, Any] = {}
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                cfg = tomllib.load(f)

        matrix_cfg = cfg.get("matrix", {})
        evolution_cfg = cfg.get("evolution", {})
        exec_meta = cfg.get("execution", {})

        return {
            "matrix": matrix_cfg,
            "evolution": evolution_cfg,
            "execution": exec_meta,
            "name": evolution_cfg.get("name", "bbob_comprehensive_matrix"),
            "noise_model": matrix_cfg.get("noise_model", "heteroscedastic"),
            "problem_ids": [int(p) for p in matrix_cfg.get("problem_ids", [1, 8, 11, 15, 21])],
            "dimensions": [int(d) for d in matrix_cfg.get("dimensions", [2, 3, 5])],
            "noise_stds": [float(s) for s in matrix_cfg.get("noise_stds", [0.0, 0.05])],
            "prompt_strategies": matrix_cfg.get(
                "prompt_strategies", ["baseline", "thinking", "vectorization", "guided"]
            ),
            "budget": int(evolution_cfg.get("budget", 1000000)),
            "iterations": int(evolution_cfg.get("iterations", 10)),
            "runs_per_config": int(evolution_cfg.get("runs_per_config", 1)),
            "num_processes": int(exec_meta.get("max_workers", 0)) or os.cpu_count() or 8,
            "auto_resume": bool(exec_meta.get("auto_resume", True)),
            "skip_completed": bool(exec_meta.get("skip_completed", True)),
            "retry_failed_synthesis": bool(exec_meta.get("retry_failed_synthesis", True)),
            "only_incomplete": bool(exec_meta.get("only_incomplete", False)),
            "target_exp_ids": exec_meta.get("target_experiment_ids") or None,
        }

