import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from llamea import Solution
from sqlalchemy.orm import sessionmaker

from evolution.domain.vos import (
    Code,
    Convergence,
    Error,
    Execution,
    Fitness,
    IterationMetadata,
    ProblemProfile,
)
from evolution.domain.services.noise_strategy import HeteroscedasticNoiseStrategy, NoNoiseStrategy
from evolution.infra.problems.bbob import BBOBProblem
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.database import build_engine
from shared.tables import Base, ExperimentORM
from evolution.application.synthesis.evaluator import Evaluator
from evolution.application.synthesis.session import LLaMEASession
from evolution.application.tasks import (
    EvolutionTask,
    TaskOrchestrator,
)
from evolution.domain.exceptions import OrchestrationError


class DummyLLM:
    """Mock LLM that returns a simple dummy search algorithm."""

    def __init__(self):
        self.model = SimpleNamespace(name="dummy-llm-1.0")
        self.calls = 0

    def sample_solution(self, prompt, parent_ids=None, **kwargs):
        self.calls += 1
        code = """class DummySearch:
    def __call__(self, problem, budget):
        import numpy as np
        best_x = np.zeros(2)
        best_y = problem(best_x)
        for _ in range(budget - 1):
            x = np.random.uniform(-5, 5, 2)
            y = problem(x)
            if y < best_y:
                best_y = y
        return best_y
"""
        sol = Solution(code=code, name="DummySearch", parent_ids=parent_ids or [])
        sol.add_metadata("llm_generation_time", 0.05)
        return sol


class FailingProblem(BBOBProblem):
    @property
    def lower_bound(self):
        raise ValueError("Job failed")


def test_dispatch_with_clean_and_noisy(temp_dir, db_session_factory):
    db_path = temp_dir / "test.db"
    repo = SQLiteSynthesisRepository(db_session_factory)
    llm = DummyLLM()

    problem_clean = BBOBProblem(
        problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1
    )
    exp_id_clean = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=problem_clean.true_optimum),
        mode="clean",
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        iterations=2,
    )

    problem_noisy = BBOBProblem(
        problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.5), instance_id=1
    )
    exp_id_noisy = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.5, true_optimum=problem_noisy.true_optimum),
        mode="noisy",
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        iterations=2,
    )

    tasks = [
        EvolutionTask(
            key="clean",
            problem=problem_clean,
            llm_client=llm,
            experiment_id=exp_id_clean,
            iterations=2,
            db_path=db_path,
        ),
        EvolutionTask(
            key="noisy",
            problem=problem_noisy,
            llm_client=llm,
            experiment_id=exp_id_noisy,
            iterations=2,
            db_path=db_path,
        ),
    ]

    orchestrator = TaskOrchestrator(max_workers=2)
    results = orchestrator.run(tasks)

    assert "clean" in results
    assert "noisy" in results
    assert results["clean"].experiment_id != results["noisy"].experiment_id

    # Verify both clean and noisy experiments are stored in the DB
    loaded_clean = repo.load(problem_id=1, mode="clean")
    loaded_noisy = repo.load(problem_id=1, mode="noisy")

    assert len(loaded_clean) == 1
    assert loaded_clean[0].experiment_id == results["clean"].experiment_id
    assert len(loaded_noisy) == 1
    assert loaded_noisy[0].experiment_id == results["noisy"].experiment_id


