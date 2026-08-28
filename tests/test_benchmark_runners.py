"""Tests for EvaluationService (Application Layer: Empirical Execution Engine)."""

import json
from pathlib import Path

from benchmarking.application.evaluation_service import EvaluationService
from benchmarking.domain.services.baselines import run_cmaes, run_de, run_pso
from benchmarking.infra.io.trace_repository import EvaluationStateRepository, IOHTraceReader
from benchmarking.infra.logging import EvaluationLogger
from benchmarking.infra.storage import (
    ChampionsReadRepository,
    EvaluationConfigRepository,
    SQLiteSynthesisReadRepository,
)
from evolution.domain.services.noise_strategy import NoNoiseStrategy
from evolution.infra.problems.bbob import BBOBProblem
from shared.database import create_db_session_factory


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
    """Test EvaluationService executing classical baselines, caching, and dashboard."""
    eval_dir = tmp_path / "evaluations"
    cfg_file = tmp_path / "benchmark.toml"
    cfg_file.write_text(
        """
[benchmarking]
target_eval_runs = 2
budget_multiplier = 50
eval_timeout_seconds = 30.0
classical_baselines = ["cmaes", "de", "pso"]
target_problems = [1]
target_dims = [2]
target_noise_levels = [0.0]
""",
        encoding="utf-8",
    )

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    champions_repo = ChampionsReadRepository(session_factory)
    trace_repo = IOHTraceReader(eval_dir=eval_dir)
    state_repo = EvaluationStateRepository(eval_dir=eval_dir)
    config_repo = EvaluationConfigRepository(config_path=cfg_file)
    logger = EvaluationLogger()

    service = EvaluationService(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        trace_repo=trace_repo,
        state_repo=state_repo,
        config_repo=config_repo,
        logger=logger,
    )

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
    """Test EvaluationService executing LLM champion code, compilation, caching, and dashboard."""
    eval_dir = tmp_path / "evaluations"
    project_root = tmp_path / "project"
    project_root.mkdir()

    cfg_file = tmp_path / "benchmark.toml"
    cfg_file.write_text(
        """
[benchmarking]
target_eval_runs = 2
budget_multiplier = 50
eval_timeout_seconds = 5.0
classical_baselines = ["cmaes", "de", "pso"]
target_problems = [1]
target_dims = [2]
target_noise_levels = [0.0]
""",
        encoding="utf-8",
    )

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    champions_repo = ChampionsReadRepository(session_factory)
    trace_repo = IOHTraceReader(eval_dir=eval_dir)
    state_repo = EvaluationStateRepository(eval_dir=eval_dir)
    config_repo = EvaluationConfigRepository(config_path=cfg_file)

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

    logger = EvaluationLogger()
    service = EvaluationService(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        trace_repo=trace_repo,
        state_repo=state_repo,
        config_repo=config_repo,
        logger=logger,
        project_root=project_root,
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


def test_service_incremental_resumption(tmp_path: Path):
    """Test incremental resumption: scaling from 2 runs to 4 runs without full re-execution."""
    eval_dir = tmp_path / "evaluations"
    project_root = tmp_path / "project"
    project_root.mkdir()

    cfg_file_2runs = tmp_path / "benchmark_2runs.toml"
    cfg_file_2runs.write_text(
        """
[benchmarking]
target_eval_runs = 2
budget_multiplier = 50
eval_timeout_seconds = 5.0
classical_baselines = ["cmaes", "de", "pso"]
target_problems = [1]
target_dims = [2]
target_noise_levels = [0.0]
""",
        encoding="utf-8",
    )

    cfg_file_4runs = tmp_path / "benchmark_4runs.toml"
    cfg_file_4runs.write_text(
        """
[benchmarking]
target_eval_runs = 4
budget_multiplier = 50
eval_timeout_seconds = 5.0
classical_baselines = ["cmaes", "de", "pso"]
target_problems = [1]
target_dims = [2]
target_noise_levels = [0.0]
""",
        encoding="utf-8",
    )

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    champions_repo = ChampionsReadRepository(session_factory)
    trace_repo = IOHTraceReader(eval_dir=eval_dir)
    state_repo = EvaluationStateRepository(eval_dir=eval_dir)
    config_repo_2 = EvaluationConfigRepository(config_path=cfg_file_2runs)
    config_repo_4 = EvaluationConfigRepository(config_path=cfg_file_4runs)
    logger = EvaluationLogger()

    dummy_code = """
import numpy as np

class IncrementalOptimizer:
    def __call__(self, problem, budget=100):
        lb, ub = problem.lower_bound, problem.upper_bound
        dim = len(lb)
        best_x = np.zeros(dim)
        best_y = problem(best_x)
        return best_x, best_y
"""
    code_path = project_root / "algorithms" / "inc_champ.py"
    code_path.parent.mkdir()
    code_path.write_text(dummy_code, encoding="utf-8")

    champ_info = {
        "problem_id": 1,
        "dim": 2,
        "noise_std": 0.0,
        "prompt_strategy": "baseline",
        "llm_name": "qwen2.5-coder-14b",
        "algorithm_name": "IncrementalOptimizer",
        "experiment_id": 102,
        "code_path": "algorithms/inc_champ.py",
    }

    # Step 1: Initial run with target_eval_runs=2
    service_initial = EvaluationService(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        trace_repo=trace_repo,
        state_repo=state_repo,
        config_repo=config_repo_2,
        logger=logger,
        project_root=project_root,
    )
    res_1 = service_initial.run_champion_trials(champ_info)
    assert res_1["status"] == "SUCCESS"
    assert len(res_1["clean_errors"]) == 2

    solver_dir = eval_dir / "2D" / "std_0.0" / "f1" / "qwen_14b_baseline"
    assert trace_repo.get_run_count(solver_dir) == 2

    # Step 2: Resume with target_eval_runs=4
    service_resumed = EvaluationService(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        trace_repo=trace_repo,
        state_repo=state_repo,
        config_repo=config_repo_4,
        logger=logger,
        project_root=project_root,
    )
    res_2 = service_resumed.run_champion_trials(champ_info)
    assert res_2["status"] == "SUCCESS"
    assert len(res_2["clean_errors"]) == 4
    assert trace_repo.get_run_count(solver_dir) == 4

    prov_file = solver_dir / "provenance.json"
    prov_data = json.loads(prov_file.read_text(encoding="utf-8"))
    assert prov_data["n_runs"] == 4
    assert len(prov_data["clean_errors"]) == 4

    # Step 3: Baseline incremental resumption
    base_res_1 = service_initial.run_baseline_trials(dim=2, noise_std=0.0, p_id=1, baseline_slug="pso")
    assert base_res_1["status"] == "SUCCESS"
    assert len(base_res_1["clean_errors"]) == 2

    pso_dir = eval_dir / "2D" / "std_0.0" / "f1" / "pso"
    assert trace_repo.get_run_count(pso_dir) == 2

    base_res_2 = service_resumed.run_baseline_trials(dim=2, noise_std=0.0, p_id=1, baseline_slug="pso")
    assert base_res_2["status"] == "SUCCESS"
    assert len(base_res_2["clean_errors"]) == 4
    assert trace_repo.get_run_count(pso_dir) == 4


def test_evaluation_config_repository_edge_cases(tmp_path: Path):
    """Test EvaluationConfigRepository handling missing, empty, or NoneType configuration sections."""
    # 1. Non-existent files
    repo_missing = EvaluationConfigRepository(
        config_path=tmp_path / "nonexistent_bench.toml",
        baselines_path=tmp_path / "nonexistent_base.toml",
    )
    cfg_missing = repo_missing.load_config()
    assert cfg_missing["target_eval_runs"] == 20
    assert "cmaes" in cfg_missing["baseline_labels"]

    # 2. Empty TOML file
    empty_cfg_file = tmp_path / "empty_bench.toml"
    empty_cfg_file.write_text("", encoding="utf-8")
    repo_empty = EvaluationConfigRepository(config_path=empty_cfg_file)
    cfg_empty = repo_empty.load_config()
    assert cfg_empty["target_eval_runs"] == 20

    # 3. File with empty [benchmarking] section
    bench_empty_file = tmp_path / "bench_empty.toml"
    bench_empty_file.write_text("[benchmarking]\n", encoding="utf-8")
    repo_bench_empty = EvaluationConfigRepository(config_path=bench_empty_file)
    cfg_bench_empty = repo_bench_empty.load_config()
    assert cfg_bench_empty["target_eval_runs"] == 20
    assert cfg_bench_empty["budget_multiplier"] == 10000

    # 4. File with [evaluation] section fallback
    eval_file = tmp_path / "eval_fallback.toml"
    eval_file.write_text("[evaluation]\ntarget_eval_runs = 5\n", encoding="utf-8")
    repo_eval = EvaluationConfigRepository(config_path=eval_file)
    cfg_eval = repo_eval.load_config()
    assert cfg_eval["target_eval_runs"] == 5


def test_evaluation_logger(tmp_path: Path):
    """Verify EvaluationLogger formatting and verbosity controls."""
    import io
    from benchmarking.infra.logging import EvaluationLogger

    # 1. EvaluationLogger capturing output
    buf = io.StringIO()
    logger = EvaluationLogger(verbose=True, stream=buf)
    logger.header("Test Header", subtitle="Testing logger")
    logger.info("Informational message")
    logger.success("Success message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.condition_start(
        index=1,
        total=5,
        solver_type="champion",
        solver_name="TestSolver",
        dim=2,
        noise_std=0.0,
        problem_id=1,
        problem_name="Sphere",
    )
    logger.trial(trial_idx=1, total_trials=10, best_clean=1e-5, runtime=0.2, evals_used=500)
    logger.cached(runs_count=10, median_error=1e-5)
    logger.resuming(existing_runs=3, target_runs=10)
    logger.condition_complete(n_runs=10, median_error=1e-5)
    logger.missing_code("/path/to/missing.py")
    logger.summary("Batch Complete", stats={"Total": 10, "Cached": 5})

    output = buf.getvalue()
    assert "TEST HEADER" in output
    assert "Informational message" in output
    assert "Success message" in output
    assert "TestSolver" in output
    assert "Sphere" in output
    assert "Trial  1/10" in output
    assert "CACHED" in output

    # 2. Quiet mode (verbose=False)
    buf_quiet = io.StringIO()
    quiet_logger = EvaluationLogger(verbose=False, stream=buf_quiet)
    quiet_logger.header("Quiet Header")
    quiet_logger.info("Quiet info")
    assert buf_quiet.getvalue() == ""


def test_evaluation_service_run_verbose_control(tmp_path: Path):
    """Verify that verbose flag on EvaluationService.run_* methods controls output dynamically."""
    import io
    from benchmarking.infra.logging import EvaluationLogger

    buf = io.StringIO()
    custom_logger = EvaluationLogger(verbose=True, stream=buf)

    eval_dir = tmp_path / "evaluations"
    cfg_file = tmp_path / "benchmark.toml"
    cfg_file.write_text(
        """
[benchmarking]
target_eval_runs = 2
budget_multiplier = 50
eval_timeout_seconds = 30.0
classical_baselines = ["cmaes"]
target_problems = [1]
target_dims = [2]
target_noise_levels = [0.0]
""",
        encoding="utf-8",
    )

    session_factory = create_db_session_factory()
    sqlite_repo = SQLiteSynthesisReadRepository(session_factory)
    champions_repo = ChampionsReadRepository(session_factory)
    trace_repo = IOHTraceReader()
    state_repo = EvaluationStateRepository(eval_dir=eval_dir)
    config_repo = EvaluationConfigRepository(config_path=cfg_file)

    service = EvaluationService(
        sqlite_repo=sqlite_repo,
        champions_repo=champions_repo,
        trace_repo=trace_repo,
        state_repo=state_repo,
        config_repo=config_repo,
        logger=custom_logger,
    )

    # 1. Run with verbose=False -> No output captured in buffer
    service.run_baselines(verbose=False)
    assert buf.getvalue() == ""

    # 2. Run with verbose=True -> Output is captured
    service.run_baselines(verbose=True)
    assert len(buf.getvalue()) > 0
    assert "CMA-ES" in buf.getvalue()






