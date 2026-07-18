import time
import traceback
import json
from pathlib import Path
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
        budget: int = 1000,
        timeout_seconds: float = 10.0,
        noise_std: float = 0.0,
        run_id: int = 1,
        json_checkpoint_path: Path | str | None = None,
        experiment_meta: dict | None = None,
    ):
        """
        Initialize the evaluator.

        Parameters
        ----------
        problem : BBOBProblem
            Fully-configured BBOB problem instance.
        budget : int, optional
            Maximum allowed objective function evaluations passed to the algorithm
            as a stopping criterion (analogous to a convergence threshold in gradient
            descent), by default 1000. It is NOT used for multi-run comparison or luck checking.
        timeout_seconds : float, optional
            Maximum wall-clock execution time allowed for one algorithm run,
            by default 10.0.
        noise_std : float, optional
            Standard deviation of noise to apply during evaluation, by default 0.0.
        """
        self.problem = problem
        self.budget = budget
        self.timeout_seconds = timeout_seconds
        self.noise_std = noise_std
        self.run_id = run_id
        self.json_checkpoint_path = Path(json_checkpoint_path) if json_checkpoint_path else None
        self.experiment_meta = experiment_meta or {}
        self.executor = AlgorithmExecutor(timeout_seconds=self.timeout_seconds)
        self._current_iteration = 0
        self._write_checkpoint_header()

    def _write_checkpoint_header(self) -> None:
        """Write an empty envelope JSON so the file is self-describing from the start."""
        if self.json_checkpoint_path is None:
            return
        path = self.json_checkpoint_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return  # don't overwrite an existing checkpoint (crash recovery scenario)
        envelope = {"experiment": self.experiment_meta, "iterations": []}
        tmp = path.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(envelope, f, indent=2)
        tmp.replace(path)

    def _append_to_json_checkpoint(self, metadata: IterationMetadata) -> None:
        """Atomically appends one IterationMetadata record to the envelope checkpoint JSON."""
        if self.json_checkpoint_path is None:
            return
        path = self.json_checkpoint_path
        try:
            with path.open("r") as f:
                envelope = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Corrupt file — rebuild from header and current record only
            envelope = {"experiment": self.experiment_meta, "iterations": []}
        envelope["iterations"].append(metadata.to_json_dict())
        tmp = path.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(envelope, f, indent=2)
        tmp.replace(path)  # atomic rename on Linux/macOS

    @property
    def problem_profile(self) -> ProblemProfile:
        """Expose the configured BBOB problem profile."""
        return ProblemProfile(
            problem_id=self.problem.problem_id,
            dim=self.problem.dim,
            noise_std=self.noise_std,
            instance_id=self.problem.instance_id,
            true_optimum=self.problem.true_optimum,
        )

    def _compute_metrics_and_feedback(
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
        true_optimum = self.problem.true_optimum
        final_error = abs(algorithm_returned_fitness - true_optimum)

        feedback = (
            f"The algorithm achieved a final error of {final_error:.4f} from the true optimum ({true_optimum:.4f}) "
            f"on BBOB Problem {self.problem.problem_id} (additive noise std: {self.noise_std}). "
            "Improve convergence speed and resilience to minimize the final error."
        )

        budget_consumed_pct = (evaluations_used / self.budget * 100) if self.budget > 0 else 0.0
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

    def _noisy_problem_fn(self, x: np.ndarray) -> float:
        """Wrap the problem call to inject noise, returning only the noisy scalar.

        BBOBProblem.__call__(x, noise_std=s) returns a dict like
        {0.0: clean_val, s: noisy_val}. We extract the noisy value by
        looking up `noise_std` as the key; if there's any float precision
        drift we fall back to the first non-zero-key value in the dict.
        """
        res = self.problem(x, noise_std=self.noise_std)
        if isinstance(res, dict):
            # Primary lookup: exact key match
            if self.noise_std in res:
                return res[self.noise_std]
            # Fallback: return the value for the first non-clean (non-zero) key
            for k, v in res.items():
                if k != 0.0:
                    return v
            # Last resort: return clean value
            return res.get(0.0, float("inf"))
        return float(res)

    def __call__(self, solution: Solution, explogger: Any | None = None) -> Solution:
        """
        Execute and score a candidate optimization algorithm solution.

        Parameters
        ----------
        solution : Solution
            The LLaMEA candidate solution containing its source code and name.
        explogger : Any | None, optional
            Framework-level experiment logger, by default None.

        Returns
        -------
        solution : Solution
            The modified solution object populated with fitness scores and feedback.
        """
        # Compute static code complexity metrics
        code_lines = len(solution.code.splitlines())
        code_length = len(solution.code)

        # Get LLM generation time from solution metadata if available
        llm_gen_time = None
        if hasattr(solution, "metadata") and isinstance(solution.metadata, dict):
            llm_gen_time = solution.metadata.get("llm_generation_time")

        # Reset evaluations counter to ensure we start at 0 for this candidate algorithm run
        self.problem.reset()
        start_time = time.perf_counter()
        try:
            # --- 1. Compile & Execute candidate run with timeout protection ---
            problem_fn = self._noisy_problem_fn if self.noise_std > 0.0 else self.problem
            algorithm_returned_fitness = self.executor.execute_algorithm(
                code=solution.code,
                name=solution.name,
                dim=self.problem.dim,
                problem=problem_fn,
                budget=self.budget,
            )
            elapsed_time = time.perf_counter() - start_time
            evals_used = self.problem._clean_problem.state.evaluations

            # --- 2. Calculate metrics, feedback, and metadata ---
            fitness_score, feedback, metadata = self._compute_metrics_and_feedback(
                algorithm_returned_fitness,
                solution.name,
                elapsed_time,
                evals_used,
                code_lines,
                code_length,
                llm_generation_time=llm_gen_time,
            )

        except (Exception, FunctionTimedOut) as e:
            elapsed_time = time.perf_counter() - start_time
            evals_used = self.problem._clean_problem.state.evaluations
            budget_consumed_pct = (evals_used / self.budget * 100) if self.budget > 0 else 0.0
            evals_per_second = (evals_used / elapsed_time) if elapsed_time > 0.0 else 0.0

            if isinstance(e, FunctionTimedOut):
                fitness_score = float("-inf")
                feedback = (
                    f"Execution failed: Your algorithm exceeded the {self.timeout_seconds}-second time limit. "
                    "Please optimize your loops and make the code more efficient."
                )
                metadata = IterationMetadata(
                    algorithm_name=solution.name,
                    execution=ExecutionProfile(
                        timed_out=True,
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
                        error_type=type(e).__name__,
                        error_message=str(e),
                        error_traceback=None,
                    ),
                    convergence=ConvergenceProfile(
                        converged=False,
                        convergence_threshold=1e-6,
                    ),
                )
            else:
                fitness_score = float("-inf")
                feedback = (
                    "Execution failed with the following Python error:\n"
                    f"{traceback.format_exc()}\n"
                    "Please fix the bugs."
                )
                metadata = IterationMetadata(
                    algorithm_name=solution.name,
                    execution=ExecutionProfile(
                        timed_out=False,
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
                        error_type=type(e).__name__,
                        error_message=str(e),
                        error_traceback=traceback.format_exc(),
                    ),
                    convergence=ConvergenceProfile(
                        converged=False,
                        convergence_threshold=1e-6,
                    ),
                )

        # Set evaluation outcomes on the solution object
        self._current_iteration += 1
        metadata.iteration = self._current_iteration
        self._append_to_json_checkpoint(metadata)

        solution.set_scores(fitness_score, feedback)

        # Attach metadata to the solution object for later serialization
        solution.metadata = metadata

        return solution

    def __getstate__(self):
        # Exclude unpicklable C++ object wrappers (executor) for joblib/pickle state logging.
        # problem is picklable since BBOBProblem implements its own self-healing __getstate__/__setstate__.
        state = self.__dict__.copy()
        state["executor"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Re-initialize the executor if needed
        from core.llamea.executor import AlgorithmExecutor

        self.executor = AlgorithmExecutor(timeout_seconds=self.timeout_seconds)
