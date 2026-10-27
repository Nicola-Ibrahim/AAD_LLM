"""Regression tests for domain contracts, identities and observation semantics."""

import inspect

import numpy as np
import pytest
from pydantic import ValidationError

from benchmark.domain.enums.solver_kind import SolverKind
from benchmark.domain.services.ecdf import EcdfConvergenceEngine
from benchmark.domain.services.hypothesis import HypothesisTestingEngine
from benchmark.domain.services.reliability import ReliabilityEngine, search_success_rate
from benchmark.domain.services.transfer import TransferAnalysisEngine
from benchmark.domain.vos import BenchmarkCondition, BenchmarkDataset, RunTrace
from evolution.domain.entities import Experiment
from evolution.domain.enums import SynthesisMode
from evolution.domain.interfaces.synthesis_repository import SynthesisRepository
from evolution.domain.vos import (
    Code,
    Convergence,
    Error,
    Execution,
    Fitness,
    IterationMetadata,
    ProblemProfile,
)
from evolution.infra.storage.synthesis.repository import SQLiteSynthesisRepository
from shared.domain.scoring import objective_gap


def candidate(number: int, error: float, evaluations: int) -> IterationMetadata:
    return IterationMetadata(
        iteration=number,
        algorithm_name=f"candidate-{number}",
        execution=Execution(
            timed_out=False,
            runtime_seconds=1.0,
            evaluations_used=evaluations,
            budget_consumed_pct=100.0,
            evals_per_second=1.0,
        ),
        fitness=Fitness(raw_fitness=error, final_error=error),
        code=Code(code_lines=1, code_length=1),
        error=Error(),
        convergence=Convergence.evaluate(error),
    )


def experiment(**changes: object) -> Experiment:
    return Experiment(
        **{
            "experiment_id": 1,
            "problem": ProblemProfile(problem_id=1, dim=2, noise_std=0.0),
            "mode": SynthesisMode.EXPLICIT,
            "llm_name": "test-model",
            "budget": 100_000,
            "max_iterations": 10,
        }
        | changes
    )


def test_condition_keys_have_one_equivalence_and_hash_rule():
    left = BenchmarkCondition(dim=2, noise_std=0.0500004999, problem_id=1)
    right = BenchmarkCondition(dim=2, noise_std=0.0500005001, problem_id=1)
    assert left == right
    assert hash(left) == hash(right)
    assert {left: "same condition"}[right] == "same condition"
    for std in (0.0, 0.05, 0.1, 0.2):
        assert BenchmarkCondition(dim=2, noise_std=std, problem_id=1).noise_std == std


@pytest.mark.parametrize("noise", [float("inf"), float("nan"), -0.1])
def test_condition_rejects_invalid_noise(noise):
    with pytest.raises(ValidationError):
        BenchmarkCondition(dim=2, noise_std=noise, problem_id=1)


@pytest.mark.parametrize(
    "evaluations,errors",
    [
        ([1, 2], [1.0]),
        ([[1]], [[1.0]]),
        ([2, 1], [1.0, 0.1]),
        ([float("nan")], [1.0]),
        ([-1], [1.0]),
    ],
)
def test_malformed_trace_is_rejected_without_silent_repair(evaluations, errors):
    with pytest.raises(ValidationError):
        RunTrace(evaluations=np.asarray(evaluations), raw_objectives=np.asarray(errors))


def test_trace_arrays_are_detached_and_read_only_across_filtered_datasets():
    values = np.array([10.0, 1.0])
    trace = RunTrace(evaluations=np.array([1, 10]), raw_objectives=values)
    values[0] = 999.0
    assert trace.raw_objectives.tolist() == [10.0, 1.0]
    condition = BenchmarkCondition(dim=2, noise_std=0.0, problem_id=1)
    dataset = BenchmarkDataset()
    dataset.add_run(condition, "solver", trace)
    filtered = dataset.filter(dims=[2])
    with pytest.raises(ValueError, match="read-only"):
        filtered[condition]["solver"][0].raw_objectives[0] = 999.0
    filtered[condition]["solver"].clear()
    assert len(dataset[condition]["solver"]) == 1


@pytest.mark.parametrize(
    "change",
    [
        {"problem_id": 0},
        {"problem_id": 25},
        {"dim": 0},
        {"instance_id": 0},
        {"noise_std": -0.1},
        {"noise_std": float("nan")},
        {"true_optimum": float("inf")},
    ],
)
def test_problem_profile_enforces_scientific_configuration(change):
    with pytest.raises(ValidationError):
        ProblemProfile(**({"problem_id": 1, "dim": 2, "noise_std": 0.0} | change))


@pytest.mark.parametrize("changes", [{"budget": -1}, {"max_iterations": 0}, {"experiment_id": 0}])
def test_experiment_rejects_invalid_identity_and_execution_limits(changes):
    with pytest.raises(ValidationError):
        experiment(**changes)


def test_experiment_requires_an_immutable_database_identity():
    for identifier in (None, 0, -1):
        with pytest.raises(ValidationError):
            experiment(experiment_id=identifier)
    with pytest.raises(ValidationError):
        Experiment(
            problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0),
            mode=SynthesisMode.EXPLICIT,
            llm_name="test-model",
        )
    persisted = experiment()
    assert persisted.experiment_id == persisted.id == 1
    assert isinstance(persisted.started_at, str)
    with pytest.raises(ValidationError):
        persisted.id = 2


