import traceback
from typing import Any, List, Optional, Tuple
import numpy as np
from func_timeout import func_timeout, FunctionTimedOut
from llamea import Solution
from aad_llm.noisy_bbob import BBOBProblem

class Evaluator:
    """
    LLaMEA-compatible evaluator for noisy BBOB optimization problems.
    
    This class is called by the LLaMEA framework to evaluate candidate search 
    algorithms. It performs a single execution run of the algorithm on a fresh 
    noisy BBOB problem instance under timeout protection, records the clean 
    convergence trajectory, calculates the anytime AOCC score, and assigns 
    the fitness score to the candidate solution.
    """

    def __init__(
        self,
        problem: BBOBProblem,
        budget: int = 1000,
        timeout_seconds: float = 10.0,
    ):
        """
        Initialize the evaluator.

        Parameters
        ----------
        problem : BBOBProblem
            Fully-configured BBOB problem instance. Its `reset()` method is
            called before each candidate evaluation to clear the history.
        budget : int, optional
            Maximum allowed objective function evaluations, by default 1000.
        timeout_seconds : float, optional
            Maximum wall-clock execution time allowed for one algorithm run,
            by default 10.0.
        """
        self.problem = problem
        self.budget = budget
        self.timeout_seconds = timeout_seconds

    def _compute_aocc(self, best_clean_values: List[float], true_optimum: float) -> float:
        """
        Compute Area Over the Convergence Curve (AOCC) on a normalized log-scale.

        Measures anytime convergence speed and quality. Progress is mapped 
        logarithmically between the starting error and target precision (1e-8), 
        then averaged over the execution budget.

        Parameters
        ----------
        best_clean_values : List[float]
            List of the best clean function values tracked at each evaluation.
        true_optimum : float
            The global minimum objective value of the BBOB function.

        Returns
        -------
        aocc_score : float
            Anytime performance score in the range [0.0, 1.0], where 1.0 is best.
        """
        history = list(best_clean_values)
        if not history:
            return 0.0

        # Enforce budget constraints by padding (if terminated early) or truncating
        if len(history) < self.budget:
            last_val = history[-1]
            history.extend([last_val] * (self.budget - len(history)))
        elif len(history) > self.budget:
            history = history[:self.budget]

        # Convert clean values to errors: e(t) = best_clean_y(t) - true_optimum.
        # Since it is a minimization problem, we clamp to >= 0.0 to prevent negative values.
        errors = [max(y - true_optimum, 0.0) for y in history]
        
        # Define log-scale targets
        min_error = 1e-8
        initial_error = errors[0]
        max_error = max(initial_error, 1.0)
        
        # If the algorithm started at or below the target precision, progress is perfect
        if max_error <= min_error:
            return 1.0
            
        log_max = float(np.log10(max_error))
        log_min = float(np.log10(min_error))
        log_range = log_max - log_min
        
        # Integrate progress across all budget evaluation steps
        progress_sum = 0.0
        for err in errors:
            # Clip step error to the range [min_error, max_error]
            clipped_err = max(min(err, max_error), min_error)
            progress = (log_max - float(np.log10(clipped_err))) / log_range
            progress_sum += progress
            
        return float(progress_sum / self.budget)

    def _instantiate_algorithm(self, code: str, name: str) -> Any:
        """
        Dynamically execute the candidate algorithm's code and instantiate the class.
        """
        # Execute the candidate code in the global namespace
        exec(code, globals())
        
        # Verify the algorithm class exists in globals
        if name not in globals():
            raise KeyError(
                f"Algorithm class '{name}' was not found after execution. "
                "Make sure the class name in your code exactly matches your proposed name."
            )
            
        algorithm_cls = globals()[name]
        algorithm = algorithm_cls()

        # Inject search space dimensionality if the algorithm class expects it
        if hasattr(algorithm, 'dim'):
            algorithm.dim = self.problem.dim
            
        return algorithm

    def _run_algorithm(self, algorithm: Any, noisy_func: Any) -> float:
        """
        Run the candidate algorithm with a budget and wall-clock timeout protection.
        """
        best_found_y = func_timeout(
            self.timeout_seconds, 
            algorithm, 
            args=(noisy_func, self.budget)
        )
        
        if best_found_y is None:
            raise TypeError(
                "The algorithm did not return a valid fitness/objective value. "
                "Make sure your __call__ method returns the best found float value."
            )
            
        return float(best_found_y)

    def _evaluate_and_format(self, best_found_y: float) -> Tuple[float, str]:
        """
        Compute AOCC score and format feedback information.
        """
        true_optimum = self.problem.true_optimum
        
        # Compute anytime AOCC score using clean best history
        aocc_score = self._compute_aocc(self.problem.best_clean_values, true_optimum)
        
        # Find the best clean value encountered and compute final error
        final_clean_y = self.problem.best_clean_values[-1] if self.problem.best_clean_values else float('inf')
        final_error = abs(final_clean_y - true_optimum)
        
        feedback = (
            f"The algorithm achieved an anytime AOCC score of {aocc_score:.4f} (where 1.0 is best) "
            f"and a final clean error of {final_error:.4f} from the true optimum ({true_optimum:.4f}) "
            f"on BBOB Problem {self.problem.problem_id} (additive noise std: {self.problem.noise_std}). "
            "Improve convergence speed and noise resilience to maximize the AOCC score."
        )
        
        return aocc_score, feedback

    def __call__(self, solution: Solution, explogger: Optional[Any] = None) -> Solution:
        """
        Execute and score a candidate optimization algorithm solution.

        Parameters
        ----------
        solution : Solution
            The LLaMEA candidate solution containing its source code and name.
        explogger : Optional[Any], optional
            Framework-level experiment logger, by default None.

        Returns
        -------
        solution : Solution
            The modified solution object populated with fitness scores and feedback.
        """
        # --- 1. Reset problem history for a fresh evaluation run ---
        self.problem.reset()

        try:
            # --- 2. Safely execute candidate code & instantiate class ---
            algorithm = self._instantiate_algorithm(solution.code, solution.name)

            # --- 3. Execute candidate run with timeout protection ---
            best_found_y = self._run_algorithm(algorithm, self.problem)
            
            # --- 4. Calculate anytime AOCC metric from clean history ---
            fitness_score, feedback = self._evaluate_and_format(best_found_y)

        except FunctionTimedOut:
            fitness_score = float('-inf')
            feedback = (
                f"Execution failed: Your algorithm exceeded the {self.timeout_seconds}-second time limit. "
                "Please optimize your loops and make the code more efficient."
            )

        except Exception:
            fitness_score = float('-inf')
            feedback = (
                "Execution failed with the following Python error:\n"
                f"{traceback.format_exc()}\n"
                "Please fix the bugs."
            )

        # Set evaluation outcomes on the solution object
        solution.set_scores(fitness_score, feedback)
        return solution

