"""Tests for BenchmarkEvaluationService (Application Layer: Empirical Execution Engine)."""

import json
from pathlib import Path

from benchmarking.application.evaluation_service import BenchmarkEvaluationService
from benchmarking.domain.baselines import run_cmaes, run_de, run_pso
from evolution.domain.services.noise_strategy import NoNoiseStrategy
from evolution.infra.problems.bbob import BBOBProblem


def test_baselines_callables():
    """Verify that classical baselines execute and return a candidate and fitness."""
    prob = BBOBProblem(problem_id=1, dim=2, instance_id=1, noise_strategy=NoNoiseStrategy())

    # 1. CMA-ES
    best_y, rt, evals = run_cmaes(prob, budget=50)
    assert isinstance(best_y, float)
    assert evals > 0

    # 2. DE
    prob2 = BBOBProblem(problem_id=1, dim=2, instance_id=1, noise_strategy=NoNoiseStrategy())
    best_y, rt, evals = run_de(prob2, budget=50)
    assert isinstance(best_y, float)
    assert evals > 0

    # 3. PSO
    prob3 = BBOBProblem(problem_id=1, dim=2, instance_id=1, noise_strategy=NoNoiseStrategy())
    best_y, rt, evals = run_pso(prob3, budget=50)
    assert isinstance(best_y, float)
    assert evals > 0


def test_service_baseline_execution(tmp_path: Path):
    """Test BenchmarkEvaluationService executing classical baselines, caching, and dashboard."""
    eval_dir = tmp_path / "evaluations"
    service = BenchmarkEvaluationService(eval_dir=eval_dir, n_runs=2, budget_multiplier=50)

    # 1. Run evaluation
    res = service.run_baseline_trials(dim=2, noise_std=0.0, p_id=1, baseline_slug="pso")
    assert res["status"] == "SUCCESS"
    assert len(res["clean_errors"]) == 2
    assert res["median_clean_error"] is not None

    prov_file = eval_dir / "2D" / "std_0.0" / "f1" / "pso" / "provenance.json"
    assert prov_file.exists()
    prov_data = json.loads(prov_file.read_text(encoding="utf-8"))
    assert prov_data["baseline"] == "pso"
    assert prov_data["n_runs"] == 2

    # 2. Second call should hit cache
    cached_res = service.run_baseline_trials(dim=2, noise_std=0.0, p_id=1, baseline_slug="pso")
    assert cached_res["status"] == "CACHED"


def test_service_champion_execution(tmp_path: Path):
    """Test BenchmarkEvaluationService executing LLM champion code, compilation, caching, and dashboard."""
    eval_dir = tmp_path / "evaluations"
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Create dummy champion algorithm script conforming to (problem, budget) contract
    dummy_code = """
import numpy as np

class RandomOptimizer:
    def __init__(self):
        pass

    def __call__(self, problem, budget=100):
        lb, ub = problem.lower_bound, problem.upper_bound
        dim = len(lb)
        best_x = None
        best_y = float('inf')
        for _ in range(min(budget, 20)):
            x = np.random.uniform(lb, ub, dim)
            y = problem(x)
            if y < best_y:
                best_y = y
                best_x = x
        return best_x, best_y
"""
    code_path = project_root / "algorithms" / "champ.py"
    code_path.parent.mkdir()
    code_path.write_text(dummy_code, encoding="utf-8")

    service = BenchmarkEvaluationService(
        eval_dir=eval_dir,
        project_root=project_root,
        n_runs=2,
        trial_timeout_seconds=5,
        budget_multiplier=50,
    )

    champ_info = {
        "problem_id": 1,
        "dim": 2,
        "noise_std": 0.0,
        "prompt_strategy": "baseline",
        "llm_name": "qwen2.5-coder-14b",
        "algorithm_name": "RandomOptimizer",
        "experiment_id": 101,
        "code_path": "algorithms/champ.py",
    }

    # 1. Run evaluation
    res = service.run_champion_trials(champ_info)
    assert res["status"] == "SUCCESS"
    assert len(res["clean_errors"]) == 2
    assert res["median_clean_error"] is not None

    prov_file = eval_dir / "2D" / "std_0.0" / "f1" / "qwen_14b_baseline" / "provenance.json"
    assert prov_file.exists()
    prov_data = json.loads(prov_file.read_text(encoding="utf-8"))
    assert prov_data["algorithm_name"] == "RandomOptimizer"
    assert prov_data["n_runs"] == 2

    # 2. Second call should hit cache
    cached_res = service.run_champion_trials(champ_info)
    assert cached_res["status"] == "CACHED"

    # 3. Missing code handling
    missing_champ = dict(champ_info)
    missing_champ["code_path"] = "algorithms/nonexistent.py"
    missing_res = service.run_champion_trials(missing_champ)
    assert missing_res["status"] == "MISSING_CODE"
