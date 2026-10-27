"""Read trusted synthesis checkpoints without retaining obsolete import modules."""

import pickle
from pathlib import Path

from llamea import LLaMEA

from evolution.infra.engines.llamea.runtime import FailureAwareLLaMEA


class SynthesisCheckpointUnpickler(pickle.Unpickler):
    """Translate persisted type locations moved to the shared foundation."""

    MODULE_RELOCATIONS = {
        "evolution.domain.interfaces.problem": "shared.domain.problem",
        "evolution.domain.enums.noise_model": "shared.domain.noise_model",
        "evolution.domain.services.noise_strategy": "shared.domain.noise",
        "evolution.infra.problems.bbob": "shared.infra.problems.bbob",
        "evolution.infra.problems.factory": "shared.infra.problems.factory",
        "evolution.infra.execution.candidate_executor": "shared.infra.execution.candidate_executor",
    }

    TYPE_RELOCATIONS = {
        ("evolution.infra.storage.code.repository", "CodeRepository"): (
            "evolution.infra.storage.code.repository",
            "FileCodeRepository",
        ),
        ("evolution.application.synthesis.models", "SessionConfig"): (
            "evolution.application.synthesis.settings",
            "SynthesisSettings",
        ),
        ("evolution.application.synthesis.models", "SessionResult"): (
            "evolution.application.synthesis.result",
            "SynthesisResult",
        ),
        ("evolution.application.synthesis.session_types", "SynthesisSessionSettings"): (
            "evolution.application.synthesis.settings",
            "SynthesisSettings",
        ),
        ("evolution.application.synthesis.session_types", "SynthesisSessionResult"): (
            "evolution.application.synthesis.result",
            "SynthesisResult",
        ),
        ("evolution.application.synthesis.evaluate_candidate", "CandidateEvaluationService"): (
            "evolution.application.synthesis.candidate_evaluation",
            "CandidateEvaluator",
        ),
    }

    def find_class(self, module: str, name: str) -> object:
        if relocated := self.TYPE_RELOCATIONS.get((module, name)):
            return super().find_class(*relocated)
        if module == "llamea.llamea" and name == "LLaMEA":
            return FailureAwareLLaMEA
        return super().find_class(self.MODULE_RELOCATIONS.get(module, module), name)


def load_synthesis_checkpoint(path: Path) -> LLaMEA:
    """Preserve pickle state and rehydration hooks; only load trusted local archives."""
    with path.open("rb") as stream:
        engine = SynthesisCheckpointUnpickler(stream).load()
    if not isinstance(engine, LLaMEA):
        raise TypeError("Synthesis checkpoint does not contain a LLaMEA engine.")
    return engine