def test_dispatch_partial_failure(temp_dir, db_session_factory):
    db_path = temp_dir / "test.db"
    repo = SQLiteSynthesisRepository(db_session_factory)
    problem_fail = FailingProblem(
        problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1
    )
    problem_succ = BBOBProblem(
        problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1
    )

    exp_id_fail = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1, dim=2, noise_std=0.0, true_optimum=0.0
        ),
        mode="clean",
        llm_name="dummy-llm-1.0",
        prompt_strategy="baseline",
        budget=1000,
        iterations=1,
    )
    exp_id_succ = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1, dim=2, noise_std=0.0, true_optimum=problem_succ.true_optimum
        ),
        mode="clean",
        llm_name="dummy-llm-1.0",
        prompt_strategy="baseline",
        budget=1000,
        iterations=1,
    )

    tasks = [
        EvolutionTask(
            key="failing",
            problem=problem_fail,
            llm_client=DummyLLM(),
            experiment_id=exp_id_fail,
            iterations=1,
            budget=1000,
            db_path=db_path,
        ),
        EvolutionTask(
            key="success",
            problem=problem_succ,
            llm_client=DummyLLM(),
            experiment_id=exp_id_succ,
            iterations=1,
            budget=1000,
            db_path=db_path,
        ),
    ]

    with pytest.raises(OrchestrationError) as exc_info:
        TaskOrchestrator().run(tasks)

    errors = exc_info.value.errors
    assert "failing" in errors
    assert isinstance(errors["failing"], ValueError)
    assert str(errors["failing"]) == "Job failed"

    # Verify success got persisted
    loaded_success = repo.load(problem_id=1, mode="clean")
    assert any(exp.experiment_id == exp_id_succ for exp in loaded_success)


@pytest.fixture
def temp_dir():
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d)


@pytest.fixture
def db_session_factory(temp_dir):
    db_path = temp_dir / "test.db"
    engine = build_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session


def test_evaluator_iteration_persistence(temp_dir, db_session_factory):
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)

    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum
        ),
        mode="clean",
        llm_name="dummy-llm",
    )

    evaluator = Evaluator(
        problem=problem,
        budget=10,
        experiment_id=exp_id,
        db_repo=repo,
        code_repo=code_repo,
    )

    # Run evaluation
    solution = Solution(
        code="""class TestSearch:
    def __call__(self, problem, budget):
        import numpy as np
        return problem(np.zeros(2))
""",
        name="test_search",
    )

    evaluator(solution)

    # Check that iteration was recorded in DB
    summaries = repo.load(problem_id=1, mode="clean")
    assert len(summaries) == 1
    assert len(summaries[0].iterations) == 1
    assert summaries[0].iterations[0].iteration == 1
    assert summaries[0].iterations[0].algorithm_name == "test_search"
    assert summaries[0].iterations[0].error.error_type is None


def test_evaluator_iteration_persistence_on_failure(temp_dir, db_session_factory):
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)

    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum
        ),
        mode="clean",
        llm_name="dummy-llm",
    )

    evaluator = Evaluator(
        problem=problem,
        budget=10,
        experiment_id=exp_id,
        db_repo=repo,
        code_repo=code_repo,
    )

    # Invalid syntax code to trigger compiler failure
    solution = Solution(
        code="""class FailedSearch:
    def __call__(self, problem, budget):
        this is invalid python syntax error!
""",
        name="failed_search",
    )

    evaluator(solution)

    # Check iteration grew in DB with error logs
    summaries = repo.load(problem_id=1, mode="clean")
    assert len(summaries) == 1
    assert len(summaries[0].iterations) == 1
    assert summaries[0].iterations[0].iteration == 1
    assert summaries[0].iterations[0].algorithm_name == "failed_search"
    assert summaries[0].iterations[0].error.error_type is not None
    assert "CodeValidationException" in summaries[0].iterations[0].error.error_type


def test_sqlite_create_and_append(db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)

    ctx1 = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=0.0),
        mode="clean",
        llm_name="dummy-llm",
    )

    it_meta = IterationMetadata(
        iteration=1,
        algorithm_name="test_search",
        execution={
            "timed_out": False,
            "runtime_seconds": 0.1,
            "llm_generation_time": 1.0,
            "evaluations_used": 1,
            "budget_consumed_pct": 10.0,
            "evals_per_second": 10.0,
        },
        fitness={
            "raw_fitness": 0.0,
            "final_error": 0.0,
            "relative_error": 0.0,
            "error_per_evaluation": 0.0,
        },
        code={
            "code_lines": 5,
            "code_length": 100,
            "code_path": None,
        },
        error={
            "error_type": None,
            "error_message": None,
            "error_traceback": None,
        },
        convergence={
            "converged": True,
            "convergence_threshold": 1e-6,
        },
    )

    repo.append_iteration(ctx1, it_meta)
    repo.mark_completed(ctx1)

    # Verify save
    with db_session_factory() as session:
        exp = session.query(ExperimentORM).first()
        assert exp.problem_id == 1
        assert exp.id == ctx1
        assert exp.status == "completed"
        assert len(exp.iterations) == 1
        assert exp.iterations[0].error_log is None

    summaries = repo.load(problem_id=1, mode="clean")
    assert len(summaries) == 1
    assert summaries[0].iterations[0].iteration == 1


