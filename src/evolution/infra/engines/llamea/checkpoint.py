"""Read trusted synthesis checkpoints without retaining obsolete import modules."""

from pathlib import Path
import pickle

from llamea import LLaMEA


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

    def find_class(self, module: str, name: str) -> object:
        return super().find_class(self.MODULE_RELOCATIONS.get(module, module), name)


def load_synthesis_checkpoint(path: Path) -> LLaMEA:
    """Preserve pickle state and rehydration hooks; only load trusted local archives."""
    with path.open("rb") as stream:
        engine = SynthesisCheckpointUnpickler(stream).load()
    if not isinstance(engine, LLaMEA):
        raise TypeError("Synthesis checkpoint does not contain a LLaMEA engine.")
    return engine
