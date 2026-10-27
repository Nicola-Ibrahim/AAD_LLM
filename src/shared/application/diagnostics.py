"""Scoped workflow identity and application failure reporting; no handler configuration."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_fields: ContextVar[dict[str, object]] = ContextVar("diagnostic_fields", default={})
_operation_depth: ContextVar[int] = ContextVar("operation_depth", default=0)


def diagnostic_fields() -> dict[str, object]:
    return dict(_fields.get())


@contextmanager
def diagnostic_context(**fields: object) -> Iterator[None]:
    token = _fields.set(_fields.get() | fields)
    try:
        yield
    finally:
        _fields.reset(token)


@contextmanager
def report_operation(logger: logging.Logger | logging.LoggerAdapter, name: str) -> Iterator[None]:
    """Application boundary: report a failure once, then propagate it unchanged."""
    depth = _operation_depth.get()
    token = _operation_depth.set(depth + 1)
    with diagnostic_context(operation=name):
        try:
            yield
        except (KeyboardInterrupt, SystemExit):
            if depth == 0:
                logger.warning("Operation interrupted: %s", name)
            raise
        except Exception:
            if depth == 0:
                path = diagnostic_fields().get("diagnostic_log")
                suffix = f". Diagnostic log: {path}" if path else ""
                logger.exception("Operation failed: %s%s", name, suffix)
            raise
        finally:
            _operation_depth.reset(token)
