"""Typed public workflow outcomes; internal collaborators continue to raise failures."""

import re
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


class ApplicationError(BaseModel):
    """Safe error information for a notebook, CLI or future HTTP response."""

    model_config = ConfigDict(frozen=True)

    operation: str
    code: str
    message: str
    diagnostic_log: str | None

    @staticmethod
    def sanitize(text: str) -> str:
        return re.sub(r"(?i)(Bearer\s+\S+|sk-[a-zA-Z0-9_-]+)", "[REDACTED]", text)

    @classmethod
    def describe(cls, error: BaseException) -> str:
        """Safe public details, never a vendor response body or client object."""
        kind = type(error)
        if kind.__module__.split(".")[0] in {"openai", "httpx", "httpcore"}:
            return f"{kind.__name__}: external provider details omitted"
        if isinstance(error, BaseExceptionGroup):
            return f"{kind.__name__}: " + "; ".join(cls.describe(e) for e in error.exceptions)
        return cls.sanitize(f"{kind.__name__}: {error}")


class Result(BaseModel, Generic[T]):
    """Exactly one public data/error outcome, retaining its exception internally.

    ``None`` means no successful value on failure, or no diagnostic file when no
    host configured one. Serialize ``error``, never the retained exception.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    value: T | None
    error: ApplicationError | None
    exception: Exception | None = Field(exclude=True, repr=False)

    @model_validator(mode="after")
    def validate_outcome(self) -> "Result[T]":
        if (self.error is None) != (self.exception is None):
            raise ValueError("A failed result must retain both its error and original exception")
        if self.error is not None and self.value is not None:
            raise ValueError("A failed result cannot also contain a successful value")
        return self

    @property
    def is_success(self) -> bool:
        return self.error is None

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        return cls(value=value, error=None, exception=None)

    @classmethod
    def failure(cls, operation: str, error: Exception) -> "Result[T]":
        path = getattr(error, "diagnostic_log", None)
        return cls(
            value=None,
            error=ApplicationError(
                operation=operation,
                code=type(error).__name__,
                message=ApplicationError.describe(error),
                diagnostic_log=str(path) if path is not None else None,
            ),
            exception=error,
        )
