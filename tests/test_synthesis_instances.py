"""Exploratory instance schedules must not change scoring or add incumbent runs."""

import pickle
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from llamea import Solution

from evolution.application.synthesis.evaluate_candidate import CandidateEvaluationService
from evolution.application.synthesis.models import CandidateInstance, SessionConfig
from evolution.infra.engines.llamea.evaluator import Evaluator
from evolution.infra.engines.llamea.runner import LLaMEASession, _InstanceScheduledLLaMEA
from evolution.infra.storage.code.repository import CodeRepository
from evolution.infra.storage.synthesis_config.repository import SynthesisConfigRepository
from shared.domain.noise import HeteroscedasticNoiseStrategy
from shared.infra.problems.bbob import BBOBProblem


def evaluator_for(tmp_path: Path, *, policy: str = "per_iteration", initial: int = 0):
    problem = BBOBProblem(15, 10, HeteroscedasticNoiseStrategy(0.1), instance_id=1, seed=43)
    executor = MagicMock()
    executor.last_captured_warnings = []
    calls = []

    def execute(**kwargs):
        objective = kwargs["problem"]
        calls.append((objective.instance_id, objective.true_optimum))
        x = objective.optimum_x
        return x, objective(x)

    executor.execute_algorithm.side_effect = execute
    config = SessionConfig(iterations=10, budget=100, instance_policy=policy)
    service = CandidateEvaluationService(problem=problem, executor=executor, budget=config.budget)
    evaluator = Evaluator(
        problem=problem,
        db_repo=MagicMock(),
        code_repo=CodeRepository(tmp_path),
        experiment_id=1,
        config=config,
        candidate_evaluation_service=service,
        initial_iteration=initial,
    )
    evaluator.logger = MagicMock()
    return evaluator, calls, executor


def candidate() -> Solution:
    return Solution(code="class Candidate: pass", name="Candidate")


def test_each_candidate_uses_new_instance_and_its_own_optimum(tmp_path):
    evaluator, calls, executor = evaluator_for(tmp_path)
    for iteration in range(1, 11):
        solution = evaluator(candidate())
        assert solution.fitness == pytest.approx(0.0)
        assert solution.metadata["instance_id"] == iteration
        context = evaluator._code_repo.load_candidate_instance(1, iteration)
        assert context.instance_id == iteration
        assert context.noise_seed == 42 + iteration
        assert context.true_optimum == calls[-1][1]
        assert context.budget == 100
    assert [instance for instance, _ in calls] == list(range(1, 11))
    assert len(set(optimum for _, optimum in calls)) > 1
    assert executor.execute_algorithm.call_count == 10
    with pytest.raises(ValueError, match="exhausted"):
        evaluator(candidate())
    assert executor.execute_algorithm.call_count == 10


def test_fixed_policy_keeps_previous_instance_behavior(tmp_path):
    evaluator, calls, _ = evaluator_for(tmp_path, policy="fixed")
    evaluator(candidate())
    evaluator(candidate())
    assert [instance for instance, _ in calls] == [1, 1]
    assert not list(tmp_path.rglob("*.instance.json"))


def test_resume_uses_next_instance_not_instance_one(tmp_path):
    evaluator, calls, _ = evaluator_for(tmp_path, initial=4)
    evaluator(candidate())
    assert calls[0][0] == 5
    assert evaluator._code_repo.load_candidate_instance(1, 5).instance_id == 5


def test_failures_advance_instances_and_preserve_stagnation(tmp_path):
    evaluator, _, executor = evaluator_for(tmp_path)
    executor.execute_algorithm.side_effect = RuntimeError("failed candidate")
    for iteration in range(1, 4):
        evaluator(candidate())
        assert evaluator._code_repo.load_candidate_instance(1, iteration).instance_id == iteration
    assert executor.execute_algorithm.call_count == 3
    evaluator.logger.stagnation_warning.assert_called_once()


def test_pickle_retains_instance_schedule(tmp_path, db_session_factory):
    from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository

    evaluator, _, _ = evaluator_for(tmp_path, initial=3)
    evaluator._db_repo = SQLiteSynthesisRepository(db_session_factory)
    restored = pickle.loads(pickle.dumps(evaluator))
    assert restored._first_instance_id == 1
    assert restored._current_iteration == 3
    assert restored._config.instance_policy == "per_iteration"


def test_empty_failed_code_still_records_its_instance(tmp_path):
    evaluator, _, executor = evaluator_for(tmp_path)
    executor.execute_algorithm.side_effect = RuntimeError("empty candidate")
    evaluator(Solution(code="", name="Empty"))
    assert evaluator._code_repo.load_candidate_instance(1, 1).instance_id == 1


def test_old_fixed_session_cannot_be_resumed_as_varying(tmp_path):
    session = object.__new__(LLaMEASession)
    session._config = SessionConfig(instance_policy="per_iteration")
    session._initial_iteration = 3
    session._restart = False
    session._experiment_id = 1
    session._code_repo = CodeRepository(tmp_path)
    with pytest.raises(ValueError, match="Cannot resume an old fixed-instance"):
        session.run()


def test_candidate_context_round_trip_and_experiment_cleanup(tmp_path):
    store = CodeRepository(tmp_path)
    context = CandidateInstance(
        iteration=2, instance_id=2, noise_seed=44, true_optimum=394.48, budget=100
    )
    store.save_candidate_instance(1, context)
    assert store.load_candidate_instance(1, 2) == context
    assert not list(tmp_path.rglob("*.tmp"))
    store.clear_experiment(1)
    assert not (tmp_path / "experiment_1").exists()


def test_checkpoint_parent_does_not_consume_the_next_instance():
    engine = object.__new__(_InstanceScheduledLLaMEA)
    parent = candidate()
    engine.population = [parent]
    engine.run_history = [parent]
    engine.generation = 1
    engine.initialize()
    assert engine.run_history == [parent]
    assert engine.generation == 1


def test_current_schedule_is_disjoint_from_benchmark_instances():
    from benchmarking.infra.storage.benchmark_config_repository import BenchmarkConfigRepository

    synthesis = SynthesisConfigRepository().load_config()
    benchmark = BenchmarkConfigRepository().load_config()
    assert synthesis.instance_policy == "per_iteration"
    assert synthesis.iterations == 10
    assert synthesis.to_session_config_dict()["instance_policy"] == "per_iteration"
    assert not set(range(1, synthesis.iterations + 1)) & {i for i, _ in benchmark.trial_schedule}
    assert benchmark.first_instance_id == 11
    assert synthesis.budget == benchmark.budget == 100000
