"""Unit tests for ProcessWorkerPool concurrency infrastructure."""

import pytest

from evolution.application.exceptions import OrchestrationError
from evolution.infra.concurrency.process_worker_pool import ProcessWorkerPool


def _square(x: int) -> int:
    return x * x


def _failing_fn(x: int) -> int:
    if x == 2:
        raise ValueError(f"Failed on {x}")
    return x * 10


def test_runner_executes_tasks():
    runner = ProcessWorkerPool(max_workers=2)
    items = [1, 2, 3, 4]
    results = runner.execute(fn=_square, items=items, key_fn=str)

    assert results == {"1": 1, "2": 4, "3": 9, "4": 16}


def test_runner_empty_items():
    runner = ProcessWorkerPool()
    results = runner.execute(fn=_square, items=[], key_fn=str)
    assert results == {}


def test_runner_propagates_orchestration_error():
    runner = ProcessWorkerPool(max_workers=2)
    items = [1, 2, 3]

    with pytest.raises(OrchestrationError) as exc_info:
        runner.execute(fn=_failing_fn, items=items, key_fn=str)

    errors = exc_info.value.errors
    assert "2" in errors
    assert isinstance(errors["2"], ValueError)
    assert "Failed on 2" in str(errors["2"])
