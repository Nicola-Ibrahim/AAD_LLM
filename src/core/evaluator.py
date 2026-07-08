import time
import traceback
from typing import Any
import numpy as np
from llamea import Solution
from problems.bbob import BBOBProblem
from func_timeout import FunctionTimedOut
from core.executor import AlgorithmExecutor


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
        self.executor = AlgorithmExecutor(timeout_seconds=self.timeout_seconds)

    def _compute_metrics_and_feedback(
        self,
        algorithm_returned_fitness: float,
        algorithm_name: str,
        runtime_seconds: float,
        evaluations_used: int,
        code_lines: int,
        code_length: int,
    ) -> tuple[float, str, dict[str, Any]]:
        """
        Compute final error, fitness score, feedback message, and metadata dictionary.
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
        error_per_evaluation = (
            (final_error / evaluations_used) if evaluations_used > 0 else float("inf")
        )
        converged = final_error < 1e-6

        metadata = {
            "problem_id": self.problem.problem_id,
            "dim": self.problem.dim,
            "noise_std": self.noise_std,
            "instance_id": self.problem.instance_id,
            "true_optimum": true_optimum,
            "raw_fitness": algorithm_returned_fitness,
            "final_error": final_error,
            "algorithm_name": algorithm_name,
            "timed_out": False,
            "runtime_seconds": runtime_seconds,
            "evaluations_used": evaluations_used,
            "budget_consumed_pct": budget_consumed_pct,
            "relative_error": relative_error,
            "evals_per_second": evals_per_second,
            "error_per_evaluation": error_per_evaluation,
            "converged": converged,
            "convergence_threshold": 1e-6,
            "code_lines": code_lines,
            "code_length": code_length,
        }

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
                metadata = {
                    "problem_id": self.problem.problem_id,
                    "dim": self.problem.dim,
                    "noise_std": self.noise_std,
                    "instance_id": self.problem.instance_id,
                    "true_optimum": self.problem.true_optimum,
                    "raw_fitness": float("inf"),
                    "final_error": float("inf"),
                    "algorithm_name": solution.name,
                    "timed_out": True,
                    "runtime_seconds": elapsed_time,
                    "evaluations_used": evals_used,
                    "budget_consumed_pct": budget_consumed_pct,
                    "relative_error": float("inf"),
                    "evals_per_second": evals_per_second,
                    "error_per_evaluation": float("inf"),
                    "converged": False,
                    "convergence_threshold": 1e-6,
                    "code_lines": code_lines,
                    "code_length": code_length,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "error_traceback": None,
                }
            else:
                fitness_score = float("-inf")
                feedback = (
                    "Execution failed with the following Python error:\n"
                    f"{traceback.format_exc()}\n"
                    "Please fix the bugs."
                )
                metadata = {
                    "problem_id": self.problem.problem_id,
                    "dim": self.problem.dim,
                    "noise_std": self.noise_std,
                    "instance_id": self.problem.instance_id,
                    "true_optimum": self.problem.true_optimum,
                    "raw_fitness": float("inf"),
                    "final_error": float("inf"),
                    "algorithm_name": solution.name,
                    "timed_out": False,
                    "runtime_seconds": elapsed_time,
                    "evaluations_used": evals_used,
                    "budget_consumed_pct": budget_consumed_pct,
                    "relative_error": float("inf"),
                    "evals_per_second": evals_per_second,
                    "error_per_evaluation": float("inf"),
                    "converged": False,
                    "convergence_threshold": 1e-6,
                    "code_lines": code_lines,
                    "code_length": code_length,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "error_traceback": traceback.format_exc(),
                }

        # Set evaluation outcomes on the solution object
        solution.set_scores(fitness_score, feedback)

        # Attach metadata to the solution object for later serialization
        solution.metadata = metadata

        return solution

    def __getstate__(self):
        # Exclude unpicklable C++ object wrappers (ioh problem, executor) for joblib/pickle state logging
        state = self.__dict__.copy()
        state["problem"] = None
        state["executor"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Re-initialize the executor if needed
        from core.executor import AlgorithmExecutor

        self.executor = AlgorithmExecutor(timeout_seconds=self.timeout_seconds)
