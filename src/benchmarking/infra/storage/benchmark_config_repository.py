"""Validate benchmark TOML once before constructing execution workflows."""

import tomllib
from pathlib import Path

from pydantic import TypeAdapter

from benchmarking.application.benchmark_config import BenchmarkConfig
from shared.config import CONFIGS_DIR


class BenchmarkConfigRepository:
    """Load typed benchmark settings and string-valued baseline metadata."""

    def __init__(
        self,
        config_path: Path = CONFIGS_DIR / "benchmark.toml",
        baselines_path: Path = CONFIGS_DIR / "baselines.toml",
    ) -> None:
        self.config_path = config_path
        self.baselines_path = baselines_path

    def load_baselines(self) -> dict[str, dict[str, str]]:
        if not self.baselines_path.exists():
            return {
                "cmaes": {"slug": "cmaes", "display_name": "CMA-ES"},
                "de": {"slug": "de", "display_name": "Differential Evolution"},
                "pso": {"slug": "pso", "display_name": "Particle Swarm Optimization"},
            }
        with self.baselines_path.open("rb") as stream:
            sections = tomllib.load(stream)
        return TypeAdapter(dict[str, dict[str, str]]).validate_python(
            sections.get("baselines", {}), strict=True
        )

    def load_config(self) -> BenchmarkConfig:
        sections: dict[str, object] = {}
        if self.config_path.exists():
            with self.config_path.open("rb") as stream:
                sections = tomllib.load(stream)
        if sections and "benchmarking" not in sections:
            raise ValueError("Benchmark configuration requires a [benchmarking] section.")
        settings = sections.get("benchmarking", {})
        if not isinstance(settings, dict):
            raise ValueError("The benchmarking section must be a TOML table.")
        if settings and "budget" not in settings:
            raise ValueError("Set benchmarking.budget to a fixed objective-call allowance.")
        baselines = self.load_baselines()
        return BenchmarkConfig(
            **{
                **settings,
                "benchmarking": settings,
                "baseline_labels": {
                    slug: info.get("display_name", slug.upper()) for slug, info in baselines.items()
                },
            }
        )
