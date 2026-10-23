"""Candidate setup executes once and remains inside the timeout boundary."""

import time

import pytest

from shared.infra.execution.compiler import CodeCompiler
from shared.infra.execution.exceptions import AlgorithmTimeoutException
from shared.infra.execution.executor import AlgorithmExecutor


def test_constructor_runs_once() -> None:
    algorithm = CodeCompiler().compile(
        """class Candidate:
    constructions = 0
    def __init__(self):
        type(self).constructions += 1
    def __call__(self, problem, budget):
        return [0.0, 0.0], 0.0
""",
        "Candidate",
        2,
    )
    assert type(algorithm).constructions == 1


@pytest.mark.parametrize("parameter", ["dim", "*, dim", "dim=3", "*, dim=3", "dim=3, /"])
def test_required_dimension_uses_actual_problem_dimension(parameter: str) -> None:
    algorithm = CodeCompiler().compile(
        f"""class Candidate:
    def __init__(self, {parameter}):
        if dim != 10:
            raise ValueError("This candidate requires 10D")
        self.dim = dim
    def __call__(self, problem, budget):
        return [0.0] * self.dim, 0.0
""",
        "Candidate",
        10,
    )
    assert algorithm.dim == 10


def test_internal_constructor_type_error_is_not_retried() -> None:
    with pytest.raises(TypeError, match="internal constructor failure"):
        CodeCompiler().compile(
            """class Candidate:
    def __init__(self, dim=2):
        raise TypeError("internal constructor failure")
    def __call__(self, problem, budget):
        return [0.0, 0.0], 0.0
""",
            "Candidate",
            2,
        )


@pytest.mark.parametrize("stage", ["module", "constructor", "optimizer"])
def test_python_loop_times_out_during_any_execution_stage(stage: str) -> None:
    module = "while True:\n    pass\n" if stage == "module" else ""
    initialization = "while True: pass" if stage == "constructor" else "pass"
    execution = "while True: pass" if stage == "optimizer" else "return [0.0, 0.0], 0.0"
    code = f"""{module}
class Candidate:
    def __init__(self):
        {initialization}
    def __call__(self, problem, budget):
        {execution}
"""
    started = time.perf_counter()
    with pytest.raises(AlgorithmTimeoutException):
        AlgorithmExecutor(timeout_seconds=0.05).execute_algorithm(
            code,
            "Candidate",
            2,
            lambda point: 0.0,
            10,
        )
    assert time.perf_counter() - started < 3.0
