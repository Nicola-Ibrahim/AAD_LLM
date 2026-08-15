import ast
import builtins
import collections
import functools
import itertools
import math
import random
import types
from typing import Any

import numpy as np
import scipy
import scipy.linalg
import scipy.special
import scipy.stats

from synthesis.execution.exceptions import CodeValidationException


class CodeCompiler:
    """
    Responsible for sanitizing, parsing, validating, compiling,
    and instantiating candidate algorithm code in a secure isolated namespace.
    """

    def sanitize_code(self, code: str) -> str:
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

    def _find_class_names_in_code(self, code: str) -> list[str]:
        """
        Use AST parsing to reliably extract all top-level class names defined
        in the algorithm source code (not from imports).
        """
        code = self.sanitize_code(code)
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def _check_banned_imports_and_calls(self, tree: ast.AST) -> None:
        """
        Check AST for banned pre-built solver imports or attribute accesses.
        Bans scipy.optimize entirely.
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "scipy.optimize" or alias.name.startswith("scipy.optimize."):
                        raise CodeValidationException(
                            f"Import of '{alias.name}' is strictly prohibited. "
                            "Pre-built scipy optimizers are banned. Write your search algorithm logic from scratch using NumPy."
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module == "scipy.optimize" or node.module.startswith("scipy.optimize."):
                        raise CodeValidationException(
                            f"Import from '{node.module}' is strictly prohibited. "
                            "Pre-built scipy optimizers are banned. Write your search algorithm logic from scratch using NumPy."
                        )
                    if node.module == "scipy":
                        for alias in node.names:
                            if alias.name == "optimize":
                                raise CodeValidationException(
                                    "Importing 'optimize' from 'scipy' is strictly prohibited. "
                                    "Pre-built scipy optimizers are banned. Write your search algorithm logic from scratch using NumPy."
                                )
            elif isinstance(node, ast.Attribute):
                if node.attr == "optimize" and isinstance(node.value, ast.Name) and node.value.id == "scipy":
                    raise CodeValidationException(
                        "Usage of 'scipy.optimize' is strictly prohibited. "
                        "Pre-built scipy optimizers are banned. Write your search algorithm logic from scratch using NumPy."
                    )

    def _check_budget_leak_patterns(self, tree: ast.AST) -> list[str]:
        """
        Scan AST for common budget leak patterns (e.g. min(..., key=lambda x: problem(x))).
        Returns advisory warning strings (non-blocking).
        """
        warnings_list: list[str] = []
        for node in ast.walk(tree):
            # Check min/max with key=lambda calling problem
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("min", "max"):
                for kw in node.keywords:
                    if kw.arg == "key" and isinstance(kw.value, ast.Lambda):
                        for inner in ast.walk(kw.value):
                            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and "problem" in inner.func.id:
                                warnings_list.append(
                                    f"line {node.lineno}: Possible hidden problem(x) calls in `{node.func.id}(..., key=...)` lambda. "
                                    "These calls are not counted in your evaluations counter. Make all problem calls explicit."
                                )
        return warnings_list

    def _validate_code(self, code: str, isolated_globals: dict[str, Any], name: str = "") -> type:
        """
        Validate LLM-generated code through four stages:
          1. AST syntax & banned imports check
          2. Execution into isolated namespace
          3. Class resolution
          4. Instantiation check

        Returns the resolved algorithm class if valid.
        Raises CodeValidationException if invalid.
        """
        self.last_compiler_warnings: list[str] = []
        try:
            tree = ast.parse(code)
            self._check_banned_imports_and_calls(tree)
            self.last_compiler_warnings = self._check_budget_leak_patterns(tree)
        except SyntaxError as e:
            raise CodeValidationException(
                f"Generated code has a Python syntax error:\n"
                f"  Line {e.lineno}: {e.msg}\n\n"
                f"Fix: ensure all method bodies are non-empty (use `pass` if needed), "
                f"and all variables are defined before use."
            ) from e

        try:
            exec(code, isolated_globals)  # noqa: S102
        except Exception as e:
            raise CodeValidationException(
                f"Generated code raised an error during compilation:\n"
                f"  {type(e).__name__}: {e}\n\n"
                f"Fix: check for undefined names, import errors, or invalid statements."
            ) from e

        algorithm_cls: type | None = None
        if name and name in isolated_globals and isinstance(isolated_globals[name], type):
            algorithm_cls = isolated_globals[name]
        else:
            class_names = self._find_class_names_in_code(code)
            for cls_name in class_names:
                candidate = isolated_globals.get(cls_name)
                if candidate is not None and isinstance(candidate, type):
                    algorithm_cls = candidate
                    break

        if algorithm_cls is None:
            class_names = self._find_class_names_in_code(code)
            raise CodeValidationException(
                f"No callable class found in generated code. "
                f"Detected class names: {class_names}. "
                f"Ensure the code contains a class with a `__call__(self, problem, budget)` method."
            )

        try:
            _ = algorithm_cls()
        except TypeError:
            try:
                _ = algorithm_cls(dim=3)
            except Exception as err:
                raise CodeValidationException(
                    f"Algorithm class `{algorithm_cls.__name__}.__init__` failed to instantiate: {err}.\n"
                    f"Fix: `__init__` must accept only `self` with no extra required parameters."
                ) from err

        return algorithm_cls

    def _create_isolated_namespace(self) -> dict[str, Any]:
        """
        Create a secure, isolated namespace with essential math and utility libraries.
        Excludes scipy.optimize to ban pre-built solver wrappers while permitting
        utility submodules (scipy.linalg, scipy.stats, scipy.special).
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
            isolated_globals["scipy"] = types.SimpleNamespace(
                linalg=scipy.linalg,
                stats=scipy.stats,
                special=scipy.special,
            )

        return isolated_globals

    def _instantiate_algorithm(self, algorithm_cls: type, name: str, dim: int) -> Any:
        """
        Safely instantiate the algorithm class.
        """
        try:
            algorithm = algorithm_cls()
        except TypeError:
            algorithm = algorithm_cls(dim)

        if hasattr(algorithm, "dim"):
            algorithm.dim = dim

        if not hasattr(algorithm, "__name__"):
            algorithm.__name__ = getattr(algorithm_cls, "__name__", name)

        return algorithm

    def compile(self, code: str, name: str, dim: int) -> Any:
        """
        Sanitize, validate, compile, and instantiate candidate algorithm code into a runnable object.
        """
        isolated_globals = self._create_isolated_namespace()
        sanitized_code = self.sanitize_code(code)

        algorithm_cls = self._validate_code(sanitized_code, isolated_globals, name=name)
        return self._instantiate_algorithm(algorithm_cls, name, dim)