def test_sqlite_append_with_error(db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)

    ctx = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=0.0),
        mode="clean",
        llm_name="dummy-llm",
    )

    it_meta = IterationMetadata(
        iteration=1,
        algorithm_name="failed_search",
        execution={
            "timed_out": False,
            "runtime_seconds": 0.1,
            "llm_generation_time": 1.0,
            "evaluations_used": 1,
            "budget_consumed_pct": 10.0,
            "evals_per_second": 10.0,
        },
        fitness={
            "raw_fitness": None,
            "final_error": None,
            "relative_error": None,
            "error_per_evaluation": None,
        },
        code={
            "code_lines": 5,
            "code_length": 100,
            "code_path": None,
        },
        error={
            "error_type": "SyntaxError",
            "error_message": "invalid syntax",
            "error_traceback": "traceback lines here",
        },
        convergence={
            "converged": False,
            "convergence_threshold": 1e-6,
        },
    )

    repo.append_iteration(ctx, it_meta)
    repo.mark_completed(ctx)

    # Load and verify error_log relation mapping
    loaded = repo.load(problem_id=1)
    assert len(loaded) == 1
    assert loaded[0].iterations[0].error.error_type == "SyntaxError"
    assert loaded[0].iterations[0].error.error_message == "invalid syntax"
    assert loaded[0].iterations[0].error.error_traceback == "traceback lines here"


def test_checkpoint_logger_and_resumption(temp_dir, db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)
    llm = DummyLLM()
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)

    exp_id = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum),
        mode=problem.mode,
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        iterations=2,
    )

    # 1. Run evolution for 2 iterations (budget=2).
    session1 = LLaMEASession(
        problem=problem,
        experiment_id=exp_id,
        initial_iteration=0,
        prompt_strategy="baseline",
        llm_client=llm,
        iterations=2,
        db_repo=repo,
        code_repo=code_repo,
    )
    res1 = session1.run()

    archive_dir = session1._archive_dir
    assert not archive_dir.exists()

    # Verify DB saved the run
    loaded_runs = repo.load(problem_id=1, mode="clean")
    assert len(loaded_runs) == 1
    assert loaded_runs[0].experiment_id == res1.experiment_id


def test_auto_experiment_id_and_session_persistence(temp_dir, db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)
    llm = DummyLLM()
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)

    exp_id1 = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum),
        mode=problem.mode,
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        iterations=2,
    )
    session1 = LLaMEASession(
        problem=problem,
        experiment_id=exp_id1,
        initial_iteration=0,
        prompt_strategy="baseline",
        llm_client=llm,
        db_repo=repo,
        code_repo=code_repo,
        iterations=2,
    )
    res1 = session1.run()

    exp_id2 = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum),
        mode=problem.mode,
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        iterations=2,
    )
    session2 = LLaMEASession(
        problem=problem,
        experiment_id=exp_id2,
        initial_iteration=0,
        prompt_strategy="baseline",
        llm_client=llm,
        db_repo=repo,
        code_repo=code_repo,
        iterations=2,
    )
    res2 = session2.run()

    assert res1.experiment_id != res2.experiment_id

    # Verify both runs are stored in DB with distinct experiment_ids
    runs = repo.load(problem_id=1, mode="clean")
    assert len(runs) == 2
    assert {r.experiment_id for r in runs} == {res1.experiment_id, res2.experiment_id}


def test_session_none_llm_guard(temp_dir, db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)

    with pytest.raises(ValueError, match="LLaMEASession requires a valid LLMClient"):
        LLaMEASession(
            problem=problem,
            experiment_id=1,
            initial_iteration=0,
            prompt_strategy="baseline",
            llm_client=None,
            db_repo=repo,
            code_repo=code_repo,
        )


