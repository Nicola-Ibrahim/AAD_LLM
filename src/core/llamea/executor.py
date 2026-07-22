import ast
import builtins
from typing import Any, Callable

from func_timeout import func_timeout

import collections
import functools
import itertools
import math
import random
import numpy as np
import scipy
import scipy.optimize
import scipy.stats


def _sanitize_code(code: str) -> str:
    """
    Sanitize LLM-generated code by inserting 'pass' into empty method/function bodies
    where a function definition ('def ...:') is followed by another definition or end of block
    without an indented statement body.
    """
    lines = code.splitlines()
    sanitized_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        sanitized_lines.append(line)
        stripped = line.strip()
        if stripped.startswith("def ") and stripped.endswith(":"):
            indent = len(line) - len(line.lstrip())
            j = i + 1
            is_empty_body = True
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip():
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent > indent and not next_line.strip().startswith(
                        ("def ", "class ")
                    ):
                        is_empty_body = False
                    break
                j += 1
            if is_empty_body:
                sanitized_lines.append(" " * (indent + 4) + "pass")
        i += 1
    return "\n".join(sanitized_lines)


def _find_class_names_in_code(code: str) -> list[str]:
    """
    Use AST parsing to reliably extract all top-level class names defined
    in the algorithm source code (not from imports).
    """
    code = _sanitize_code(code)
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


class CodeValidationError(Exception):
    """Raised when LLM-generated code fails structural or syntax validation."""

    pass


def _validate_code(code: str, isolated_globals: dict[str, Any]) -> type:
    """
    Validate LLM-generated code through four stages:
      1. AST syntax check (catches IndentationError, SyntaxError)
      2. Execution into isolated namespace
      3. Class resolution (finding the top-level algorithm class)
      4. Instantiation check (verifying no-arg constructor or dim parameter)

    Returns the resolved algorithm class if valid.
    Raises CodeValidationError with a descriptive message if invalid.
    """
    # Stage 1: AST syntax check
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise CodeValidationError(
            f"Generated code has a Python syntax error:\n"
            f"  Line {e.lineno}: {e.msg}\n\n"
            f"Fix: ensure all method bodies are non-empty (use `pass` if needed), "
            f"and all variables are defined before use."
        ) from e

    # Stage 2: Execute into isolated namespace
    try:
        exec(code, isolated_globals)  # noqa: S102
    except Exception as e:
        raise CodeValidationError(
            f"Generated code raised an error during compilation:\n"
            f"  {type(e).__name__}: {e}\n\n"
            f"Fix: check for undefined names, import errors, or invalid statements."
        ) from e

    # Stage 3: Class resolution
    class_names = _find_class_names_in_code(code)
    algorithm_cls: type | None = None
    for cls_name in class_names:
        candidate = isolated_globals.get(cls_name)
        if candidate is not None and isinstance(candidate, type):
            algorithm_cls = candidate
            break

    if algorithm_cls is None:
        raise CodeValidationError(
            f"No callable class found in generated code. "
            f"Detected class names: {class_names}. "
            f"Ensure the code contains a class with a `__call__(self, problem, budget)` method."
        )

    # Stage 4: Instantiation check
    try:
        _ = algorithm_cls()
    except TypeError:
        try:
            _ = algorithm_cls(dim=3)
        except Exception as err:
            raise CodeValidationError(
                f"Algorithm class `{algorithm_cls.__name__}.__init__` failed to instantiate: {err}.\n"
                f"Fix: `__init__` must accept only `self` with no extra required parameters."
            ) from err

    return algorithm_cls


class AlgorithmExecutor:
    """
    Responsible for dynamically compiling and executing candidate algorithms
    under strict timeout constraints.
    """

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        """
        Initialize the AlgorithmExecutor.

        Args:
            timeout_seconds (float): Maximum wall-clock time allowed for an algorithm execution.
        """
        self._timeout_seconds = timeout_seconds

    def _create_isolated_namespace(self) -> dict[str, Any]:
        """
        Create a secure, isolated namespace with essential math and utility libraries.

        Returns:
            dict[str, Any]: A dictionary representing the global namespace for code execution.
        """
        isolated_globals: dict[str, Any] = {
            "__builtins__": builtins,
            "np": np,
            "numpy": np,
            "math": math,
            "random": random,
            "collections": collections,
            "itertools": itertools,
            "functools": functools,
        }
        if scipy is not None:
            isolated_globals["scipy"] = scipy

        return isolated_globals

    def _instantiate_algorithm(self, algorithm_cls: type, name: str, dim: int) -> Any:
        """
        Safely instantiate the algorithm class.

        Args:
            algorithm_cls (type): The class of the algorithm.
            name (str): The name of the class for fallback.
            dim (int): Dimensionality to optionally pass to the constructor.

        Returns:
            Any: An instantiated algorithm object ready for execution.
        """
        try:
            algorithm = algorithm_cls()
        except TypeError:
            algorithm = algorithm_cls(dim)

        # Inject search space dimensionality if the algorithm class defines it
        if hasattr(algorithm, "dim"):
            algorithm.dim = dim

        # Ensure algorithm instance has a __name__ attribute for func_timeout error formatting
        if not hasattr(algorithm, "__name__"):
            algorithm.__name__ = getattr(algorithm_cls, "__name__", name)

        return algorithm

    def execute_algorithm(
        self, code: str, name: str, dim: int, problem: Callable[..., float], budget: int
    ) -> float:
        """Dynamically execute (compile) candidate algorithm code, instantiate the class,
        and execute it with budget and wall-clock timeout protection.

        Args:
            code: The raw python code of the optimization algorithm.
            name: The class name of the optimization algorithm to instantiate.
                If the class is not found by name, the first class defined in the
                code (via AST analysis) is used as a fallback.
            dim: The dimensionality of the search space, to be injected into the algorithm.
            problem: The objective function to be minimized.
            budget: Stopping criterion given to the algorithm (equivalent to a convergence
                threshold in gradient descent). The algorithm uses this to limit its `problem(x)`
                calls and return its best found float value.

        Returns:
            float: The best fitness value reported by the candidate algorithm.
        """
        isolated_globals = self._create_isolated_namespace()
        code = _sanitize_code(code)

        algorithm_cls = _validate_code(code, isolated_globals)
        algorithm = self._instantiate_algorithm(algorithm_cls, name, dim)

        algorithm_returned_fitness = func_timeout(
            self._timeout_seconds, algorithm, args=(problem, budget)
        )

        if algorithm_returned_fitness is None:
            raise TypeError(
                "The algorithm did not return a valid fitness/objective value. "
                "Make sure your __call__ method returns the best found float value."
            )

        return float(algorithm_returned_fitness)
