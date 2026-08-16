from llamea import Solution

from domain.services.noise_strategy import MultiplicativeNoiseStrategy
from domain.vos import ProblemProfile
from infra.problems.bbob import BBOBProblem
from infra.storage.code.repository import CodeRepository
from infra.storage.sqlite.repository import SQLiteExperimentRepository
from synthesis.evaluator import Evaluator
from synthesis.execution.compiler import CodeCompiler
from synthesis.execution.executor import AlgorithmExecutor


def test_failure_tiers_and_is_failure():
    assert Evaluator.is_failure(Evaluator.FAILURE_FITNESS) is True
    assert Evaluator.is_failure(Evaluator.RUNTIME_FAILURE_FITNESS) is True
    assert Evaluator.is_failure(Evaluator.TIMEOUT_FAILURE_FITNESS) is True
    assert Evaluator.is_failure(float("-inf")) is True
    assert Evaluator.is_failure(float("nan")) is True

    # Real scores (e.g. -0.05, -100.0, 0.0) should NOT be failures
    assert Evaluator.is_failure(0.0) is False
    assert Evaluator.is_failure(-0.05) is False
    assert Evaluator.is_failure(-1000.0) is False
    assert Evaluator.is_failure(-1e6) is False


def test_stagnation_diversity_injection(db_session_factory, tmp_path):
    repo = SQLiteExperimentRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code_store")
    problem = BBOBProblem(
        problem_id=15,
        dim=3,
        noise_strategy=MultiplicativeNoiseStrategy(noise_std=0.5),
        ioh_logger=None,
    )
    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=15,
            dim=3,
            noise_std=0.5,
            noise_model="multiplicative",
            true_optimum=problem.true_optimum,
        ),
        mode="noisy",
        llm_name="test-llm",
    )

    evaluator = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        budget=100,
        experiment_id=exp_id,
        stagnation_threshold=3,
    )

    failing_code = """
import numpy as np
class FailingOpt:
    def __call__(self, problem, budget):
        raise ValueError("Intentional failure")
"""
    # 1st failure
    sol1 = Solution(code=failing_code, name="FailingOpt1")
    scored1 = evaluator(sol1)
    assert Evaluator.is_failure(scored1.fitness)
    assert "[META-FEEDBACK]" not in scored1.feedback

    # 2nd failure
    sol2 = Solution(code=failing_code, name="FailingOpt2")
    scored2 = evaluator(sol2)
    assert Evaluator.is_failure(scored2.fitness)
    assert "[META-FEEDBACK]" not in scored2.feedback

    # 3rd failure -> triggers stagnation diversity injection!
    sol3 = Solution(code=failing_code, name="FailingOpt3")
    scored3 = evaluator(sol3)
    assert Evaluator.is_failure(scored3.fitness)
    assert "[META-FEEDBACK]" in scored3.feedback
    assert "You MUST try a completely different algorithm family" in scored3.feedback


def test_evaluator_noisy_feedback_no_noise_std_leak(db_session_factory, tmp_path):
    repo = SQLiteExperimentRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code_store")
    problem = BBOBProblem(
        problem_id=15,
        dim=3,
        noise_strategy=MultiplicativeNoiseStrategy(noise_std=0.75),
        ioh_logger=None,
    )
    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=15,
            dim=3,
            noise_std=0.75,
            noise_model="multiplicative",
            true_optimum=problem.true_optimum,
        ),
        mode="noisy",
        llm_name="test-llm",
    )

    evaluator = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        budget=100,
        experiment_id=exp_id,
    )

    success_code = """
import numpy as np
class DummyOpt:
    def __call__(self, problem, budget):
        x = np.array([0.0, 0.0, 0.0])
        return x, float(problem(x))
"""
    sol = Solution(code=success_code, name="DummyOpt")
    scored = evaluator(sol)
    assert not Evaluator.is_failure(scored.fitness)
    # Ensure noise std numeric value 0.75 is NOT leaked in feedback
    assert "noise std: 0.75" not in scored.feedback
    assert "noise std:" not in scored.feedback
    assert "[NOISY PROBLEM]" in scored.feedback


def test_compiler_budget_leak_warning():
    compiler = CodeCompiler()
    code_with_leak = """
import numpy as np
class LeakOpt:
    def __call__(self, problem, budget):
        pop = [np.array([0.0, 0.0, 0.0])]
        best = min(pop, key=lambda x: problem(x))
        return best, float(problem(best))
"""
    _ = compiler.compile(code_with_leak, "LeakOpt", 3)
    warnings = getattr(compiler, "last_compiler_warnings", [])
    assert any("min(..., key=...)" in w for w in warnings)


def test_executor_budget_overrun_warning():
    executor = AlgorithmExecutor(timeout_seconds=5.0)

    class MockProblem:
        def __init__(self):
            self.evaluations = 150
            self.dim = 3
        def __call__(self, x):
            return 0.0

    overrun_code = """
import numpy as np
class OverrunOpt:
    def __call__(self, problem, budget):
        return np.array([0.0, 0.0, 0.0]), 0.0
"""
    mock_prob = MockProblem()
    _, _ = executor.execute_algorithm(overrun_code, "OverrunOpt", 3, mock_prob, budget=100)
    assert any("[BUDGET OVERRUN]" in w for w in executor.last_captured_warnings)