def test_session_mark_failed_on_error(temp_dir, db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)
    llm = DummyLLM()
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)

    exp_id = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum),
        mode=problem.mode,
        llm_name=llm.model.name,
        prompt_strategy="baseline",
        budget=1000000,
        iterations=2,
    )

    session = LLaMEASession(
        problem=problem,
        experiment_id=exp_id,
        initial_iteration=0,
        prompt_strategy="baseline",
        llm_client=llm,
        db_repo=repo,
        code_repo=code_repo,
        iterations=2,
    )

    # Inject an error into _setup_evaluator to force run() to fail
    def bad_setup():
        raise RuntimeError("Simulated evaluation failure")

    session._setup_evaluator = bad_setup

    with pytest.raises(RuntimeError, match="Simulated evaluation failure"):
        session.run()

    with db_session_factory() as db_session:
        existing = db_session.get(ExperimentORM, exp_id)
        assert existing is not None
        assert existing.status == "failed"


def test_evolution_task_execution(temp_dir, db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)
    llm = DummyLLM()
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)

    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum
        ),
        mode="clean",
        llm_name=llm.model.name,
        budget=2500,
    )

    task = EvolutionTask(
        key="test_task_1",
        problem=problem,
        llm_client=llm,
        experiment_id=exp_id,
        initial_iteration=0,
        budget=2500,
        iterations=2,
        db_path=temp_dir / "test.db",
    )
    assert task.experiment_id == exp_id
    assert task.problem.problem_id == 1
    assert task.problem.dim == 2
    assert task.budget == 2500
    res = task()
    assert res is not None
    assert res.experiment_id == exp_id


def test_session_problem_validation(temp_dir, db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)
    llm = DummyLLM()

    with pytest.raises(ValueError, match="LLaMEASession requires a valid problem"):
        LLaMEASession(
            problem=None,
            experiment_id=1,
            initial_iteration=0,
            prompt_strategy="baseline",
            llm_client=llm,
            db_repo=repo,
            code_repo=code_repo,
        )


def test_evaluator_current_iteration_resumes_from_db(temp_dir, db_session_factory):
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=temp_dir)
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy(), instance_id=1)

    exp_id = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0, true_optimum=0.0),
        mode="clean",
        llm_name="dummy",
    )

    status, max_iter = repo.get_experiment_status(exp_id)
    assert status == "running"
    assert max_iter == 0

    evaluator1 = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        experiment_id=exp_id,
    )
    assert evaluator1._current_iteration == 0

    # Simulate 3 iterations persisted
    for i in range(1, 4):
        evaluator1._current_iteration = i - 1
        meta = IterationMetadata(
            iteration=i,
            algorithm_name="Alg",
            execution=Execution(
                timed_out=False,
                runtime_seconds=1.0,
                evaluations_used=10,
                budget_consumed_pct=1.0,
                evals_per_second=10.0,
            ),
            fitness=Fitness(),
            code=Code(code_lines=10, code_length=100),
            error=Error(),
            convergence=Convergence(converged=False, convergence_threshold=1e-6),
        )
        repo.append_iteration(exp_id, meta)

    _, max_iter = repo.get_experiment_status(exp_id)
    assert max_iter == 3

    # New Evaluator created for the same experiment_id (e.g. during warm start)
    evaluator2 = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        experiment_id=exp_id,
        initial_iteration=max_iter,
    )
    assert evaluator2._current_iteration == 3


class FailingLLM:
    """Mock LLM that returns invalid python code causing candidate execution failure."""

    def __init__(self):
        self.model = SimpleNamespace(name="failing-llm-1.0")

    def sample_solution(self, prompt, parent_ids=None, **kwargs):
        sol = Solution(
            code="invalid python code !!! syntax error",
            name="InvalidAlg",
            description="Broken code generator",
        )
        sol.add_metadata("llm_generation_time", 0.05)
        return sol


