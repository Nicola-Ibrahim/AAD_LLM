"""Console presentation and plain, redacted diagnostic formatting."""

import copy
import logging
import re
import time

from shared.application.result import ApplicationError
from shared.infra.logging.exceptions import format_diagnostic_exception

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


class DiagnosticFormatter(logging.Formatter):
    converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        record = copy.copy(record)
        if record.exc_info:
            record.exc_text = format_diagnostic_exception(record.exc_info[1])
            record.exc_info = None
        fields = " ".join(
            f"{key}={record.__dict__[key]}"
            for key in (
                "invocation",
                "operation",
                "experiment_id",
                "trial",
                "instance_id",
                "task",
                "model",
                "problem_id",
                "dim",
                "noise_std",
                "mode",
                "strategy",
            )
            if key in record.__dict__
        )
        rendered = super().format(record)
        return ApplicationError.sanitize(_ANSI.sub("", f"{rendered} {fields}"))


class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = ApplicationError.sanitize(record.getMessage())
        if record.exc_info:
            message += " (details in the diagnostic log)"
        return message


class ConsoleFilter(logging.Filter):
    """Keep progress readable and coalesce repeated operational warnings."""

    def __init__(self) -> None:
        super().__init__()
        self.last_warning: dict[tuple[str, str], float] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < logging.WARNING:
            return bool(getattr(record, "progress", False))
        if record.levelno == logging.WARNING:
            key = (record.name, str(getattr(record, "message_template", record.msg)))
            now = time.monotonic()
            previous = self.last_warning.get(key, float("-inf"))
            if now - previous < 60.0:
                return False
            self.last_warning[key] = now
            return True
        return True
