"""Per-invocation logging with one writer and process-safe diagnostic transport."""

import copy
import io
import logging
import multiprocessing
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from multiprocessing.queues import Queue
from pathlib import Path
from typing import TextIO
from uuid import uuid4

from shared.application.diagnostics import (
    diagnostic_context,
    diagnostic_fields,
    report_operation,
    reset_process_diagnostics,
)
from shared.config import PROJECT_ROOT
from shared.infra.logging.exceptions import format_diagnostic_exception
from shared.infra.logging.formatters import ConsoleFilter, ConsoleFormatter, DiagnosticFormatter

_runtime: ContextVar["LoggingRuntime | None"] = ContextVar("logging_runtime", default=None)
_ROOTS = ("evolution", "benchmark", "shared")
_original_settings: dict[str, tuple[int, bool]] = {}


def current_runtime() -> "LoggingRuntime | None":
    return _runtime.get()


class ContextFilter(logging.Filter):
    def __init__(self, invocation: str) -> None:
        super().__init__()
        self.invocation = invocation

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in diagnostic_fields().items():
            record.__dict__.setdefault(key, value)
        record.__dict__.setdefault("invocation", self.invocation)
        return record.invocation == self.invocation


class DiagnosticQueueHandler(QueueHandler):
    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        record = copy.copy(record)
        record.message_template = str(record.msg)
        record.msg = record.getMessage()
        record.args = None
        if record.exc_info:
            record.exc_text = format_diagnostic_exception(record.exc_info[1])
            record.exc_info = None
        return record


class LoggingRuntime:
    """Own only this invocation's handlers; leave notebook/server handlers intact."""

    def __init__(self, workflow: str, directory: Path, stream: TextIO) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC")
        self.invocation = f"{stamp}-{uuid4().hex[:8]}"
        self.path = directory / workflow / self.invocation / "diagnostics.log"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.queue = multiprocessing.get_context().Queue()
        self.console = logging.StreamHandler(stream)
        self.console.setLevel(logging.INFO)
        self.console.setFormatter(ConsoleFormatter())
        self.console.addFilter(ConsoleFilter())
        self.file = RotatingFileHandler(
            self.path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        self.file.setLevel(logging.DEBUG)
        self.file.setFormatter(
            DiagnosticFormatter(
                "%(asctime)sZ %(levelname)s %(name)s pid=%(process)d %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        self.handler = DiagnosticQueueHandler(self.queue)
        self.handler.addFilter(ContextFilter(self.invocation))
        self.listener = QueueListener(
            self.queue, self.console, self.file, respect_handler_level=True
        )
        self.closed = False
        for name in _ROOTS:
            logger = logging.getLogger(name)
            _original_settings.setdefault(name, (logger.level, logger.propagate))
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
            logger.addHandler(self.handler)
        self.listener.start()

    @contextmanager
    def operation(self, name: str) -> Iterator[None]:
        if self.closed:
            raise RuntimeError("Logging runtime is closed.")
        token = _runtime.set(self)
        with diagnostic_context(invocation=self.invocation, diagnostic_log=str(self.path)):
            try:
                with report_operation(logging.getLogger("shared.workflow"), name):
                    yield
            finally:
                _runtime.reset(token)

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        for name in _ROOTS:
            logger = logging.getLogger(name)
            logger.removeHandler(self.handler)
            if not any(isinstance(h, DiagnosticQueueHandler) for h in logger.handlers):
                level, propagate = _original_settings.pop(name)
                logger.setLevel(level)
                logger.propagate = propagate
        self.listener.stop()
        self.queue.close()
        self.queue.join_thread()
        self.handler.close()
        self.console.close()
        self.file.close()


def configure_worker_logging(queue: Queue, invocation: str) -> None:
    """Process initializer: workers emit records; only the parent writes files."""
    reset_process_diagnostics()
    _runtime.set(None)
    handler = DiagnosticQueueHandler(queue)
    handler.addFilter(ContextFilter(invocation))
    for name in _ROOTS:
        logger = logging.getLogger(name)
        # The child must not use inherited parent handlers under fork.
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(handler)
    sys.stdout = WorkerOutput(logging.DEBUG)
    sys.stderr = WorkerOutput(logging.WARNING)


class WorkerOutput(io.TextIOBase):
    """Capture library prints only in dedicated pool workers, never notebook threads."""

    def __init__(self, level: int) -> None:
        self.level = level
        self.pending = ""

    def write(self, text: str) -> int:
        self.pending += text
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            if line.strip():
                logging.getLogger("evolution.external").log(self.level, "%s", line)
        return len(text)

    def flush(self) -> None:
        if self.pending.strip():
            logging.getLogger("evolution.external").log(self.level, "%s", self.pending)
        self.pending = ""


def start_logging(workflow: str) -> LoggingRuntime:
    return LoggingRuntime(workflow, PROJECT_ROOT / "logs", sys.stdout)