def test_all_executions_failed_session_handling(db_session_factory, tmp_path):
    """Verify LLaMEASession handles cases gracefully when all generated candidate algorithms fail."""
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code_store")
    problem = BBOBProblem(problem_id=24, dim=2, noise_strategy=NoNoiseStrategy())
    mock_llm = FailingLLM()

    exp_id = repo.create_experiment(
        problem=ProblemProfile(problem_id=24, dim=2, noise_std=0.0, true_optimum=problem.true_optimum),
        mode=problem.mode,
        llm_name=mock_llm.model.name,
        prompt_strategy="baseline",
        budget=10,
        iterations=2,
    )

    session = LLaMEASession(
        problem=problem,
        experiment_id=exp_id,
        initial_iteration=0,
        prompt_strategy="baseline",
        llm_client=mock_llm,
        db_repo=repo,
        code_repo=code_repo,
        budget=10,
        iterations=2,
    )

    # Must complete without throwing AttributeError or crashing
    result = session.run()

    assert result.best_error is None
    assert result.problem_id == 24
    assert result.dim == 2


def test_prompt_strategy_persisted(db_session_factory, tmp_path):
    """Verify create_experiment and load properly handle prompt_strategy."""
    repo = SQLiteSynthesisRepository(db_session_factory)
    exp_id = repo.create_experiment(
        problem=ProblemProfile(problem_id=1, dim=3, noise_std=0.0, true_optimum=0.0),
        mode="clean",
        llm_name="test-llm",
        prompt_strategy="vectorization",
    )
    repo.mark_completed(exp_id)

    summaries = repo.load(problem_id=1, prompt_strategy="vectorization")
    assert len(summaries) == 1
    assert summaries[0].prompt_strategy == "vectorization"

    # Filter with different strategy returns empty list
    empty_summaries = repo.load(problem_id=1, prompt_strategy="baseline")
    assert len(empty_summaries) == 0


def test_scipy_optimize_banned(tmp_path):
    """Verify that generated code attempting to use scipy.optimize fails execution or compilation."""
    from shared.execution import AlgorithmExecutor, CodeValidationException

    executor = AlgorithmExecutor(timeout_seconds=2.0)
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    problem_fn = problem.get_objective_fn()

    banned_code = """
import scipy.optimize

class BannedOptimizer:
    def __call__(self, problem, budget):
        res = scipy.optimize.minimize(problem, [0.0, 0.0])
        return res.x, float(res.fun)
"""
    with pytest.raises(CodeValidationException):
        executor.execute_algorithm(banned_code, "BannedOptimizer", 2, problem_fn, 100)


def test_evaluator_clean_reevaluation_with_tuple_return(db_session_factory, tmp_path):
    """Verify that Evaluator clean re-evaluates best_x when algorithm returns a (best_x, best_y) tuple."""
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code_store")
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=HeteroscedasticNoiseStrategy(0.5))
    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1,
            dim=2,
            noise_std=0.5,
            noise_model="heteroscedastic",
            true_optimum=problem.true_optimum,
        ),
        mode="noisy",
        llm_name="test-llm",
    )
    evaluator = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        budget=10,
        experiment_id=exp_id,
    )

    good_code = """
import numpy as np

class CustomOpt:
    def __call__(self, problem, budget):
        # Coordinates of known optimum for f1 instance 1
        opt_x = getattr(problem, 'optimum_x', np.zeros(2))
        noisy_y = problem(opt_x)
        return opt_x, float(noisy_y)
"""
    sol = Solution(code=good_code, name="CustomOpt", description="Test solution")
    scored_sol = evaluator(sol)
    assert scored_sol.fitness is not None
    # Because opt_x is the true optimum, clean error should be near 0.0 (< 1e-4) even though noisy_y was perturbed
    assert scored_sol.fitness > -0.01


def test_evaluator_out_of_bounds_best_x_rejected(db_session_factory, tmp_path):
    """Verify that Evaluator marks algorithm as failed if returned best_x is out of search space bounds."""
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code_store")
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum
        ),
        mode="clean",
        llm_name="test-llm",
    )
    evaluator = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        budget=10,
        experiment_id=exp_id,
    )

    out_of_bounds_code = """
import numpy as np

class BadOpt:
    def __call__(self, problem, budget):
        return np.array([999.0, 999.0]), 0.0
"""
    sol = Solution(code=out_of_bounds_code, name="BadOpt", description="Out of bounds solution")
    scored_sol = evaluator(sol)
    assert Evaluator.is_failure(scored_sol.fitness)
    assert scored_sol.fitness == Evaluator.RUNTIME_FAILURE_FITNESS
    assert "outside search space bounds" in scored_sol.feedback


