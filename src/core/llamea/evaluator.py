import time
import traceback
from typing import Any
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
from infra.storage.code_store.code import CodeRepository


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
        experiment_id: int = 1,
        experiment_meta: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the evaluator.

        Args:
            problem: Fully-configured BBOB problem instance.
            db_repo: ExperimentRepository to persist incremental iteration records.
            code_repo: CodeRepository to persist algorithm source code per iteration.
            budget: Maximum allowed objective function evaluations passed to the algorithm
                as a stopping criterion (analogous to a convergence threshold in gradient
                descent), by default 1000. It is NOT used for multi-run comparison or luck checking.
            timeout_seconds: Maximum wall-clock execution time allowed for one algorithm run,
                by default 10.0.
            noise_std: Standard deviation of noise to apply during evaluation, by default 0.0.
            experiment_id: Globally unique experiment primary key, by default 1.
            experiment_meta: Metadata about the active experiment, by default None.
        """
        self._problem = problem
        self._db_repo = db_repo
        self._code_repo = code_repo
        self._budget = budget
        self._timeout_seconds = timeout_seconds
        self._noise_std = noise_std
        self._experiment_id = experiment_id
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
        error_per_evaluation = (
            (final_error / evaluations_used) if evaluations_used > 0 else float("inf")
        )
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

    def _run_and_score_algorithm(
        self,
        solution: Solution,
        start_time: float,
        code_lines: int,
        code_length: int,
        llm_gen_time: float | None,
    ) -> tuple[float, str, IterationMetadata]:
        """Compile, execute algorithm run with exception handling, and return metrics/feedback."""
        problem_fn = self._problem.get_objective_fn(self._noise_std)
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
                raw_fitness=float("inf"),
                final_error=float("inf"),
                relative_error=float("inf"),
                error_per_evaluation=float("inf"),
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

    def _persist_iteration(self, solution: Solution, metadata: IterationMetadata) -> None:
        """Record iteration count, save code file, and persist metadata to database repo."""
        self._current_iteration += 1
        metadata.iteration = self._current_iteration

        # 1. Save candidate code file immediately
        if solution.code:
            code_path = self._code_repo.save_code(
                code=solution.code,
                iteration_num=self._current_iteration,
                experiment_id=self._experiment_id,
            )
            metadata.code.code_path = str(code_path)

        # 2. Append complete iteration metadata to database repo
        self._db_repo.append_iteration(
            experiment_id=self._experiment_id,
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
        llm_gen_time = solution.metadata.get("llm_generation_time")

        self._problem.reset()
        start_time = time.perf_counter()

        fitness_score, feedback, metadata = self._run_and_score_algorithm(
            solution, start_time, code_lines, code_length, llm_gen_time
        )

        solution.set_scores(fitness_score, feedback)
        solution.metadata = metadata
        self._persist_iteration(solution, metadata)

        return solution

    def __getstate__(self) -> dict[str, Any]:
        # Exclude unpicklable C++ executor wrapper only.
        # _db_repo and _code_repo are preserved: SQLiteExperimentRepository has its own
        # __getstate__/__setstate__ that safely strips the non-picklable session_factory.
        # Without them, warm-start resumes would have no db_repo and all iteration
        # persistence would silently stop.
        state = self.__dict__.copy()
        state["_executor"] = None
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        # Re-initialize the executor on resume.
        self._executor = AlgorithmExecutor(timeout_seconds=self._timeout_seconds)
        # If _db_repo or _code_repo are None after resume (e.g. from an old pickle),
        # we cannot recover them here — the session must re-attach them after warm_start.
        if self._db_repo is None:
            print(
                "[WARN] Evaluator resumed from pickle with _db_repo=None. "
                "Iteration persistence is DISABLED for this run. "
                "Call evaluator._db_repo = repo to re-attach."
            )
        if self._code_repo is None:
            print(
                "[WARN] Evaluator resumed from pickle with _code_repo=None. "
                "Code file saving is DISABLED for this run."
            )
