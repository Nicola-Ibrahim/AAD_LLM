"""Classical baseline optimization algorithms (Domain Solvers).

Contains mathematical optimization procedures for:
- CMA-ES (Covariance Matrix Adaptation Evolution Strategy)
- Differential Evolution (DE)
- Particle Swarm Optimization (PSO)
"""

from collections.abc import Callable
import time
from typing import Any

import numpy as np


def run_cmaes(problem: Any, budget: int) -> tuple[float, float, int]:
    """Execute CMA-ES on the target problem."""
    from cma import CMAEvolutionStrategy

    lb, ub = problem.lower_bound, problem.upper_bound
    dim = problem.dim
    x0 = np.random.uniform(lb[0], ub[0], dim)
    sigma0 = 0.5 * (ub[0] - lb[0]) / 3.0
    es = CMAEvolutionStrategy(x0, sigma0, {"bounds": [lb[0], ub[0]], "verbose": -9})

    t0 = time.perf_counter()
    evals = 0
    while not es.stop() and evals < budget:
        solutions = es.ask()
        fitnesses = [problem(x) for x in solutions]
        evals += len(solutions)
        es.tell(solutions, fitnesses)
    t1 = time.perf_counter()

    best_x = es.result.xbest
    best_clean = problem.eval_clean(best_x)
    return best_clean, t1 - t0, evals


def run_de(problem: Any, budget: int) -> tuple[float, float, int]:
    """Execute Differential Evolution on the target problem."""
    from scipy.optimize import differential_evolution

    lb, ub = problem.lower_bound, problem.upper_bound
    bounds = [(lb[i], ub[i]) for i in range(problem.dim)]
    t0 = time.perf_counter()
    res = differential_evolution(
        problem,
        bounds,
        maxiter=max(1, budget // (15 * problem.dim)),
        popsize=15,
        polish=False,
    )
    t1 = time.perf_counter()
    best_clean = problem.eval_clean(res.x)
    return best_clean, t1 - t0, res.nfev


def run_pso(problem: Any, budget: int) -> tuple[float, float, int]:
    """Execute Particle Swarm Optimization (PSO) on the target problem."""
    dim = problem.dim
    num_particles = min(50, max(10, 5 * dim))
    max_iter = max(1, budget // num_particles)
    lb, ub = problem.lower_bound[0], problem.upper_bound[0]

    X = np.random.uniform(lb, ub, (num_particles, dim))
    V = np.random.uniform(-(ub - lb), ub - lb, (num_particles, dim)) * 0.1
    pbest_X = X.copy()
    pbest_F = np.array([problem(x) for x in X])
    evals = num_particles

    gbest_idx = np.argmin(pbest_F)
    gbest_X = pbest_X[gbest_idx].copy()
    gbest_F = pbest_F[gbest_idx]

    w, c1, c2 = 0.729, 1.49445, 1.49445
    t0 = time.perf_counter()

    for _ in range(max_iter):
        if evals >= budget:
            break
        r1 = np.random.rand(num_particles, dim)
        r2 = np.random.rand(num_particles, dim)
        V = w * V + c1 * r1 * (pbest_X - X) + c2 * r2 * (gbest_X - X)
        X = np.clip(X + V, lb, ub)

        for i in range(num_particles):
            if evals >= budget:
                break
            f = problem(X[i])
            evals += 1
            if f < pbest_F[i]:
                pbest_F[i] = f
                pbest_X[i] = X[i].copy()
                if f < gbest_F:
                    gbest_F = f
                    gbest_X = X[i].copy()

    t1 = time.perf_counter()
    best_clean = problem.eval_clean(gbest_X)
    return best_clean, t1 - t0, evals


def get_baseline_runner(baseline_slug: str) -> Callable[[Any, int], tuple[float, float, int]]:
    """Resolve and return the execution function for a baseline solver name."""
    match baseline_slug.lower():
        case "cmaes" | "cma-es":
            return run_cmaes
        case "de":
            return run_de
        case "pso":
            return run_pso
        case _:
            raise ValueError(f"Unknown baseline: '{baseline_slug}'. Supported: 'cmaes', 'de', 'pso'.")
