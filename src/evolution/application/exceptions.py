"""Application failures raised while coordinating synthesis workflows."""

from typing import Literal

ProviderFailure = Literal["authentication", "quota", "unavailable", "timeout", "invalid_response"]


class ProviderError(RuntimeError):
    """Terminal model-provider failure, never an optimizer performance result."""

    def __init__(self, reason: ProviderFailure, model: str, message: str) -> None:
        super().__init__(reason, model, message)
        self.reason = reason
        self.model = model

    def __str__(self) -> str:
        return f"Model provider {self.model}: {self.args[2]} ({self.reason})"


class OrchestrationError(RuntimeError):
    """Aggregate failures from one or more dispatched campaign tasks."""

    def __init__(
        self, errors: dict[str, Exception], results: dict[str, object] | None = None
    ) -> None:
        formatted = "\n".join(
            f"  - Task '{key}': {type(err).__name__}: {err}" for key, err in errors.items()
        )
        super().__init__(f"Evolution tasks failed:\n{formatted}")
        self.errors = errors
        self.results = results if results is not None else {}

    def __reduce__(self) -> tuple[object, ...]:
        return type(self), (self.errors, self.results)


class SynthesisResumeError(ValueError):
    """A saved session cannot be resumed without mixing execution protocols."""


__all__ = ["OrchestrationError", "ProviderError", "SynthesisResumeError"]
