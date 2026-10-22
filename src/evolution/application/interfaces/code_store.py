"""Abstract persistence interface for synthesized source code."""

from abc import ABC, abstractmethod
from pathlib import Path

from evolution.application.synthesis.models import CandidateInstance


class SynthesisCodeStore(ABC):
    """Store and retrieve source code produced during synthesis."""

    @abstractmethod
    def save_code(self, code: str, iteration_num: int, experiment_id: int) -> Path:
        """Persist one generated candidate and return its path."""

    @abstractmethod
    def load_code(self, code_path: str | Path) -> str:
        """Load generated source code from its stored path."""

    @abstractmethod
    def clear_experiment(self, experiment_id: int) -> None:
        """Remove generated code belonging only to the selected experiment."""

    @abstractmethod
    def save_candidate_instance(self, experiment_id: int, context: CandidateInstance) -> None:
        """Save the scientific condition alongside a generated candidate."""

    @abstractmethod
    def load_candidate_instance(self, experiment_id: int, iteration: int) -> CandidateInstance:
        """Read recorded instance provenance; fail if absent or invalid."""
