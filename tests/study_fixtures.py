"""Explicit small-study settings for isolated backend tests; no config files."""

from benchmarking.application.benchmark_config import BenchmarkConfig
from evolution.application.synthesis_config import SynthesisConfig


def run_parameters(config: SynthesisConfig | BenchmarkConfig) -> dict[str, object]:
    """Extract execution arguments for fixtures that also exercise internal components."""
    if isinstance(config, SynthesisConfig):
        fields = {
            "problem_targets",
            "noise_conditions",
            "synthesis_modes",
            "budget",
            "timeout_seconds",
            "iterations",
            "runs_per_config",
            "auto_resume",
            "skip_completed",
            "retry_failed_synthesis",
        }
    else:
        fields = {
            "trials_per_condition",
            "random_seed",
            "first_instance_id",
            "budget",
            "trial_timeout_seconds",
            "observation_trace_points",
            "force_rerun",
            "classical_baselines",
            "noise_robustness_enabled",
            "cross_function_enabled",
            "cross_function_problem_ids",
        }
    return config.model_dump(include=fields)


def synthesis_config(**overrides: object) -> SynthesisConfig:
    values = {
        "problem_targets": [
            {"id": problem, "dimensions": [2, 10, 50]} for problem in [1, 8, 11, 15, 21]
        ],
        "noise_conditions": [
            {"std": 0.0, "noise_model": "none"},
            {"std": 0.05, "noise_model": "heteroscedastic"},
            {"std": 0.1, "noise_model": "heteroscedastic"},
            {"std": 0.2, "noise_model": "heteroscedastic"},
        ],
        "synthesis_modes": [
            {"mode": mode, "strategies": ["baseline", "thinking", "vectorization", "guided"]}
            for mode in ["explicit", "implicit"]
        ],
        "budget": 100_000,
    }
    return SynthesisConfig(**(values | overrides))
