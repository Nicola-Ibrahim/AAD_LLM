from core.llamea.session import LLaMEASession, SessionResult
from core.llamea.evaluator import Evaluator
from core.llamea.executor import AlgorithmExecutor
from core.dispatcher import dispatch, EvolutionJob, DispatchError
from infra.storage.checkpoint import CheckpointRepository


def recover_orphaned_checkpoints(checkpoint_dir, db_repo):
    """Wrapper to recover orphaned checkpoints."""
    repo = CheckpointRepository(checkpoint_dir)
    return repo.recover_orphaned(db_repo)


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
