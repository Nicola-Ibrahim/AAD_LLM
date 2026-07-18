from core.llamea.session import LLaMEASession, SessionResult
from core.llamea.evaluator import Evaluator
from core.llamea.executor import AlgorithmExecutor
from core.dispatcher import dispatch, EvolutionJob, DispatchError


def recover_orphaned_checkpoints(checkpoint_dir, storage_manager):
    """Wrapper to recover orphaned checkpoints."""
    from core.checkpoint.manager import CheckpointManager
    from infra.storage.checkpoint import CheckpointRepository
    repo = CheckpointRepository(checkpoint_dir)
    return CheckpointManager(repo, storage_manager).recover_orphaned()


__all__ = [
    "Evaluator",
    "AlgorithmExecutor",
    "LLaMEASession",
    "SessionResult",
    "dispatch",
    "EvolutionJob",
    "DispatchError",
    "recover_orphaned_checkpoints",
]