def test_experiment_lifecycle_is_explicit_and_historical_absence_is_preserved():
    summary = experiment(budget=None, max_iterations=None)
    assert summary.budget is None and summary.max_iterations is None
    with pytest.raises(ValidationError):
        summary.status = "anything"
    summary.complete()
    timestamp = summary.finished_at
    summary.complete()
    assert summary.finished_at == timestamp
    with pytest.raises(ValueError):
        summary.fail()
    with pytest.raises(ValueError):
        summary.record_iteration(candidate(1, 1.0, 10))
    failed = experiment()
    failed.fail()
    with pytest.raises(ValueError):
        failed.complete()


def test_synthesis_incumbent_preserves_first_exact_tie():
    summary = experiment()
    summary.record_iteration(candidate(1, 1.0, 100))
    summary.record_iteration(candidate(2, 1.0, 10))
    assert summary.incumbent.algorithm_name == summary.best_algorithm == "candidate-1"
    summary.record_iteration(candidate(3, 0.5, 100))
    assert summary.incumbent.algorithm_name == summary.best_algorithm == "candidate-3"


def test_repository_query_contract_and_required_execution_parameters(db_session_factory):
    repository: SynthesisRepository = SQLiteSynthesisRepository(db_session_factory)
    assert set(inspect.signature(SynthesisRepository.load).parameters) == set(
        inspect.signature(SQLiteSynthesisRepository.load).parameters
    )
    identifiers = []
    for noise in (0.0, 0.1):
        identifiers.append(
            repository.create_experiment(
                problem=ProblemProfile(problem_id=1, dim=2, noise_std=noise),
                mode=SynthesisMode.EXPLICIT,
                llm_name="filter-model",
                budget=100_000,
                max_iterations=10,
            )
        )
    assert [
        r.id
        for r in repository.load(llm_name="filter-model", noise_std=0.1, dim=2, status="running")
    ] == identifiers[1:]
    assert [r.id for r in repository.load(llm_name="filter-model", noise_std=0.0)] == identifiers[
        :1
    ]
    for signature in (
        SynthesisRepository.create_experiment,
        SQLiteSynthesisRepository.create_experiment,
    ):
        assert inspect.signature(signature).parameters["budget"].default is inspect.Parameter.empty
    with pytest.raises(ValidationError):
        repository.create_experiment(
            problem=ProblemProfile(problem_id=1, dim=2, noise_std=0.0),
            mode=SynthesisMode.EXPLICIT,
            llm_name="invalid",
            budget=-1,
            max_iterations=10,
        )
    assert not repository.load(llm_name="invalid")


def test_missing_trials_are_unavailable_but_executed_failures_count():
    grid = np.array([1, 10])
    ecdf = EcdfConvergenceEngine()
    reliability = ReliabilityEngine()
    assert np.isnan(ecdf.compute_ecdf([], grid, np.array([1e-8]))).all()
    assert all(np.isnan(curve).all() for curve in reliability.compute_attainment_band([], grid))
    assert np.isnan(search_success_rate([]))
    success = RunTrace(evaluations=grid, raw_objectives=np.array([1.0, 0.0]))
    failed = RunTrace(evaluations=np.array([]), raw_objectives=np.array([]))
    assert search_success_rate([success, failed]) == 0.5
    np.testing.assert_array_equal(
        reliability.compute_attainment_band([success, failed], grid)[0], [0.0, 0.5]
    )
    terminal = TransferAnalysisEngine.condition_table(
        [
            {
                "model": "model",
                "strategy": "baseline",
                "dim": 2,
                "problem_id": 1,
                "noise_std": 0.0,
                "clean_errors": [0.0, float("inf")],
            }
        ],
        expected_trials=2,
    )
    assert terminal.iloc[0]["Success Rate"] == 0.5
    assert terminal.iloc[0]["Complete"]


def test_solver_origin_does_not_depend_on_model_name():
    condition = BenchmarkCondition(dim=2, noise_std=0.0, problem_id=1)
    dataset = BenchmarkDataset()
    for solver, values in (("Qwen / baseline", [1.0, 2.0, 3.0]), ("CMA-ES", [4.0, 5.0, 6.0])):
        for value in values:
            dataset.add_run(
                condition,
                solver,
                RunTrace(evaluations=np.array([1]), raw_objectives=np.array([value])),
            )
    kinds = {"Qwen / baseline": SolverKind.GENERATED, "CMA-ES": SolverKind.CLASSICAL}
    pairwise = HypothesisTestingEngine().run_pairwise_fdr(dataset, solver_kinds=kinds)
    assert pairwise.iloc[0]["Comparison Tier"] == "Tier 2 (LLaMEA vs. Classical)"
    with pytest.raises(ValueError, match="Missing solver origins"):
        HypothesisTestingEngine().run_pairwise_fdr(dataset, solver_kinds={})


@pytest.mark.parametrize(
    "clean,optimum", [(float("nan"), 0.0), (float("inf"), 0.0), (1.0, float("nan"))]
)
def test_nonfinite_objectives_cannot_become_zero_gap(clean, optimum):
    with pytest.raises(ValueError):
        objective_gap(clean, optimum)
