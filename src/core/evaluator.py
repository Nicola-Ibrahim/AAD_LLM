import traceback
from typing import Any
import numpy as np
from llamea import Solution
from problems.bbob import BBOBProblem
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
            Maximum allowed objective function evaluations, by default 1000.
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
        self, algorithm_returned_fitness: float, algorithm_name: str
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

        metadata = {
            "problem_id": self.problem.problem_id,
            "dim": self.problem.dim,
            "noise_std": self.noise_std,
            "instance_id": self.problem.instance_id,
            "true_optimum": true_optimum,
            "algorithm_returned_fitness": algorithm_returned_fitness,
            "final_error": final_error,
            "algorithm_name": algorithm_name,
            "timed_out": False,
        }

        # LLaMEA expects a fitness score where higher is better.
        # We negate the final_error so that an error of 0 is the max (0.0), and larger errors are more negative.
        fitness_score = -final_error

        return fitness_score, feedback, metadata

    def _noisy_problem_fn(self, x: np.ndarray) -> float:
        """Helper method to wrap noise evaluation without unpicklable lambda functions."""
        res = self.problem(x, noise_std=self.noise_std)
        if isinstance(res, dict):
            return res.get(self.noise_std, float("inf"))
        return res

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

            # --- 2. Calculate metrics, feedback, and metadata ---
            fitness_score, feedback, metadata = self._compute_metrics_and_feedback(
                algorithm_returned_fitness, solution.name
            )

        except Exception as e:
            if type(e).__name__ == "FunctionTimedOut":
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
                    "algorithm_returned_fitness": float("inf"),
                    "final_error": float("inf"),
                    "algorithm_name": solution.name,
                    "timed_out": True,
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
                    "algorithm_returned_fitness": float("inf"),
                    "final_error": float("inf"),
                    "algorithm_name": solution.name,
                    "timed_out": False,
                }

        # Set evaluation outcomes on the solution object
        solution.set_scores(fitness_score, feedback)

        # Attach metadata to the solution object for later serialization
        solution.metadata = metadata

        return solution
