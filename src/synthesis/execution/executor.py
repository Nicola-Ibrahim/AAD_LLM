from typing import Callable

import numpy as np
from func_timeout import FunctionTimedOut, func_timeout

from synthesis.execution.exceptions import AlgorithmTimeoutException
from synthesis.execution.compiler import CodeCompiler


class AlgorithmExecutor:
    """
    Responsible for executing candidate algorithms under strict timeout constraints.
    Delegates compilation and validation to CodeCompiler.
    """

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        compiler: CodeCompiler | None = None,
    ) -> None:
        """
        Initialize the AlgorithmExecutor.

        Args:
            timeout_seconds (float): Maximum wall-clock time allowed for an algorithm execution.
            compiler (CodeCompiler | None): Optional custom compiler instance.
        """
        self._timeout_seconds = timeout_seconds
        self._compiler = compiler or CodeCompiler()

    def execute_algorithm(
        self, code: str, name: str, dim: int, problem: Callable[..., float], budget: int
    ) -> tuple[np.ndarray | None, float]:
        """Dynamically compile and execute candidate algorithm code with budget and
        wall-clock timeout protection.

        Args:
            code: The raw python code of the optimization algorithm.
            name: The class name of the optimization algorithm to instantiate.
            dim: The dimensionality of the search space, to be injected into the algorithm.
            problem: The objective function to be minimized.
            budget: Stopping criterion given to the algorithm.

        Returns:
            tuple[np.ndarray | None, float]: A tuple containing the best search point coordinates
                (if returned by the algorithm) and the best observed fitness value.
        """
        algorithm = self._compiler.compile(code, name, dim)

        try:
            result = func_timeout(
                self._timeout_seconds, algorithm, args=(problem, budget)
            )
        except FunctionTimedOut as e:
            raise AlgorithmTimeoutException(
                f"Execution failed: Your algorithm exceeded the {self._timeout_seconds}-second time limit."
            ) from e

        if result is None:
            raise TypeError(
                "The algorithm did not return a valid fitness/objective value. "
                "Make sure your __call__ method returns (best_x, float(best_y))."
            )

        best_x: np.ndarray | None = None
        algorithm_returned_fitness: float

        if isinstance(result, tuple) and len(result) == 2:
            raw_x, raw_y = result
            if raw_x is not None:
                best_x = np.asarray(raw_x, dtype=float)
            algorithm_returned_fitness = float(raw_y)
        elif isinstance(result, (int, float, np.number)):
            algorithm_returned_fitness = float(result)
        else:
            raise TypeError(
                f"The algorithm returned an unexpected object type {type(result).__name__}. "
                "Expected (best_x, float(best_y)) or float(best_y)."
            )

        return best_x, algorithm_returned_fitness
