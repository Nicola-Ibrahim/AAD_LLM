from shared.execution import (
    AlgorithmTimeoutException,
    CodeValidationException,
)


class BaseDomainException(Exception):
    """Base exception for all domain and application level errors."""

    pass


class OrchestrationError(BaseDomainException, RuntimeError):
    """Exception raised when one or more parallel evolution tasks fail."""

    def __init__(self, errors: dict[str, Exception]):
        formatted_details = "\n".join(
            f"  - Task '{key}': {type(err).__name__}: {err}" for key, err in errors.items()
        )
        super().__init__(f"Evolution tasks failed:\n{formatted_details}")
        self.errors = errors


__all__ = [
    "BaseDomainException",
    "CodeValidationException",
    "AlgorithmTimeoutException",
    "OrchestrationError",
]
