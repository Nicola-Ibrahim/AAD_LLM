"""Unit tests for domain-owned candidate scoring rules."""

import math

from evolution.domain.services.algorithm_scoring import (
    AlgorithmScoringService,
    FailureKind,
)


def test_success_uses_objective_gap_and_clamps_roundoff():
    result = AlgorithmScoringService.success(clean_objective=12.5, true_optimum=10.0)
    assert result.objective_gap == 2.5
    assert result.fitness == -2.5
    assert AlgorithmScoringService.objective_gap(9.999999999, 10.0) == 0.0


def test_failure_categories_keep_distinct_penalties():
    scores = [
        AlgorithmScoringService.failure_score(kind)
        for kind in (FailureKind.EXECUTION, FailureKind.RUNTIME, FailureKind.TIMEOUT)
    ]
    assert len(set(scores)) == 3
    assert all(AlgorithmScoringService.is_failure(score) for score in scores)
    assert AlgorithmScoringService.is_failure(math.nan)
    assert not AlgorithmScoringService.is_failure(-10.0)
