"""Callable collaborators used by the benchmark evaluation workflow."""

from collections.abc import Callable

from shared.domain.problem import BaseProblem
from shared.application.interfaces.candidate_executor import CandidateExecutor

BaselineRunner = Callable[[BaseProblem, int], tuple[float, float, int]]
BaselineRunnerResolver = Callable[[str], BaselineRunner]
ExecutorBuilder = Callable[[float], CandidateExecutor]