def test_convergence_evaluate():
    profile_met = Convergence.evaluate(1e-7, threshold=1e-6)
    assert profile_met.converged is True
    assert profile_met.convergence_threshold == 1e-6

    profile_unmet = Convergence.evaluate(1e-5, threshold=1e-6)
    assert profile_unmet.converged is False
    assert profile_unmet.convergence_threshold == 1e-6

    profile_none = Convergence.evaluate(None, threshold=1e-6)
    assert profile_none.converged is False
    assert profile_none.convergence_threshold == 1e-6


def test_evaluator_failure_fitness_and_categorized_feedback(db_session_factory, tmp_path):
    """Verify that failure returns Evaluator failure tiers and categorized feedback prefixes."""
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code_store")
    problem = BBOBProblem(problem_id=1, dim=2, noise_strategy=NoNoiseStrategy())
    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=1, dim=2, noise_std=0.0, true_optimum=problem.true_optimum
        ),
        mode="clean",
        llm_name="test-llm",
    )
    evaluator = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        budget=10,
        experiment_id=exp_id,
    )

    # Test Runtime Error (ZeroDivisionError / Math Error)
    zero_div_code = """
import numpy as np
class ZeroDivOpt:
    def __call__(self, problem, budget):
        return np.array([0.0, 0.0]), 1.0 / 0.0
"""
    sol = Solution(code=zero_div_code, name="ZeroDivOpt", description="Zero div solution")
    scored = evaluator(sol)
    assert Evaluator.is_failure(scored.fitness)
    assert scored.fitness == Evaluator.RUNTIME_FAILURE_FITNESS
    assert "[MATH ERROR]" in scored.feedback

    # Test Non-Finite return from algorithm
    nan_return_code = """
import numpy as np
class NanOpt:
    def __call__(self, problem, budget):
        return np.array([0.0, 0.0]), float("nan")
"""
    sol_nan = Solution(code=nan_return_code, name="NanOpt", description="Nan return solution")
    scored_nan = evaluator(sol_nan)
    assert Evaluator.is_failure(scored_nan.fitness)
    assert scored_nan.fitness == Evaluator.RUNTIME_FAILURE_FITNESS
    assert "[INVALID RETURN]" in scored_nan.feedback


def test_evaluator_enriched_feedback_and_warnings(db_session_factory, tmp_path):
    """Verify code snippet extraction (Option A), problem context footer (Option B), and warning capture (Option D)."""
    repo = SQLiteSynthesisRepository(db_session_factory)
    code_repo = CodeRepository(base_dir=tmp_path / "code_store")
    problem = BBOBProblem(problem_id=8, dim=3, noise_strategy=NoNoiseStrategy())
    exp_id = repo.create_experiment(
        problem=ProblemProfile(
            problem_id=8, dim=3, noise_std=0.0, true_optimum=problem.true_optimum
        ),
        mode="clean",
        llm_name="test-llm",
    )
    evaluator = Evaluator(
        problem=problem,
        db_repo=repo,
        code_repo=code_repo,
        budget=10,
        experiment_id=exp_id,
    )

    # Candidate code with runtime error and numpy warning
    runtime_err_code = """import numpy as np

class BadMatrixOpt:
    def __call__(self, problem, budget):
        # Line 6: Trigger numpy RuntimeWarning
        x = np.sqrt(-1.0)
        # Line 8: Trigger runtime error
        arr = np.array([1, 2])
        return arr @ np.array([[1], [2], [3]]), 0.0
"""
    sol = Solution(code=runtime_err_code, name="BadMatrixOpt", description="Bad matrix option")
    scored = evaluator(sol)

    assert Evaluator.is_failure(scored.fitness)
    assert scored.fitness == Evaluator.RUNTIME_FAILURE_FITNESS
    # Option A check: relevant code line extracted
    assert "Relevant code lines from your algorithm:" in scored.feedback
    assert "line   8:" in scored.feedback

    # Option B check: problem context footer
    assert "Problem context: BBOB-8, dim=3" in scored.feedback

    # Option D check: numpy warning captured
    assert "NumPy/Runtime Warnings raised during execution" in scored.feedback
    assert "invalid value encountered in sqrt" in scored.feedback
