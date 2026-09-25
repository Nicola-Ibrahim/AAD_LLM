"""Exceptions for code compilation, validation, and sandboxed execution."""


class CodeValidationException(Exception):
    """Exception raised when generated code fails syntax, structure, or security validation."""

    pass


class AlgorithmTimeoutException(Exception):
    """Exception raised when candidate algorithm execution exceeds the allowed wall-clock time."""

    pass
