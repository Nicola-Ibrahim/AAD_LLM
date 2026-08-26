"""Experiment Configuration Read Repository (Pure I/O & TOML Parsing).

Encapsulates reading, parsing, and resolving TOML configuration files
for evolutionary synthesis search spaces and execution parameters.
"""

import os
from pathlib import Path
from typing import Any
import tomllib

from shared.config import CONFIGS_DIR


class ExperimentConfigRepository:
    """Infrastructure repository for reading and parsing experiments.toml and runner.toml."""

    def __init__(
        self,
        exp_config_path: Path = CONFIGS_DIR / "experiments.toml",
        runner_config_path: Path = CONFIGS_DIR / "runner.toml",
    ):
        self.exp_config_path = exp_config_path
        self.runner_config_path = runner_config_path

    def load_config(self) -> dict[str, Any]:
        """Loads and merges experiments.toml (search space) and runner.toml (execution metadata)."""
        exp_cfg: dict[str, Any] = {}
        if self.exp_config_path.exists():
            with open(self.exp_config_path, "rb") as f:
                exp_cfg = tomllib.load(f)

        runner_cfg: dict[str, Any] = {}
        if self.runner_config_path.exists():
            with open(self.runner_config_path, "rb") as f:
                runner_cfg = tomllib.load(f)

        matrix_cfg = exp_cfg.get("matrix", exp_cfg.get("search_space", {}))
        evolution_cfg = exp_cfg.get("evolution", exp_cfg.get("experiment", {}))
        exec_meta = runner_cfg.get("execution", exp_cfg.get("execution", {}))

        return {
            "matrix": matrix_cfg,
            "evolution": evolution_cfg,
            "execution": exec_meta,
            "name": evolution_cfg.get("name", "bbob_comprehensive_matrix"),
            "noise_model": matrix_cfg.get("noise_model", "heteroscedastic"),
            "budget": int(evolution_cfg.get("budget", 1000000)),
            "iterations": int(evolution_cfg.get("iterations", 10)),
            "runs_per_config": int(evolution_cfg.get("runs_per_config", 1)),
            "num_processes": int(exec_meta.get("max_workers", 0)) or os.cpu_count() or 8,
            "auto_resume": bool(exec_meta.get("auto_resume", True)),
            "skip_completed": bool(exec_meta.get("skip_completed", True)),
            "retry_failed_synthesis": bool(exec_meta.get("retry_failed_synthesis", True)),
            "only_incomplete": bool(exec_meta.get("only_incomplete", False)),
            "filter_problems": exec_meta.get("filter_problem_ids") or None,
            "filter_dims": exec_meta.get("filter_dimensions") or None,
            "filter_modes": exec_meta.get("filter_modes") or None,
            "filter_strategies": exec_meta.get("filter_prompt_strategies") or None,
            "target_exp_ids": exec_meta.get("target_experiment_ids") or None,
        }
