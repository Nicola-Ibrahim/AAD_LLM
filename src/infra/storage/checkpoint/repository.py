import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from core.schema import ProblemProfile, IterationMetadata, ExperimentSummary


@dataclass
class CheckpointState:
    """Transient state descriptor for a LLaMEA session's filesystem checkpoints."""
    archive_dir: Path
    json_path: Path
    pickle_exists: bool
    json_exists: bool


class CheckpointRepository:
    """Manages file-based checkpoints for transient LLaMEA execution state."""

    def __init__(self, checkpoint_dir: Path | str):
        self.checkpoint_dir = Path(checkpoint_dir)

    def resolve(self, *, problem_id: int, dim: int, mode: str, run_id: int) -> CheckpointState:
        """Computes checkpoint paths, ensures archive directories exist, and checks existence."""
        experiment_name = f"bbob_{problem_id}_dim{dim}_{mode}"
        archive_dir = self.checkpoint_dir / experiment_name
        json_path = self.checkpoint_dir / f"run{run_id}_p{problem_id}_d{dim}_{mode}.ckpt.json"

        # Ensure directory structure exists for the archive
        archive_dir.mkdir(parents=True, exist_ok=True)

        pickle_exists = (archive_dir / "llamea_config.pkl").exists()
        json_exists = json_path.exists()

        return CheckpointState(
            archive_dir=archive_dir,
            json_path=json_path,
            pickle_exists=pickle_exists,
            json_exists=json_exists,
        )

    def delete(self, state: CheckpointState) -> None:
        """Atomically clean up all checkpoint files and directories on disk."""
        if state.json_path.exists():
            state.json_path.unlink()
        if state.archive_dir.exists() and state.archive_dir.is_dir():
            shutil.rmtree(state.archive_dir)

    def recover_orphaned(self, db_repo: Any) -> int:
        """Scans the checkpoint directory for orphaned .ckpt.json files and recovers them."""

        recovered_count = 0
        if not self.checkpoint_dir.exists():
            return 0

        for ckpt_path in sorted(self.checkpoint_dir.glob("*.ckpt.json")):
            try:
                with ckpt_path.open("r") as f:
                    envelope = json.load(f)

                experiment_meta = envelope.get("experiment")
                iterations_data = envelope.get("iterations")

                if not experiment_meta or not iterations_data:
                    # Malformed checkpoint, discard
                    ckpt_path.unlink()
                    continue

                problem_meta = ProblemProfile(
                    problem_id=experiment_meta["problem_id"],
                    dim=experiment_meta["dim"],
                    noise_std=experiment_meta["noise_std"],
                    instance_id=experiment_meta.get("instance_id", 1),
                    true_optimum=experiment_meta.get("true_optimum"),
                )

                iterations = [IterationMetadata(**it) for it in iterations_data]

                # Calculate best iteration metrics
                best_iteration = None
                best_error = float("inf")
                best_algo = None
                for it in iterations:
                    if it.fitness.final_error is not None and it.fitness.final_error < best_error:
                        best_error = it.fitness.final_error
                        best_iteration = it.iteration
                        best_algo = it.algorithm_name

                best_err_val = best_error if best_error != float("inf") else None

                summary = ExperimentSummary(
                    mode=experiment_meta["mode"],
                    llm_name=experiment_meta["llm_name"],
                    run_id=experiment_meta["run_id"],
                    problem=problem_meta,
                    best_iteration=best_iteration,
                    best_algorithm=best_algo,
                    best_final_error=best_err_val,
                    iterations=iterations,
                )

                db_repo.save(summary)

                ckpt_path.unlink()
                recovered_count += 1
                print(
                    f"[recovery] Recovered crashed run {experiment_meta.get('run_id')} for "
                    f"BBOB-{experiment_meta.get('problem_id')} ({experiment_meta.get('mode')})"
                )
            except Exception as e:
                print(f"[recovery] Failed to recover {ckpt_path.name}: {e}")

        return recovered_count
