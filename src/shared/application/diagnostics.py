"""Scoped workflow identity and application failure reporting; no handler configuration."""

import logging
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from shared.application.result import ApplicationError

_fields: ContextVar[dict[str, object]] = ContextVar("diagnostic_fields", default={})
_operation_depth: ContextVar[int] = ContextVar("operation_depth", default=0)
_diagnostics: ContextVar[list[str] | None] = ContextVar("operation_diagnostics", default=None)
_reported: ContextVar[dict[int, BaseException] | None] = ContextVar(
    "reported_failures", default=None
)


def record_diagnostic(message: str, error: Exception | None = None) -> None:
    """Collect nonfatal IO/exclusion diagnostics for the owning application operation.

    Outside an operation, the shared application reporter emits the diagnostic.
    Optional maintenance must remain nonfatal even under warnings-as-errors.
    """
    detail = f"{message} ({ApplicationError.describe(error)})" if error else message
    detail = ApplicationError.sanitize(detail)
    pending = _diagnostics.get()
    if pending is None:
        logging.getLogger("shared.workflow").warning("%s", detail)
    else:
        pending.append(detail)


@contextmanager
def preserve_primary_failure(operation: str) -> Iterator[None]:
    """Run cleanup, retaining an active primary failure and noting secondary errors.

    Use in an except/finally block. With no active failure, cleanup errors propagate.
    """
    primary = sys.exception()
    try:
        yield
    except BaseException as cleanup:
        if primary is None:
            raise
        primary.add_note(
            ApplicationError.sanitize(
                f"{operation} also failed ({ApplicationError.describe(cleanup)})"
            )
        )


def reset_process_diagnostics() -> None:
    """Discard inherited operation state in a newly initialized pool process."""
    _fields.set({})
    _operation_depth.set(0)
    _diagnostics.set(None)
    _reported.set(None)


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
    """Report each failure once within an operation tree, then propagate unchanged."""
    depth = _operation_depth.get()
    token = _operation_depth.set(depth + 1)
    pending_token = _diagnostics.set([]) if depth == 0 else None
    reported_token = _reported.set({}) if depth == 0 else None
    reported = _reported.get()
    assert reported is not None  # The outer operation creates this scoped registry.
    with diagnostic_context(operation=name):
        try:
            yield
        except (KeyboardInterrupt, SystemExit) as error:
            if id(error) not in reported:
                reported[id(error)] = error
                logger.warning("Operation interrupted: %s", name)
            raise
        except Exception as error:
            path = diagnostic_fields().get("diagnostic_log")
            if path is not None:
                error.diagnostic_log = str(path)
            if id(error) not in reported:
                reported[id(error)] = error
                suffix = f". Diagnostic log: {path}" if path else ""
                logger.exception("Operation failed: %s%s", name, suffix)
            raise
        finally:
            if pending_token is not None:
                pending = _diagnostics.get()
                _diagnostics.reset(pending_token)
                for message in pending or ():
                    logger.warning("%s", message)
            if reported_token is not None:
                _reported.reset(reported_token)
            _operation_depth.reset(token)
