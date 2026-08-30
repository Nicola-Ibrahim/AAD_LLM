import warnings
from typing import Any, Callable

import numpy as np
from func_timeout import FunctionTimedOut, func_timeout

from shared.execution.exceptions import AlgorithmTimeoutException
from shared.execution.compiler import CodeCompiler


class AlgorithmExecutor:
    """
    Responsible for executing candidate algorithms under strict timeout constraints.
    Delegates compilation and validation to CodeCompiler.

    Workflow:
                 code, name, dim, problem, budget
                                │
                                ▼
              CodeCompiler.compile(code, name, dim)
              • AST Parse & Sanitize (empty def bodies)
              • Ban Check: scipy.optimize strictly blocked
              • Isolated Namespace Execution & Class Instantiation
                                │
                                ▼
              Sandboxed Execution with Timeout Protection
              • func_timeout(timeout_seconds, runner)
              • Warning Interception (np.seterr, catch_warnings)
                                │
           ┌────────────────────┴────────────────────┐
        Success                                   Timeout
    (returns result)                    (exceeds timeout_seconds)
           │                                         │
           ▼                                         ▼
    1. Unpack & Normalize:                Raise AlgorithmTimeoutException
       • (best_x, best_y) or float(best_y)
       • Convert best_x to np.ndarray
    2. Validate Finiteness (no NaN/inf)
    3. Budget Overrun Check (> 1.10x)
           │
           ▼
    Return (best_x, fitness)
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
        self.last_captured_warnings: list[str] = []

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
        self.last_captured_warnings = list(getattr(self._compiler, "last_compiler_warnings", []))
        captured_warnings = self.last_captured_warnings

        def _runner(p: Callable[..., float], b: int) -> Any:
            with warnings.catch_warnings(record=True) as recorded:
                warnings.simplefilter("always")
                old_errstate = np.seterr(all="warn")
                try:
                    return algorithm(p, b)
                finally:
                    np.seterr(**old_errstate)
                    for w in recorded:
                        msg = f"{w.category.__name__}: {w.message}"
                        if w.filename == "<string>" or "string" in str(w.filename):
                            msg = f"line {w.lineno}: {msg}"
                        if msg not in captured_warnings:
                            captured_warnings.append(msg)

        try:
            result = func_timeout(self._timeout_seconds, _runner, args=(problem, budget))
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

        import math

        if not math.isfinite(algorithm_returned_fitness):
            raise ValueError(
                f"[INVALID RETURN] Algorithm returned a non-finite value: {algorithm_returned_fitness}. "
                "Ensure __call__ returns a valid float (no NaN or inf)."
            )

        actual_evals = getattr(problem, "evaluations", None)
        if actual_evals is not None and actual_evals > budget * 1.10:
            captured_warnings.append(
                f"[BUDGET OVERRUN] Algorithm used {actual_evals} problem() calls but budget={budget}. "
                "Your evaluations counter is not tracking all calls to problem(). "
                "Fix: increment evaluations for every call to problem()."
            )

        return best_x, algorithm_returned_fitness
