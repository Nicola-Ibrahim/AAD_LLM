"""Lifecycle states of a synthesis experiment."""

from enum import StrEnum


class ExperimentStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
