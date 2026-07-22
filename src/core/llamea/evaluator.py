import time
import traceback
from typing import Any
import numpy as np
from llamea import Solution
from core.problems.bbob import BBOBProblem
from func_timeout import FunctionTimedOut
from core.llamea.executor import AlgorithmExecutor
from core.schema import (
    IterationMetadata,
    ExecutionProfile,
    FitnessMetrics,
    CodeMetrics,
    ErrorProfile,
    ConvergenceProfile,
    ProblemProfile,
)
from infra.storage.base import ExperimentRepository
from infra.storage.filesystem.code import CodeRepository


class Evaluator:
    """
    LLaMEA-compatible evaluator for noisy BBOB optimization problems.

    This class is called by the LLaMEA framework to evaluate candidate search
    algorithms. It performs a single execution run of the algorithm on a
    noisy BBOB problem instance under timeout protection, records the clean
    convergence trajectory locally, calculates the anytime AOCC score, and
    assigns the fitness score to the candidate solution.
    """

    def __init__(
        self,
        problem: BBOBProblem,
        db_repo: ExperimentRepository,
        code_repo: CodeRepository,
        budget: int = 1000,
        timeout_seconds: float = 10.0,
        noise_std: float = 0.0,
        run_id: int = 1,
        experiment_meta: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the evaluator.

        Args:
            problem: Fully-configured BBOB problem instance.
            db_repo: ExperimentRepository to persist incremental checkpoint iterations.
            code_repo: CodeRepository to persist algorithm source code per iteration.
            budget: Maximum allowed objective function evaluations passed to the algorithm
                as a stopping criterion (analogous to a convergence threshold in gradient
                descent), by default 1000. It is NOT used for multi-run comparison or luck checking.
            timeout_seconds: Maximum wall-clock execution time allowed for one algorithm run,
                by default 10.0.
            noise_std: Standard deviation of noise to apply during evaluation, by default 0.0.
            run_id: Unique run execution identifier, by default 1.
            experiment_meta: Metadata about the active experiment, by default None.
        """
        self._problem = problem
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._budget = budget
        self._timeout_seconds = timeout_seconds
        self._noise_std = noise_std
        self._run_id = run_id
        self._experiment_meta = experiment_meta or {}
        self._executor = AlgorithmExecutor(timeout_seconds=self._timeout_seconds)
        self._current_iteration = 0

    @property
    def problem_profile(self) -> ProblemProfile:
        """Expose the configured BBOB problem profile."""
        return ProblemProfile(
            problem_id=self._problem.problem_id,
            dim=self._problem.dim,
            noise_std=self._noise_std,
            instance_id=self._problem.instance_id,
            true_optimum=self._problem.true_optimum,
        )

    def _calculate_fitness_and_feedback(
        self,
        algorithm_returned_fitness: float,
        algorithm_name: str,
        runtime_seconds: float,
        evaluations_used: int,
        code_lines: int,
        code_length: int,
        llm_generation_time: float | None = None,
    ) -> tuple[float, str, IterationMetadata]:
        """
        Compute final error, fitness score, feedback message, and metadata object.
        """
        true_optimum = self._problem.true_optimum
        final_error = abs(algorithm_returned_fitness - true_optimum)

        feedback = (
            f"The algorithm achieved a final error of {final_error:.4f} from the true optimum ({true_optimum:.4f}) "
            f"on BBOB Problem {self._problem.problem_id} (additive noise std: {self._noise_std}). "
            "Improve convergence speed and resilience to minimize the final error."
        )

        budget_consumed_pct = (evaluations_used / self._budget * 100) if self._budget > 0 else 0.0
        relative_error = (final_error / abs(true_optimum)) if true_optimum != 0.0 else final_error
        evals_per_second = (evaluations_used / runtime_seconds) if runtime_seconds > 0.0 else 0.0
        error_per_evaluation = (final_error / evaluations_used) if evaluations_used > 0 else None
        converged = final_error < 1e-6

        metadata = IterationMetadata(
            algorithm_name=algorithm_name,
            execution=ExecutionProfile(
                timed_out=False,
                runtime_seconds=runtime_seconds,
                llm_generation_time=llm_generation_time,
                evaluations_used=evaluations_used,
                budget_consumed_pct=budget_consumed_pct,
                evals_per_second=evals_per_second,
            ),
            fitness=FitnessMetrics(
                raw_fitness=algorithm_returned_fitness,
                final_error=final_error,
                relative_error=relative_error,
                error_per_evaluation=error_per_evaluation,
            ),
            code=CodeMetrics(
                code_lines=code_lines,
                code_length=code_length,
                code_path=None,
            ),
            error=ErrorProfile(
                error_type=None,
                error_message=None,
                error_traceback=None,
            ),
            convergence=ConvergenceProfile(
                converged=converged,
                convergence_threshold=1e-6,
            ),
        )

        # LLaMEA expects a fitness score where higher is better.
        # We negate the final_error so that an error of 0 is the max (0.0), and larger errors are more negative.
        fitness_score = -final_error

        return fitness_score, feedback, metadata

    def _noisy_objective_function(self, x: np.ndarray) -> float:
        """Wrap the problem call to inject noise, returning only the noisy scalar.

        BBOBProblem.__call__(x, noise_std=s) returns a dict like
        {0.0: clean_val, s: noisy_val}. We extract the noisy value by
        looking up `noise_std` as the key; if there's any float precision
        drift we fall back to the first non-zero-key value in the dict.
        """
        res = self._problem(x, noise_std=self._noise_std)
        if isinstance(res, dict):
            # Primary lookup: exact key match
            if self._noise_std in res:
                return res[self._noise_std]
            # Fallback: return the value for the first non-clean (non-zero) key
            for k, v in res.items():
                if k != 0.0:
                    return v
            # Last resort: return clean value
            return res.get(0.0, float("inf"))
        return float(res)

    def _parse_generation_latency(self, solution: Solution) -> float | None:
        """Extract LLM generation time from solution metadata if available."""
        if hasattr(solution, "metadata") and isinstance(solution.metadata, dict):
            return solution.metadata.get("llm_generation_time")
        return None

    def _run_and_score_algorithm(
        self,
        solution: Solution,
        start_time: float,
        code_lines: int,
        code_length: int,
        llm_gen_time: float | None,
    ) -> tuple[float, str, IterationMetadata]:
        """Compile, execute algorithm run with exception handling, and return metrics/feedback."""
        problem_fn = self._noisy_objective_function if self._noise_std > 0.0 else self._problem
        try:
            algorithm_returned_fitness = self._executor.execute_algorithm(
                code=solution.code,
                name=solution.name,
                dim=self._problem.dim,
                problem=problem_fn,
                budget=self._budget,
            )
            elapsed_time = time.perf_counter() - start_time
            evals_used = self._problem._clean_problem.state.evaluations

            return self._calculate_fitness_and_feedback(
                algorithm_returned_fitness,
                solution.name,
                elapsed_time,
                evals_used,
                code_lines,
                code_length,
                llm_generation_time=llm_gen_time,
            )
        except (Exception, FunctionTimedOut) as error:
            return self._score_failed_algorithm(
                error, solution.name, start_time, code_lines, code_length, llm_gen_time
            )

    def _score_failed_algorithm(
        self,
        error: Exception | FunctionTimedOut,
        solution_name: str,
        start_time: float,
        code_lines: int,
        code_length: int,
        llm_gen_time: float | None,
    ) -> tuple[float, str, IterationMetadata]:
        """Handle execution timeout or runtime error, generating failure feedback and metadata."""
        elapsed_time = time.perf_counter() - start_time
        evals_used = self._problem._clean_problem.state.evaluations
        is_timeout = isinstance(error, FunctionTimedOut)

        if is_timeout:
            feedback = (
                f"Execution failed: Your algorithm exceeded the {self._timeout_seconds}-second time limit. "
                "Please optimize your loops and make the code more efficient."
            )
        else:
            feedback = (
                "Execution failed with the following Python error:\n"
                f"{traceback.format_exc()}\n"
                "Please fix the bugs."
            )

        metadata = self._build_error_metadata(
            algorithm_name=solution_name,
            elapsed_time=elapsed_time,
            evals_used=evals_used,
            code_lines=code_lines,
            code_length=code_length,
            llm_gen_time=llm_gen_time,
            is_timeout=is_timeout,
            error=error,
        )

        return float("-inf"), feedback, metadata

    def _build_error_metadata(
        self,
        algorithm_name: str,
        elapsed_time: float,
        evals_used: int,
        code_lines: int,
        code_length: int,
        llm_gen_time: float | None,
        is_timeout: bool,
        error: Exception,
    ) -> IterationMetadata:
        """Construct an IterationMetadata object for failed algorithm executions."""
        budget_consumed_pct = (evals_used / self._budget * 100) if self._budget > 0 else 0.0
        evals_per_second = (evals_used / elapsed_time) if elapsed_time > 0.0 else 0.0
        error_traceback = None if is_timeout else traceback.format_exc()

        return IterationMetadata(
            algorithm_name=algorithm_name,
            execution=ExecutionProfile(
                timed_out=is_timeout,
                runtime_seconds=elapsed_time,
                llm_generation_time=llm_gen_time,
                evaluations_used=evals_used,
                budget_consumed_pct=budget_consumed_pct,
                evals_per_second=evals_per_second,
            ),
            fitness=FitnessMetrics(
                raw_fitness=None,
                final_error=None,
                relative_error=None,
                error_per_evaluation=None,
            ),
            code=CodeMetrics(
                code_lines=code_lines,
                code_length=code_length,
                code_path=None,
            ),
            error=ErrorProfile(
                error_type=type(error).__name__,
                error_message=str(error),
                error_traceback=error_traceback,
            ),
            convergence=ConvergenceProfile(
                converged=False,
                convergence_threshold=1e-6,
            ),
        )

    def _checkpoint_iteration(self, solution: Solution, metadata: IterationMetadata) -> None:
        """Record iteration count, save code file, and persist metadata to JSONL checkpoint."""
        self._current_iteration += 1
        metadata.iteration = self._current_iteration
        mode = self._experiment_meta.get("mode", "noisy" if self._noise_std > 0.0 else "clean")

        # 1. Save candidate code file immediately
        if solution.code:
            code_path = self._code_repo.save_code(
                code=solution.code,
                iteration_num=self._current_iteration,
                problem=self.problem_profile,
                mode=mode,
                llm_name=self._experiment_meta.get("llm_name", "unknown"),
                run_id=self._run_id,
            )
            metadata.code.code_path = str(code_path)

        # 2. Append complete iteration metadata to JSONL checkpoint
        self._db_repo.append_iteration(
            problem_id=self._problem.problem_id,
            dim=self._problem.dim,
            mode=mode,
            run_id=self._run_id,
            metadata=metadata,
            experiment_meta=self._experiment_meta,
        )

    def __call__(self, solution: Solution, explogger: Any | None = None) -> Solution:
        """Execute and score a candidate optimization algorithm solution.

        Args:
            solution: The LLaMEA candidate solution containing its source code and name.
            explogger: Framework-level experiment logger, by default None.

        Returns:
            Solution: The modified solution object populated with fitness scores and feedback.
        """
        code_lines = len(solution.code.splitlines())
        code_length = len(solution.code)
        llm_gen_time = self._parse_generation_latency(solution)

        self._problem.reset()
        start_time = time.perf_counter()

        fitness_score, feedback, metadata = self._run_and_score_algorithm(
            solution, start_time, code_lines, code_length, llm_gen_time
        )

        solution.set_scores(fitness_score, feedback)
        solution.metadata = metadata
        self._checkpoint_iteration(solution, metadata)

        return solution

    def __getstate__(self) -> dict[str, Any]:
        # Exclude unpicklable C++ object wrappers (executor) and DB repos for joblib/pickle state logging.
        # problem is picklable since BBOBProblem implements its own self-healing __getstate__/__setstate__.
        state = self.__dict__.copy()
        state["_executor"] = None
        state["_db_repo"] = None
        state["_code_repo"] = None
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        # Re-initialize the executor if needed
        self._executor = AlgorithmExecutor(timeout_seconds=self._timeout_seconds)
