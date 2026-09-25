"""Application failures raised while coordinating synthesis workflows."""


class OrchestrationError(RuntimeError):
    """Aggregate failures from one or more dispatched campaign tasks."""

    def __init__(self, errors: dict[str, Exception]) -> None:
        formatted = "\n".join(
            f"  - Task '{key}': {type(err).__name__}: {err}" for key, err in errors.items()
        )
        super().__init__(f"Evolution tasks failed:\n{formatted}")
        self.errors = errors


__all__ = ["OrchestrationError"]
