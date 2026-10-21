"""Benchmark Configuration Read Repository (Pure I/O & TOML Parsing).

Encapsulates reading, parsing, and resolving configs/benchmark.toml and configs/baselines.toml
for multi-trial benchmark evaluations and classical baselines.
"""

import tomllib
from pathlib import Path
from typing import cast

from benchmarking.application.benchmark_config import BenchmarkConfig
from shared.config import CONFIGS_DIR

TomlTable = dict[str, object]


class BenchmarkConfigRepository:
    """Infrastructure repository for reading and parsing benchmark.toml and baselines.toml."""

    def __init__(
        self,
        config_path: Path = CONFIGS_DIR / "benchmark.toml",
        baselines_path: Path = CONFIGS_DIR / "baselines.toml",
    ) -> None:
        self.config_path = config_path
        self.baselines_path = baselines_path

    def load_baselines(self) -> dict[str, dict[str, str]]:
        """Loads baseline optimizer metadata and display labels from baselines.toml."""
        if not self.baselines_path.exists():
            return {
                "cmaes": {"slug": "cmaes", "display_name": "CMA-ES"},
                "de": {"slug": "de", "display_name": "Differential Evolution"},
                "pso": {"slug": "pso", "display_name": "Particle Swarm Optimization"},
            }
        with open(self.baselines_path, "rb") as f:
            raw_baselines = tomllib.load(f).get("baselines", {})
        if not isinstance(raw_baselines, dict):
            return {}
        return {
            str(slug): {str(key): str(value) for key, value in metadata.items()}
            for slug, metadata in raw_baselines.items()
            if isinstance(metadata, dict)
        }

    def load_config(self) -> BenchmarkConfig:
        """Loads and parses the benchmark.toml configuration into an BenchmarkConfig model."""
        cfg: TomlTable = {}
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                cfg = cast(TomlTable, tomllib.load(f))

        if cfg and "benchmarking" not in cfg:
            raise ValueError("Benchmark configuration requires a [benchmarking] section.")
        raw_bench_cfg = cfg.get("benchmarking", {})
        bench_cfg = cast(TomlTable, raw_bench_cfg) if isinstance(raw_bench_cfg, dict) else {}
        if unknown := bench_cfg.keys() - BenchmarkConfig.model_fields.keys():
            raise ValueError(f"Unknown benchmark settings: {sorted(unknown)}")
        if bench_cfg and "budget" not in bench_cfg:
            raise ValueError("Set benchmarking.budget to a fixed objective-call allowance.")
        baselines_data = self.load_baselines()
        baseline_labels = {
            slug: info.get("display_name", slug.upper()) for slug, info in baselines_data.items()
        }

        raw_noises = bench_cfg.get("target_noise_stds")
        target_noise_stds = [float(n) for n in raw_noises] if isinstance(raw_noises, list) else []
        raw_classical_baselines = bench_cfg.get("classical_baselines", ["cmaes", "de", "pso"])
        classical_baselines = (
            [str(name) for name in raw_classical_baselines]
            if isinstance(raw_classical_baselines, list)
            else ["cmaes", "de", "pso"]
        )
        raw_reliability = bench_cfg.get("reliability", {})
        reliability = cast(TomlTable, raw_reliability) if isinstance(raw_reliability, dict) else {}

        return BenchmarkConfig(
            benchmarking=bench_cfg,
            trials_per_condition=int(bench_cfg.get("trials_per_condition", 20)),
            random_seed=int(bench_cfg.get("random_seed", 42)),
            first_instance_id=int(bench_cfg.get("first_instance_id", 2)),
            budget=bench_cfg.get("budget", 100_000),
            trial_timeout_seconds=float(bench_cfg.get("trial_timeout_seconds", 30.0)),
            observation_trace_points=int(bench_cfg.get("observation_trace_points", 64)),
            force_rerun=bool(bench_cfg.get("force_rerun", False)),
            fill_missing_only=bool(bench_cfg.get("fill_missing_only", True)),
            classical_baselines=classical_baselines,
            baseline_labels=baseline_labels,
            noise_robustness_enabled=bool(bench_cfg.get("noise_robustness_enabled", True)),
            cross_function_enabled=bool(bench_cfg.get("cross_function_enabled", False)),
            cross_function_problem_ids=bench_cfg.get(
                "cross_function_problem_ids", [1, 8, 11, 15, 21]
            ),
            target_noise_stds=target_noise_stds,
            reliability=reliability,
        )
