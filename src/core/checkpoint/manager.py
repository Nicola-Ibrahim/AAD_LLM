from typing import Any
from infra.storage.manager import ExperimentManager
from infra.storage.checkpoint import CheckpointRepository


class CheckpointManager:
    """
    Manages loading, recovery, database persistence, and cleanup of checkpoints
    created during experiment executions.
    """
    def __init__(self, repo: CheckpointRepository, storage_manager: ExperimentManager):
        self.repo = repo
        self.storage_manager = storage_manager

    def persist_and_cleanup(self, result: Any) -> None:
        """Saves result history and problem profile to database via facade, then deletes checkpoint."""
        # Save to DB via repository facade
        self.storage_manager.save_experiment(
            history=result.run_history,
            problem=result.problem_profile,
            mode=result.mode,
            llm_name=result.llm_name,
            run_id=result.run_id,
        )

        # Delegate checkpoint resolution and cleanup to CheckpointRepository
        state = self.repo.resolve(
            problem_id=result.problem_id,
            dim=result.dim,
            mode=result.mode,
            run_id=result.run_id,
        )
        self.repo.delete(state)

    def recover_orphaned(self) -> int:
        """
        Scans the checkpoint directory for orphaned .ckpt.json files and recovers them.

        Returns
        -------
        int
            The number of successfully recovered experiment runs.
        """
        return self.repo.recover_orphaned(self.storage_manager)
