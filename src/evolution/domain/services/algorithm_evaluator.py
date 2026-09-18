"""Domain Algorithm Evaluator Service.

Encapsulates scientific evaluation rules for synthesized optimization algorithms:
- Validating search space bounds and dimensionality.
- Ground-truth scoring on un-noised objective: y_clean = problem.eval_clean(best_x), error = |y_clean - y*|.
- Mapping error to fitness score (-error).
- Categorizing failure tiers (-4.0e8, -4.5e8, -5.0e8).
- Tracking consecutive failures and detecting stagnation.
"""

import math
import re
import time
import traceback
from dataclasses import dataclass, field

import numpy as np

from evolution.domain.interfaces.problem import BaseProblem
from evolution.domain.vos.evaluation_result import AlgorithmEvaluationResult
from evolution.domain.vos.iteration import IterationMetadata
from evolution.domain.vos.metrics import (
    Code,
    Convergence,
    Error,
    Execution,
    Fitness,
)
from shared.execution import AlgorithmExecutor, AlgorithmTimeoutException


@dataclass
class _AlgorithmExecutionContext:
    """Internal context encapsulating algorithm execution telemetry and outputs."""

    algorithm_name: str
    runtime_seconds: float
    code_lines: int
    code_length: int
    llm_generation_time: float = 0.0
    evaluations_used: int = 0
    algorithm_returned_fitness: float = 0.0
    best_x: np.ndarray | None = None
    candidate_code: str = ""
    captured_warnings: list[str] = field(default_factory=list)


