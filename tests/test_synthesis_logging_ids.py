"""Synthesis telemetry identifies the executing database record, not a new session ID."""

import re
from io import StringIO

from evolution.application.interfaces.logger import BaseLogger
from evolution.infra.logging import SynthesisLogger


class RecordingLogger(BaseLogger):
    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    def info(self, msg: str) -> None:
        self.messages.append(msg)

    def warning(self, msg: str) -> None:
        self.messages.append(msg)

    def error(self, msg: str) -> None:
        self.messages.append(msg)


def record_lifecycle(logger: BaseLogger) -> None:
    logger.task_start(1, 1, "test-model", 5, 0.2, 8, "guided", 3680)
    logger.resuming(3680, 2, 10)
    logger.cached(3680, 10, 0.01)
    logger.task_complete(3680, "optimizer", 0.01)
    logger.task_complete(3680, "optimizer", None)


def assert_executing_id_only(output: str) -> None:
    plain = re.sub(r"\x1b\[[0-9;]*m", "", output)
    assert plain.count("Exp ID: #3680") == 5
    assert "Session ID" not in plain
    assert "Session #" not in plain


def test_console_logger_uses_one_consistent_experiment_id_label() -> None:
    stream = StringIO()
    logger = SynthesisLogger(stream=stream, logger_name="test.synthesis.executing-id")
    record_lifecycle(logger)
    assert_executing_id_only(stream.getvalue())


def test_base_logger_uses_the_same_experiment_id_label() -> None:
    logger = RecordingLogger()
    record_lifecycle(logger)
    assert_executing_id_only("\n".join(logger.messages))
