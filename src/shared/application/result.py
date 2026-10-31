"""Typed public workflow outcomes with safe, serializable failure details."""

import re
from typing import Callable, Generic, TypeVar, cast

from pydantic import BaseModel, ConfigDict, PrivateAttr, model_validator

T = TypeVar("T")
R = TypeVar("R")


class Error(BaseModel):
    """Safe error information, with its original exception kept private."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, extra="forbid")

    operation: str
    code: str
    message: str
    diagnostic_log: str | None = None
    _original_exception: Exception | None = PrivateAttr(default=None)

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

    @classmethod
    def from_exception(cls, operation: str, exception: Exception) -> "Error":
        path = getattr(exception, "diagnostic_log", None)
        error = cls(
            operation=operation,
            code=type(exception).__name__,
            message=cls.describe(exception),
            diagnostic_log=str(path) if path is not None else None,
        )
        error._original_exception = exception
        return error


class Result(BaseModel, Generic[T]):
    """One successful value or one error; the inactive field is None."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, extra="forbid")

    value: T | None = None
    error: Error | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> "Result[T]":
        if (self.value is None) == (self.error is None):
            raise ValueError("Provide either a value or an error")
        return self

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        return cls(value=value)

    @classmethod
    def failure(cls, operation: str, exception: Exception) -> "Result[T]":
        return cls(error=Error.from_exception(operation, exception))

    @property
    def is_success(self) -> bool:
        return self.error is None

    def on(
        self,
        on_success: Callable[[T], R],
        on_failure: Callable[[Error], R],
    ) -> R:
        if self.error is not None:
            return on_failure(self.error)
        return on_success(cast(T, self.value))