class AlgorithmEvaluator:
    """Core domain evaluation service for synthesized optimization algorithms.

    Agnostic of framework (LLaMEA, EoH, FunSearch, Reflection). Evaluates candidate code
    against a BaseProblem instance and constructs an AlgorithmEvaluationResult.
    """

    FAILURE_FITNESS: float = -5.0e8
    RUNTIME_FAILURE_FITNESS: float = -4.5e8
    TIMEOUT_FAILURE_FITNESS: float = -4.0e8

    @classmethod
    def is_failure(cls, score: float) -> bool:
        """Returns True if the score represents any failure tier (crash, runtime, or timeout)."""
        return not math.isfinite(score) or score <= -4.0e8

    def __init__(
        self,
        problem: BaseProblem,
        budget: int = 1_000_000,
        timeout_seconds: float = 30.0,
        stagnation_threshold: int = 3,
        convergence_threshold: float = 1e-6,
        executor: AlgorithmExecutor | None = None,
    ) -> None:
        self._problem = problem
        self._budget = budget
        self._timeout_seconds = timeout_seconds
        self._stagnation_threshold = stagnation_threshold
        self._convergence_threshold = convergence_threshold
        self._executor = executor or AlgorithmExecutor(timeout_seconds=timeout_seconds)
        self._consecutive_failures = 0

    def evaluate(
        self,
        code: str,
        name: str = "Algorithm",
        llm_generation_time: float | None = None,
    ) -> AlgorithmEvaluationResult:
        """Executes and scores an optimization algorithm source code string.

        Args:
            code: Candidate algorithm source code.
            name: Optional algorithm name.
            llm_generation_time: Wall-clock time spent generating the code.

        Returns:
            AlgorithmEvaluationResult: Domain evaluation result containing fitness, error, and diagnostics.
        """
        code_lines = len(code.splitlines())
        code_length = len(code)

        self._problem.reset()
        start_time = time.perf_counter()

        problem_fn = (
            self._problem.get_objective_fn()
            if hasattr(self._problem, "get_objective_fn")
            else self._problem
        )
        try:
            best_x, algorithm_returned_fitness = self._executor.execute_algorithm(
                code=code,
                name=name,
                dim=self._problem.dim,
                problem=problem_fn,
                budget=self._budget,
            )
            runtime_seconds = time.perf_counter() - start_time
            evaluations_used = getattr(self._problem, "evaluations", 0)
            captured = list(getattr(self._executor, "last_captured_warnings", []))
            ctx = _AlgorithmExecutionContext(
                algorithm_name=name,
                runtime_seconds=runtime_seconds,
                code_lines=code_lines,
                code_length=code_length,
                llm_generation_time=llm_generation_time or 0.0,
                evaluations_used=evaluations_used,
                algorithm_returned_fitness=algorithm_returned_fitness,
                best_x=best_x,
                candidate_code=code,
                captured_warnings=captured,
            )
            fitness_score, final_error, metadata = self._calculate_success_result(
                ctx=ctx,
            )
            code_context = ""
            is_failure = False
            self._consecutive_failures = 0

        except Exception as error:
            runtime_seconds = time.perf_counter() - start_time
            evaluations_used = getattr(self._problem, "evaluations", 0)
            captured = list(getattr(self._executor, "last_captured_warnings", []))
            ctx = _AlgorithmExecutionContext(
                algorithm_name=name,
                runtime_seconds=runtime_seconds,
                code_lines=code_lines,
                code_length=code_length,
                llm_generation_time=llm_generation_time or 0.0,
                evaluations_used=evaluations_used,
                algorithm_returned_fitness=0.0,
                best_x=None,
                candidate_code=code,
                captured_warnings=captured,
            )
            fitness_score, metadata, code_context = self._calculate_failure_result(
                ctx=ctx,
                error=error,
            )
            final_error = None
            is_failure = True
            self._consecutive_failures += 1

        if not math.isfinite(fitness_score):
            fitness_score = self.FAILURE_FITNESS
            is_failure = True

        is_stagnated = False
        if self._consecutive_failures >= self._stagnation_threshold:
            self._consecutive_failures = 0
            is_stagnated = True

        return AlgorithmEvaluationResult(
            fitness_score=fitness_score,
            final_error=final_error,
            is_failure=is_failure,
            is_stagnated=is_stagnated,
            metadata=metadata,
            code_context=code_context,
            captured_warnings=ctx.captured_warnings,
        )

    def _resolve_clean_objective(
        self,
        best_x: np.ndarray | None,
        algorithm_returned_fitness: float,
    ) -> float:
        """Validate best_x dimension and bounds, re-evaluate on clean objective, and check finite return."""
        if best_x is not None:
            if len(best_x) != self._problem.dim:
                raise ValueError(
                    f"Returned best_x has dimension {len(best_x)}, expected problem dimension {self._problem.dim}."
                )
            if not self._problem.is_in_bounds(best_x):
                lb_val = (
                    self._problem.lower_bound[0] if hasattr(self._problem, "lower_bound") else -5.0
                )
                ub_val = (
                    self._problem.upper_bound[0] if hasattr(self._problem, "upper_bound") else 5.0
                )
                raise ValueError(
                    f"Returned best_x {best_x.tolist()} is outside search space bounds [{lb_val}, {ub_val}]. "
                    "Ensure your algorithm clips candidate solutions to domain bounds using problem.clip(x) or np.clip(x, lb, ub)."
                )
            clean_y = self._problem.eval_clean(best_x)
        else:
            clean_y = algorithm_returned_fitness

        if not math.isfinite(clean_y):
            raise ValueError(
                f"[INVALID RETURN] Algorithm returned a non-finite value ({clean_y}). "
                "Ensure __call__ returns a valid float — no NaN or inf."
            )

        return clean_y

    @staticmethod
    def extract_code_context(tb_str: str, candidate_code: str) -> str:
        """Extract lines of generated candidate code referenced in exception tracebacks."""
        if not candidate_code or not tb_str:
            return ""

        code_lines = candidate_code.splitlines()
        matches = re.findall(r'File "<string>", line (\d+)', tb_str) or re.findall(
            r'File "[^"]*<string>[^"]*", line (\d+)', tb_str
        )
        if not matches:
            return ""

        context_blocks = []
        seen_lines: set[int] = set()
        for line_str in matches:
            line_num = int(line_str)
            if line_num in seen_lines:
                continue
            seen_lines.add(line_num)

            idx = line_num - 1
            if 0 <= idx < len(code_lines):
                start = max(0, idx - 2)
                end = min(len(code_lines), idx + 3)
                snippet_lines = []
                for i in range(start, end):
                    prefix = "->" if i == idx else "  "
                    snippet_lines.append(f"  {prefix} line {i + 1:3d}: {code_lines[i]}")
                context_blocks.append("\n".join(snippet_lines))

        if not context_blocks:
            return ""

        return "\n---\n".join(context_blocks)

    def _build_success_metadata(
        self,
        ctx: _AlgorithmExecutionContext,
        final_error: float,
    ) -> IterationMetadata:
        """Construct IterationMetadata for a successful run."""
        true_optimum = self._problem.true_optimum
        budget_consumed_pct = (
            (ctx.evaluations_used / self._budget * 100) if self._budget > 0 else 0.0
        )
        relative_error = (final_error / abs(true_optimum)) if true_optimum != 0.0 else final_error
        evals_per_second = (
            (ctx.evaluations_used / ctx.runtime_seconds) if ctx.runtime_seconds > 0.0 else 0.0
        )
        error_per_evaluation = (
            (final_error / ctx.evaluations_used) if ctx.evaluations_used > 0 else None
        )

        return IterationMetadata(
            algorithm_name=ctx.algorithm_name,
            execution=Execution(
                timed_out=False,
                runtime_seconds=ctx.runtime_seconds,
                llm_generation_time=ctx.llm_generation_time,
                evaluations_used=ctx.evaluations_used,
                budget_consumed_pct=budget_consumed_pct,
                evals_per_second=evals_per_second,
            ),
            fitness=Fitness(
                raw_fitness=ctx.algorithm_returned_fitness,
                final_error=final_error,
                relative_error=relative_error,
                error_per_evaluation=error_per_evaluation,
            ),
            code=Code(
                code_lines=ctx.code_lines,
                code_length=ctx.code_length,
                code_path=None,
            ),
            error=Error(
                error_type=None,
                error_message=None,
                error_traceback=None,
            ),
            convergence=Convergence.evaluate(final_error, self._convergence_threshold),
        )

    def _calculate_success_result(
        self,
        ctx: _AlgorithmExecutionContext,
    ) -> tuple[float, float, IterationMetadata]:
        """Compute final error, fitness score, and metadata object."""
        true_optimum = self._problem.true_optimum
        clean_y = self._resolve_clean_objective(ctx.best_x, ctx.algorithm_returned_fitness)
        final_error = abs(clean_y - true_optimum)
        metadata = self._build_success_metadata(ctx, final_error)
        fitness_score = -final_error

        return fitness_score, final_error, metadata

    def _calculate_failure_result(
        self,
        ctx: _AlgorithmExecutionContext,
        error: Exception,
    ) -> tuple[float, IterationMetadata, str]:
        """Handle execution timeout or runtime error, determining failure tier, metadata, and code context."""
        is_timeout = isinstance(error, AlgorithmTimeoutException)

        if is_timeout:
            internal_score = self.TIMEOUT_FAILURE_FITNESS
        elif isinstance(
            error,
            (ValueError, TypeError, ZeroDivisionError, OverflowError, FloatingPointError),
        ):
            internal_score = self.RUNTIME_FAILURE_FITNESS
        else:
            internal_score = self.FAILURE_FITNESS

        tb_str = "" if is_timeout else traceback.format_exc()
        code_context = self.extract_code_context(tb_str, ctx.candidate_code)

        metadata = self._build_failure_metadata(
            ctx=ctx,
            error=error,
            is_timeout=is_timeout,
        )

        return internal_score, metadata, code_context

    def _build_failure_metadata(
        self,
        ctx: _AlgorithmExecutionContext,
        error: Exception,
        is_timeout: bool,
    ) -> IterationMetadata:
        """Construct IterationMetadata for a failed run."""
        error_traceback = None if is_timeout else traceback.format_exc()
        budget_consumed_pct = (
            (ctx.evaluations_used / self._budget * 100) if self._budget > 0 else 0.0
        )
        evals_per_second = (
            (ctx.evaluations_used / ctx.runtime_seconds) if ctx.runtime_seconds > 0.0 else 0.0
        )

        return IterationMetadata(
            algorithm_name=ctx.algorithm_name,
            execution=Execution(
                timed_out=is_timeout,
                runtime_seconds=ctx.runtime_seconds,
                llm_generation_time=ctx.llm_generation_time,
                evaluations_used=ctx.evaluations_used,
                budget_consumed_pct=budget_consumed_pct,
                evals_per_second=evals_per_second,
            ),
            fitness=Fitness(
                raw_fitness=None,
                final_error=None,
                relative_error=None,
                error_per_evaluation=None,
            ),
            code=Code(
                code_lines=ctx.code_lines,
                code_length=ctx.code_length,
                code_path=None,
            ),
            error=Error(
                error_type=type(error).__name__,
                error_message=str(error),
                error_traceback=error_traceback,
            ),
            convergence=Convergence.evaluate(None, self._convergence_threshold),
        )
