"""Infrastructure adapters for third-party and classical optimization solvers."""

from benchmark.infra.solvers.baselines import (
    get_baseline_runner,
    run_cmaes,
    run_de,
    run_pso,
)

__all__ = ["get_baseline_runner", "run_cmaes", "run_de", "run_pso"]
