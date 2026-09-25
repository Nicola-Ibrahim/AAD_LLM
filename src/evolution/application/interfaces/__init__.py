"""Application Layer Interface Contracts."""

from evolution.application.interfaces.engine import (
    SessionConfig,
    SessionResult,
    SynthesisEngine,
)
from evolution.application.interfaces.logger import BaseLogger
from evolution.application.interfaces.repository import SynthesisRepository
from evolution.application.interfaces.candidate_executor import CandidateExecutor, CandidateTimeout
from evolution.application.interfaces.configuration import SynthesisConfigReader
from evolution.application.interfaces.campaign_runtime import ProblemFactory, TaskDispatcher

__all__ = [
    "BaseLogger",
    "SynthesisRepository",
    "CandidateExecutor",
    "CandidateTimeout",
    "SynthesisConfigReader",
    "ProblemFactory",
    "TaskDispatcher",
    "SessionConfig",
    "SessionResult",
    "SynthesisEngine",
]
